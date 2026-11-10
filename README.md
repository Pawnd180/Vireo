# Vireo — GitHub release

This folder holds everything needed to publish Vireo on GitHub.

## What is in here

| File | Purpose |
| --- | --- |
| `Vireo-Setup.exe` | Installer: bundles the app, creates shortcuts, installs the instrument pack |
| `Vireo-Instruments.zip` | The 52 bundled soundfonts + manifest + licences (about 1.25 GB) |
| `Vireo-Setup.ini` | `repo=owner/name` used by the installer to download the pack |
| `SHA256SUMS.txt` | Checksums of the release files |
| `installer/` | Installer source and Windows metadata |
| `build_release.py` | Rebuilds the setup, the pack and the checksums |
| `RELEASE_NOTES.md` | Copy for the GitHub release page |
| `LICENSE-soundfonts.md` | Licences of the bundled instruments |

The setup executable is unsigned, so Windows SmartScreen may show
**“Windows protected your PC”**. Choose **More info → Run anyway**.
## Installing

1. Download `Vireo-Setup.exe` and `Vireo-Instruments.zip` into one folder.
2. Run `Vireo-Setup.exe`.
3. Pick a folder (default `%LOCALAPPDATA%\Programs\Vireo`), then **Install Vireo**.

The installer copies the app, extracts `instruments/` beside it, creates a
Start Menu shortcut, and optionally a desktop shortcut and a first launch.
Projects, exports and recordings are written beside `Vireo.exe`; set
`VIREO_HOME` to store them elsewhere. Re-run the setup and use **Uninstall**
to remove the installation.

## Building from source

From the repository root:

```bash
py -m pip install -r requirements.txt pyinstaller
py build_app.py
py github/build_release.py --repo Pawnd180/Vireo
```

`build_app.py` produces `dist/Vireo.exe` plus `dist/instruments`.
`build_release.py` then produces:

- `github/Vireo-Setup.exe` (~30 MB)
- `github/Vireo-Instruments.zip` (~1.25 GB)
- `github/SHA256SUMS.txt`

Use `--skip-app` to reuse an existing `dist/Vireo.exe`, and
`--skip-instruments` for a fast setup-only build.

## Continuous integration

`.github/workflows/build-release.yml` builds both files on a `v*` tag and
attaches them to the GitHub release. It downloads the soundfonts, builds the
app, builds the installer and the pack, and uploads everything. The first run
takes roughly 15–25 minutes because it moves about 3 GB.

## Requirements and licences

- Windows 10/11 x64 with the Edge WebView2 runtime (included with Windows 11).
- The application code has no licence file in this repository yet — add one
  before publishing.
- The bundled soundfonts are CC0 1.0, except the MuldjordKit drums which are
  CC BY 4.0. See `LICENSE-soundfonts.md`.
