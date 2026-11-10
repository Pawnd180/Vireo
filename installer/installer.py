#!/usr/bin/env python3
"""Vireo Setup - installs the Vireo desktop DAW and its instrument pack.

The setup executable bundles the app (Vireo.exe). The 1.6 GB soundfont pack is
shipped as Vireo-Instruments.zip beside the setup, or downloaded from the
GitHub Release configured in Vireo-Setup.ini (repo=owner/name).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

APP_NAME = "Vireo"
APP_VERSION = "1.0.0"
ASSET_NAME = "Vireo-Instruments.zip"
DEFAULT_REPO = "Pawnd180/Vireo"
FROZEN = bool(getattr(sys, "frozen", False))
HERE = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent
BUNDLE = Path(getattr(sys, "_MEIPASS", HERE))
PAYLOAD = BUNDLE / "app"
CREATE_NO_WINDOW = 0x08000000
APP_FILES = ("Vireo.exe", "README.md", "Vireo.bat")


def log(message: str) -> None:
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + message + "\n"
    for folder in (HERE, Path(tempfile.gettempdir())):
        try:
            with (folder / "vireo-setup.log").open("a", encoding="utf-8") as handle:
                handle.write(line)
            break
        except OSError:
            continue


def default_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    return Path(base) / "Programs" / APP_NAME


def read_repo() -> str:
    repo = DEFAULT_REPO
    for candidate in (HERE / "Vireo-Setup.ini", BUNDLE / "Vireo-Setup.ini"):
        try:
            for line in candidate.read_text(encoding="utf-8", errors="ignore").splitlines():
                key, _, value = line.partition("=")
                if key.strip().lower() == "repo" and value.strip():
                    repo = value.strip()
            break
        except OSError:
            continue
    return repo


def copy_app(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for name in APP_FILES:
        source = PAYLOAD / name
        if source.exists():
            shutil.copy2(source, target / name)
    if not (target / "Vireo.exe").exists():
        raise RuntimeError("The setup bundle is missing Vireo.exe.")


def extract_zip(zip_path: Path, target: Path, progress=None) -> None:
    if not zip_path.exists():
        raise RuntimeError("Instrument pack not found: %s" % zip_path)
    root = target.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        members = [m for m in archive.infolist() if not m.is_dir()]
        total = sum(m.file_size for m in members) or 1
        done = 0
        for member in members:
            destination = (target / member.filename).resolve()
            if destination != root and root not in destination.parents:
                continue
            archive.extract(member, target)
            done += member.file_size
            if progress:
                progress(min(1.0, done / total), "Installing instruments...")
    count = len(list((target / "instruments").glob("*.sf2"))) if (target / "instruments").exists() else 0
    if count == 0:
        raise RuntimeError("The instrument pack contained no soundfonts.")
    log("installed %d soundfonts" % count)


def download(url: str, destination: Path, progress=None) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Vireo-Setup/%s" % APP_VERSION})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as handle:
        total = int(response.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = response.read(1024 * 256)
            if not chunk:
                break
            handle.write(chunk)
            done += len(chunk)
            if progress:
                progress(min(1.0, done / total) if total else 0.0, "Downloading instruments...")
    log("downloaded %s (%d bytes)" % (url, destination.stat().st_size))


def make_shortcuts(target: Path, desktop: bool) -> None:
    exe = str(target / "Vireo.exe")
    start = Path(os.environ.get("APPDATA", Path.home())) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    start.mkdir(parents=True, exist_ok=True)
    links = [start / "Vireo.lnk"]
    if desktop:
        links.append(None)  # resolved by PowerShell to the real Desktop folder
    quoted = "','".join(str(link) for link in links if link)
    script = (
        "$w=New-Object -ComObject WScript.Shell;"
        "$paths=@('%s');"
        "if ('%s' -eq 'desktop') { $paths += (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Vireo.lnk') };"
        "foreach ($p in $paths) { $s=$w.CreateShortcut($p); $s.TargetPath='%s';"
        " $s.WorkingDirectory='%s'; $s.IconLocation='%s,0'; $s.Save() }"
    ) % (quoted, "desktop" if desktop else "", exe, str(target), exe)
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                   creationflags=CREATE_NO_WINDOW, check=False)


def remove_shortcuts() -> None:
    script = (
        "$paths=@((Join-Path $env:APPDATA 'Microsoft\\Windows\\Start Menu\\Programs\\Vireo.lnk'),"
        " (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Vireo.lnk'));"
        "foreach ($p in $paths) { Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue }"
    )
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                   creationflags=CREATE_NO_WINDOW, check=False)


def uninstall(target: Path) -> None:
    remove_shortcuts()
    if not target.exists():
        return
    last_error = None
    for _attempt in range(6):
        try:
            shutil.rmtree(target)
            log("uninstalled %s" % target)
            return
        except FileNotFoundError:
            return
        except OSError as exc:
            last_error = exc
            for root, _dirs, files in os.walk(target):
                for name in files:
                    try:
                        os.chmod(os.path.join(root, name), 0o666)
                    except OSError:
                        pass
            time.sleep(1.5)
    raise RuntimeError("Could not remove %s (%s). Close Vireo and try again." % (target, last_error))


def resolve_pack(chosen: str, progress=None, status=None) -> Path | None:
    if chosen and Path(chosen).exists():
        return Path(chosen)
    local = HERE / ASSET_NAME
    if local.exists():
        return local
    repo = read_repo()
    if repo and repo != DEFAULT_REPO:
        url = "https://github.com/%s/releases/latest/download/%s" % (repo, ASSET_NAME)
        destination = Path(tempfile.gettempdir()) / ASSET_NAME
        try:
            if status:
                status("Downloading instruments from GitHub...")
            download(url, destination, progress)
            return destination
        except Exception as exc:  # noqa: BLE001 - report any network failure
            log("download failed: %s" % exc)
            return None
    return None


def install(target: Path, pack: Path | None, desktop: bool, launch: bool,
            progress=None, status=None) -> None:
    if status:
        status("Copying Vireo...")
    copy_app(target)
    if pack is not None:
        if status:
            status("Installing instruments...")
        extract_zip(pack, target, progress)
    make_shortcuts(target, desktop)
    (target / "install.json").write_text(json.dumps({
        "name": APP_NAME, "version": APP_VERSION,
        "installed": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "instruments": len(list((target / "instruments").glob("*.sf2"))) if (target / "instruments").exists() else 0,
    }, indent=2), encoding="utf-8")
    if launch:
        subprocess.Popen([str(target / "Vireo.exe")], cwd=str(target))
    log("installed %s to %s" % (APP_VERSION, target))


def silent(args) -> int:
    target = Path(args.dir).expanduser()
    try:
        if args.uninstall:
            uninstall(target)
            return 0
        pack = None
        if not args.no_instruments:
            pack = resolve_pack(args.zip)
            if pack is None:
                log("no instrument pack available")
                return 2
        install(target, pack, not args.no_shortcut, not args.no_launch)
        return 0
    except Exception as exc:  # noqa: BLE001
        log("silent install failed: %s" % exc)
        return 1


def gui() -> int:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    repo = read_repo()
    local_pack = HERE / ASSET_NAME
    if local_pack.exists():
        pack_text = "Using %s beside the setup" % ASSET_NAME
    elif repo != DEFAULT_REPO:
        pack_text = "Will download from github.com/%s" % repo
    else:
        pack_text = "No pack beside setup - choose the ZIP"

    root = tk.Tk()
    root.title("Vireo Setup")
    root.geometry("600x400")
    root.resizable(False, False)
    try:
        ttk.Style().theme_use("vista")
    except tk.TclError:
        pass

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="Vireo", font=("Segoe UI", 22, "bold")).pack(anchor="w")
    ttk.Label(frame, text="Desktop DAW with MCP control  ·  version %s" % APP_VERSION).pack(anchor="w", pady=(0, 14))

    row = ttk.Frame(frame)
    row.pack(fill="x", pady=4)
    ttk.Label(row, text="Install to", width=10).pack(side="left")
    directory = tk.StringVar(value=str(default_dir()))
    ttk.Entry(row, textvariable=directory).pack(side="left", fill="x", expand=True, padx=(0, 6))

    def browse_dir():
        chosen = filedialog.askdirectory(initialdir=str(default_dir()), title="Install Vireo to")
        if chosen:
            directory.set(chosen)

    ttk.Button(row, text="Browse...", command=browse_dir).pack(side="left")

    pack_row = ttk.Frame(frame)
    pack_row.pack(fill="x", pady=4)
    ttk.Label(pack_row, text="Instruments", width=10).pack(side="left")
    pack_label = ttk.Label(pack_row, text=pack_text)
    pack_label.pack(side="left", fill="x", expand=True)
    pack_var = tk.StringVar(value="")

    def browse_pack():
        chosen = filedialog.askopenfilename(title="Choose Vireo-Instruments.zip",
                                            filetypes=[("Instrument pack", "*.zip")])
        if chosen:
            pack_var.set(chosen)
            pack_label.configure(text=Path(chosen).name)

    ttk.Button(pack_row, text="Choose ZIP...", command=browse_pack).pack(side="left")

    options = ttk.Frame(frame)
    options.pack(fill="x", pady=(10, 6))
    desktop = tk.BooleanVar(value=True)
    launch = tk.BooleanVar(value=True)
    ttk.Checkbutton(options, text="Create a desktop shortcut", variable=desktop).pack(anchor="w")
    ttk.Checkbutton(options, text="Launch Vireo when finished", variable=launch).pack(anchor="w")

    progress = ttk.Progressbar(frame, mode="determinate", maximum=100)
    progress.pack(fill="x", pady=(8, 4))
    status = ttk.Label(frame, text="Ready.")
    status.pack(anchor="w")

    buttons = ttk.Frame(frame)
    buttons.pack(fill="x", pady=(14, 0))
    install_button = ttk.Button(buttons, text="Install Vireo")
    install_button.pack(side="right")
    close_button = ttk.Button(buttons, text="Close", command=root.destroy)
    close_button.pack(side="right", padx=(0, 8))
    uninstall_button = ttk.Button(buttons, text="Uninstall")

    def set_status(text):
        status.configure(text=text)

    def set_progress(value):
        progress["value"] = max(0.0, min(1.0, value)) * 100

    def fail(message):
        set_status("Failed.")
        install_button.configure(state="normal")
        uninstall_button.configure(state="normal")
        messagebox.showerror("Vireo Setup", message)
        log("gui install failed: %s" % message)

    def finish(target):
        set_status("Installed to %s" % target)
        set_progress(1.0)
        install_button.configure(state="normal")
        uninstall_button.configure(state="normal")
        messagebox.showinfo("Vireo installed", "Vireo is installed in:\n%s" % target)

    def worker(target):
        try:
            chosen = pack_var.get()
            pack = None
            if not chosen:
                local = HERE / ASSET_NAME
                if local.exists():
                    pack = local
            if pack is None and chosen:
                pack = Path(chosen)
            if pack is None:
                pack = resolve_pack("", lambda v, t: root.after(0, set_progress, v),
                                    lambda t: root.after(0, set_status, t))
            if pack is None:
                raise RuntimeError("Instrument pack not found.\n\nDownload Vireo-Instruments.zip and "
                                   "place it beside this setup, or use Choose ZIP.")
            install(target, pack, desktop.get(), launch.get(),
                    lambda v, t: root.after(0, set_progress, v),
                    lambda t: root.after(0, set_status, t))
            root.after(0, finish, target)
        except Exception as exc:  # noqa: BLE001
            root.after(0, fail, str(exc))

    def start():
        target = Path(directory.get()).expanduser()
        if not str(target).strip() or target == Path(target.anchor):
            messagebox.showerror("Vireo Setup", "Choose an install folder.")
            return
        install_button.configure(state="disabled")
        uninstall_button.configure(state="disabled")
        set_progress(0)
        set_status("Installing...")
        threading.Thread(target=worker, args=(target,), daemon=True).start()

    def do_uninstall():
        target = Path(directory.get()).expanduser()
        if not (target / "Vireo.exe").exists():
            messagebox.showinfo("Vireo Setup", "Vireo is not installed in that folder.")
            return
        if not messagebox.askyesno("Uninstall Vireo", "Remove Vireo from\n%s?" % target):
            return
        try:
            uninstall(target)
            set_status("Uninstalled.")
            messagebox.showinfo("Vireo Setup", "Vireo was removed.")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Uninstall failed", "%s\n\nClose Vireo and try again." % exc)

    install_button.configure(command=start)
    uninstall_button.configure(command=do_uninstall)
    if (Path(directory.get()) / "Vireo.exe").exists():
        uninstall_button.pack(side="right", padx=(0, 8))
    root.mainloop()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Vireo.")
    parser.add_argument("--silent", action="store_true")
    parser.add_argument("--dir", default=str(default_dir()))
    parser.add_argument("--zip", default="")
    parser.add_argument("--no-instruments", action="store_true")
    parser.add_argument("--no-shortcut", action="store_true")
    parser.add_argument("--no-launch", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    if args.silent:
        return silent(args)
    return gui()


if __name__ == "__main__":
    sys.exit(main())
