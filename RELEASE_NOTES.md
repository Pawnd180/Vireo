# Vireo 1.0.0

First public release of Vireo, a local desktop DAW for Windows: arrange tracks on a
timeline, record and edit MIDI, shape sound with a mixer and 12 effects, and export
to WAV or MP3. Everything runs on your machine.

## Highlights

- **79 instruments out of the box** from 52 bundled soundfonts, plus 27 one-click
  General MIDI sounds and 12 built-in synth presets.
- **Non-destructive editing**: clips, fades, quantise, transpose, velocity, humanise.
- **Mixing**: per-track gain/pan/mute/solo, sends, master bus, 12 effect types.
- **Export**: WAV and MP3 renders with a normalise option.
- **Projects are plain JSON**, so songs are easy to back up and diff.

## Install

1. Download `Vireo-Setup.exe` and `Vireo-Instruments.zip` into the same folder.
2. Run `Vireo-Setup.exe`.
3. Choose a folder (default `%LOCALAPPDATA%\Programs\Vireo`) and click **Install Vireo**.

The setup installs the app, unpacks the 52 soundfonts beside it, and creates a Start
Menu shortcut. If the ZIP is missing it downloads it from this release; if that
fails it asks you to pick the file.

## Notes

- Windows 10/11 x64. The setup is unsigned, so SmartScreen may warn: choose
  **More info → Run anyway**.
- Uninstall by running the setup again and choosing **Uninstall**, or from
  Settings → Apps.
- The soundfonts are CC0 1.0, except the MuldjordKit drums (CC BY 4.0). See
  `LICENSE-soundfonts.md`.

## Checksums

See `SHA256SUMS.txt` on this release.
