"""Build a narrated walkthrough from genuine browser captures (macOS say + ffmpeg).

Run: uv run --with pillow python demo-video/render.py
Input: scenes.json and captures/*.png. Output: wallet-vitals-demo.mp4 + subtitles.srt.
This is an edited walkthrough, not a claim of uninterrupted screen recording.
"""

import json
import re
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
RENDER = ROOT / "render"
RENDER.mkdir(exist_ok=True)
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def run(*args):
    subprocess.run([str(arg) for arg in args], check=True, capture_output=True)


def timestamp(seconds):
    millis = round(seconds * 1000)
    return (
        f"{millis // 3600000:02}:{millis // 60000 % 60:02}:"
        f"{millis // 1000 % 60:02},{millis % 1000:03}"
    )


scenes = json.loads((ROOT / "scenes.json").read_text())
clips, captions, offset = [], [], 0.0
for index, scene in enumerate(scenes, 1):
    stem = RENDER / f"scene-{index:02}"
    narration = stem.with_suffix(".txt")
    narration.write_text(scene["narration"])
    audio = stem.with_suffix(".aiff")
    run("say", "-v", "Samantha", "-r", "155", "-f", narration, "-o", audio)
    duration = (
        float(
            subprocess.check_output(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(audio),
                ]
            )
        )
        + 1.1
    )

    # New branded frame; the browser capture is composited without changing any data.
    frame = Image.new("RGB", (1920, 1080), "#123f36")
    draw = ImageDraw.Draw(frame)
    draw.text((52, 28), "WALLET VITALS", font=ImageFont.truetype(BOLD, 29), fill="#edf2e3")
    draw.text(
        (1370, 31),
        "ETHONLINE 2026  /  LIVE WALKTHROUGH",
        font=ImageFont.truetype(FONT, 21),
        fill="#b9d4c9",
    )
    capture = Image.open(ROOT / "captures" / scene["capture"]).convert("RGB")
    capture.thumbnail((1390, 924), Image.Resampling.LANCZOS)
    frame.paste(capture, (36, 94))
    draw.text(
        (1470, 122),
        f"{index:02} / {len(scenes):02}",
        font=ImageFont.truetype(FONT, 24),
        fill="#a8c9b9",
    )
    y = 184
    for line in textwrap.wrap(scene["title"], width=19):
        draw.text((1470, y), line, font=ImageFont.truetype(BOLD, 38), fill="#f6f1e5")
        y += 50
    y += 28
    for line in textwrap.wrap(scene["callout"], width=27):
        draw.text((1470, y), line, font=ImageFont.truetype(FONT, 27), fill="#c8ded0")
        y += 39
    draw.text((1470, 894), "READ-ONLY", font=ImageFont.truetype(BOLD, 25), fill="#d5e4a5")
    draw.text(
        (1470, 937), "No signatures. No trading.", font=ImageFont.truetype(FONT, 24), fill="#c8ded0"
    )
    draw.text(
        (52, 1032),
        "onebattle.win/wallet-vitals/",
        font=ImageFont.truetype(FONT, 22),
        fill="#c8ded0",
    )
    draw.text(
        (960, 1032),
        "Edited real UI captures · English synthetic narration · Not financial advice",
        font=ImageFont.truetype(FONT, 19),
        fill="#aac4b9",
    )
    png = stem.with_suffix(".png")
    frame.save(png)
    clip = stem.with_suffix(".mp4")
    run(
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-loop",
        "1",
        "-framerate",
        "24",
        "-i",
        png,
        "-i",
        audio,
        "-t",
        str(duration),
        "-c:v",
        "libx264",
        "-tune",
        "stillimage",
        "-preset",
        "fast",
        "-crf",
        "24",
        "-pix_fmt",
        "yuv420p",
        "-af",
        "apad",
        "-c:a",
        "aac",
        "-b:a",
        "112k",
        clip,
    )
    clips.append(clip)
    sentences = [part.strip() for part in scene["narration"].split(". ") if part.strip()]
    total_chars = sum(len(part) for part in sentences)
    local_offset = 0.0
    for sentence in sentences:
        span = (duration - 1.1) * len(sentence) / total_chars
        captions.append(
            f"{len(captions) + 1}\n{timestamp(offset + local_offset)} --> "
            f"{timestamp(offset + local_offset + span)}\n"
            + "\n".join(textwrap.wrap(sentence.rstrip(".") + ".", 72))
            + "\n"
        )
        local_offset += span
    offset += duration
    print(f"Rendered {index}/{len(scenes)}: {duration:.1f}s", flush=True)

concat = RENDER / "concat.txt"
concat.write_text("\n".join(f"file '{clip}'" for clip in clips))
subtitles = ROOT / "subtitles.srt"
subtitles.write_text("\n".join(captions))
(ROOT / "subtitles.vtt").write_text(
    "WEBVTT\n\n" + re.sub(r"(\d{2}:\d{2}:\d{2}),(\d{3})", r"\1.\2", "\n".join(captions))
)
output = ROOT / "wallet-vitals-demo.mp4"
run(
    "ffmpeg",
    "-y",
    "-loglevel",
    "error",
    "-f",
    "concat",
    "-safe",
    "0",
    "-i",
    concat,
    "-i",
    subtitles,
    "-map",
    "0:v",
    "-map",
    "0:a",
    "-map",
    "1:s",
    "-c",
    "copy",
    "-c:s",
    "mov_text",
    "-metadata:s:s:0",
    "language=eng",
    "-disposition:s:0",
    "default",
    "-movflags",
    "+faststart",
    output,
)
print(f"Created {output}: {offset:.1f}s, {output.stat().st_size / 1024 / 1024:.1f} MiB")
