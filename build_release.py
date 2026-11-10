#!/usr/bin/env python3
"""Build Vireo's GitHub release artifacts.

    py github/build_release.py --repo your-name/vireo

Outputs in github/:
    Vireo-Setup.exe        self-contained installer (app bundled)
    Vireo-Instruments.zip  the 52 soundfonts + manifest + licences
    Vireo-Setup.ini        repo= line used for the instrument download
    SHA256SUMS.txt
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GITHUB = ROOT / "github"
INSTALLER = GITHUB / "installer"
DIST = ROOT / "dist"
ASSET_NAME = "Vireo-Instruments.zip"
APP_FILES = ("Vireo.exe", "README.md", "Vireo.bat")


def run(command, **kwargs):
    print("+ " + " ".join(str(part) for part in command), flush=True)
    subprocess.run(command, check=True, **kwargs)


def stage_payload() -> Path:
    payload = GITHUB / "payload" / "app"
    if payload.parent.exists():
        shutil.rmtree(payload.parent)
    payload.mkdir(parents=True)
    for name in APP_FILES:
        source = DIST / name
        if not source.exists():
            raise SystemExit("missing %s - run py build_app.py first" % source)
        shutil.copy2(source, payload / name)
    print("staged app payload: %.0f MB" % (sum((payload / n).stat().st_size for n in APP_FILES) / 1048576))
    return payload


def write_ini(repo: str, version: str) -> None:
    (GITHUB / "Vireo-Setup.ini").write_text(
        "[vireo]\nrepo=%s\nversion=%s\n" % (repo, version), encoding="utf-8")


def build_installer(payload: Path, version: str) -> Path:
    icon = INSTALLER / "vireo.ico"
    run([sys.executable, str(INSTALLER / "make_icon.py")])
    separator = ";" if os.name == "nt" else ":"
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
               "--onefile", "--windowed", "--name", "Vireo-Setup",
               "--distpath", str(GITHUB), "--workpath", str(ROOT / "build" / "setup"),
               "--specpath", str(ROOT / "build" / "setup"),
               "--icon", str(icon), "--version-file", str(INSTALLER / "version_info.txt"),
               "--add-data", "%s%s%s" % (payload, separator, "app"),
               "--add-data", "%s%s%s" % (GITHUB / "Vireo-Setup.ini", separator, "."),
               str(INSTALLER / "installer.py")]
    run(command, cwd=str(ROOT))
    target = GITHUB / "Vireo-Setup.exe"
    if not target.exists():
        raise SystemExit("PyInstaller did not produce %s" % target)
    print("built %s (%.1f MB)" % (target.name, target.stat().st_size / 1048576))
    return target


def build_instruments() -> Path:
    source = DIST / "instruments"
    if not source.exists():
        raise SystemExit("missing %s - run py build_app.py first" % source)
    target = GITHUB / ASSET_NAME
    if target.exists():
        target.unlink()
    files = sorted([p for p in source.rglob("*") if p.is_file()])
    written = 0
    total = 0
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            relative = path.relative_to(DIST)
            if (len(relative.parts) != 2 or relative.parts[0] != "instruments"):
                continue
            if path.suffix.lower() not in (".sf2", ".json", ".md"):
                continue
            archive.write(path, relative.as_posix())
            written += 1
            total += path.stat().st_size
            if total // (200 * 1048576) != (total - path.stat().st_size) // (200 * 1048576):
                print("  packed %.0f MB..." % (total / 1048576), flush=True)
    print("built %s (%d files, %.0f MB packed)" % (target.name, written, target.stat().st_size / 1048576))
    return target


def checksums(paths):
    lines = []
    for path in paths:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        lines.append("%s  %s" % (digest.hexdigest(), path.name))
    (GITHUB / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build GitHub release artifacts.")
    parser.add_argument("--repo", default="your-name/vireo")
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--skip-app", action="store_true")
    parser.add_argument("--skip-instruments", action="store_true")
    args = parser.parse_args()

    if not args.skip_app:
        run([sys.executable, str(ROOT / "build_app.py")], cwd=str(ROOT))

    write_ini(args.repo, args.version)
    payload = stage_payload()
    setup = build_installer(payload, args.version)
    paths = [setup]
    if not args.skip_instruments:
        paths.append(build_instruments())
    license_file = DIST / "instruments" / "LICENSE.md"
    if license_file.exists():
        shutil.copy2(license_file, GITHUB / "LICENSE-soundfonts.md")
    checksums(paths)
    return 0


if __name__ == "__main__":
    sys.exit(main())
