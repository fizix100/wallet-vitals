"""Stage the unchanged shared Python core and frontend for pywrangler."""

import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / "cloudflare"
shutil.copytree(
    root / "src/wallet_vitals",
    target / "src/wallet_vitals",
    dirs_exist_ok=True,
    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
)
shutil.copytree(root / "src/wallet_vitals/static", target / "public/static", dirs_exist_ok=True)
shutil.copyfile(root / "src/wallet_vitals/templates/index.html", target / "public/index.html")
media_target = target / "public/wallet-vitals"
media_target.mkdir(exist_ok=True)
for source, filename in [("wallet-vitals-demo.mp4", "demo.mp4"), ("subtitles.vtt", "demo.vtt")]:
    artifact = root / "demo-video" / source
    if artifact.exists():
        shutil.copyfile(artifact, media_target / filename)
print("Cloudflare bundle staged without credentials or local database.")
