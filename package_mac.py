#%%
from __future__ import annotations
import os, shutil, subprocess, sys, time
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
DMG_TMP = ROOT / "dmg_temp"
APP_NAME = "Eir.app"
VOL_NAME = "Eir STPA Tool"

def sh(cmd: str, check: bool = True) -> int:
    print(f"Running: {cmd}")
    return subprocess.run(cmd, shell=True, check=check).returncode

def clean_dirs() -> None:
    if DMG_TMP.exists():
        shutil.rmtree(DMG_TMP)
    DMG_TMP.mkdir(parents=True, exist_ok=True)
    DIST.mkdir(parents=True, exist_ok=True)

def unique_dmg_name(version_hint: Optional[str] = None) -> Path:
    # Prefer tag name from CI, else timestamp
    tag = os.getenv("GITHUB_REF_NAME") or version_hint or time.strftime("v%Y%m%d-%H%M%S")
    return DIST / f"Eir-STPA-Tool-{tag}.dmg"

def create_dmg(version_hint: Optional[str] = None) -> Path:
    clean_dirs()

    # Copy the .app produced by PyInstaller to the dmg temp
    app_src = DIST / APP_NAME
    if not app_src.exists():
        raise FileNotFoundError(f"Expected {app_src} (did PyInstaller produce the .app?)")

    app_dst = DMG_TMP / APP_NAME
    shutil.copytree(app_src, app_dst, symlinks=True)

    # Add /Applications alias inside the DMG
    sh(f"ln -s /Applications '{(DMG_TMP / 'Applications').as_posix()}'")

    dmg_path = unique_dmg_name(version_hint)

    # Ensure no leftover DMG with same name
    if dmg_path.exists():
        dmg_path.unlink()

    # Extra safety: list and detach any mounted images with same name (rare in CI)
    # No-op if not mounted.
    subprocess.run("hdiutil info | awk '/Eir STPA Tool/ {print $1}' | xargs -I{{}} hdiutil detach {{}}",
                   shell=True, check=False)

    # Create compressed DMG with retries (handles sporadic 'Resource busy')
    cmd = (
        f'hdiutil create -volname "{VOL_NAME}" '
        f'-srcfolder "{DMG_TMP}" -ov -format UDZO -imagekey zlib-level=9 '
        f'"{dmg_path}"'
    )

    tries, delay = 3, 5
    for i in range(1, tries + 1):
        try:
            sh(cmd, check=True)
            break
        except subprocess.CalledProcessError as e:
            if i == tries:
                raise
            print(f"[warn] hdiutil failed (attempt {i}/{tries}). Sleeping {delay}s then retrying…")
            time.sleep(delay)

    print(f"✅ DMG created at: {dmg_path}")
    return dmg_path

def main() -> None:
    # Allow `python package_mac.py dmg-only` (your current usage)
    args = sys.argv[1:]
    version_hint = None
    if args:
        # Accept optional version like dmg-only:v0.4.6
        if ":" in args[0]:
            _, version_hint = args[0].split(":", 1)
    create_dmg(version_hint)

if __name__ == "__main__":
    main()
