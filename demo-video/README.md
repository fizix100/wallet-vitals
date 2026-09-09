# Wallet Vitals demo video

Watch: https://onebattle.win/wallet-vitals/demo

MP4: https://onebattle.win/wallet-vitals/demo.mp4

Duration: approximately **3 minutes 9 seconds**. H.264, 1920×1080, AAC audio, English subtitles.
The video is an **edited walkthrough using genuine public-deployment screenshots**, with
macOS Samantha synthetic narration. It is not an uninterrupted screen recording and contains
no simulated risk reports. No voice impersonation, music or stock media is used.

The September 9, 2026 captures show:

- The live homepage and a real public Aave V3 address, without claiming ownership of that address.
- Report `VLtqVHNf9XixK4DS7fVu8WkY`, block 25939275, compared with block 25939270.
- HF 1.1407; contract HF 1.140653315606182338; successful same-block account verification.
- Actual OpenAI summary and explicitly deterministic liquidation-boundary explanation.
- An actual rejected negative `scaledATokenBalance` from another public address.

Reports expire after 24 hours. The video preserves the historical capture, not a guarantee
that the same address or financial values will be reproducible later.

## Rebuild on macOS

Requires `uv`, `ffmpeg`/`ffprobe`, and the built-in Samantha voice:

```sh
uv run --with pillow python demo-video/render.py
uv run python scripts/prepare_cloudflare.py
cd cloudflare
uv run pywrangler deploy
```

`scenes.json` contains the narration and scene order; `captures/` contains original UI captures.
`subtitles.srt` and `subtitles.vtt` are sentence-timed English captions; MP4 includes a subtitle
track, and the web player uses WebVTT. Generated MP4/intermediate audio frames are ignored by Git.
The source captures and rendering script are committed for reproducibility.
