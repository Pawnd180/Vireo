# Vireo 1.0.0 — a free desktop DAW for Windows

Vireo is a local-first digital audio workstation. Arrange on a timeline, edit MIDI,
shape sound with a mixer and 12 effect types, and render to WAV or MP3. No account,
no cloud upload, no subscription: projects are plain JSON files on your own disk.

## Download

| File | Size | What it is |
| --- | --- | --- |
| `Vireo-Setup.exe` | 35 MB | The app plus its installer |
| `Vireo-Instruments.zip` | 1.25 GB | 52 soundfonts, 79 instruments |
| `SHA256SUMS.txt` | 1 KB | SHA-256 checksums for both files |

## Install

1. Download `Vireo-Setup.exe` and `Vireo-Instruments.zip` into the same folder.
2. Run `Vireo-Setup.exe`.
3. Keep the default folder (`%LOCALAPPDATA%\Programs\Vireo`) and click **Install Vireo**.

The setup copies the app, unpacks the instruments beside it, and adds a Start Menu
shortcut (desktop shortcut and first launch are optional). If the ZIP is not beside
the setup it downloads it from this release, and if that fails it asks you to pick
the file instead.

Projects, exports and recordings live beside `Vireo.exe`; set `VIREO_HOME` to store
them elsewhere. Run the setup again to uninstall.

**First launch:** the setup is not code-signed, so Windows SmartScreen may warn that
it protected your PC. Click **More info → Run anyway**.

## What is in the box

- **79 instruments** out of the box: 52 bundled soundfonts, 27 one-click General MIDI
  sounds (concert grand, organs, nylon/steel/jazz/clean/distortion guitars, electric
  bass, harp, timpani, sax, clarinet, recorder, ocarina, kalimba, bagpipe and a GM
  percussion kit) and 12 built-in synth presets.
- **Timeline editing** with clips, fades, quantise, transpose, velocity and humanise.
- **Mixing** with per-track gain, pan, mute and solo, sends, a master bus and 12 effect
  types: reverb, delay, chorus, drive, filter, compressor, bitcrush, tremolo, flanger,
  phaser, EQ and auto-pan.
- **Export** to WAV or MP3, with optional normalisation.
- **Agentic control**: 160+ MCP tools, so an assistant can compose, mix and export
  alongside you.
- **Your files, your disk**: songs are readable JSON, with no account and no telemetry.

## Requirements

Windows 10 or 11, 64-bit. About 1.7 GB of disk space once the instruments are unpacked.

## Support Vireo

Vireo is free and stays free. There is no trial timer, no watermark, and no feature
locked behind a payment. If Vireo earns a place in your workflow, you can support
development on Patreon:

**https://www.patreon.com/17113902/join**

Support pays for the soundfont library, the Windows machines this gets built and
tested on, and the hours that go into every update. Membership is optional and you
can cancel at any time; the app keeps working either way.

## Checksums

Verify your downloads against `SHA256SUMS.txt`. On Windows:

```
certutil -hashfile Vireo-Setup.exe SHA256
certutil -hashfile Vireo-Instruments.zip SHA256
```

If a line does not match the file you downloaded, download it again before running it.
