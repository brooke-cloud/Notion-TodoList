"""Read-only isolated EXE liveness smoke; never prints configuration values."""
from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import dotenv_values


def windows_for_pid(pid):
    found = []
    enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    @enum_proc
    def callback(hwnd, _):
        owner = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and ctypes.windll.user32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    ctypes.windll.user32.EnumWindows(callback, 0)
    return found


def main():
    exe = Path(sys.argv[1]).resolve()
    if not exe.is_file():
        raise SystemExit(f"EXE_NOT_FOUND {exe}")
    env = os.environ.copy()
    for key, value in dotenv_values(Path(__file__).resolve().parents[1] / ".env").items():
        if value is not None: env[key] = value
    process = subprocess.Popen([str(exe)], cwd="C:\\", env=env)
    try:
        deadline = time.monotonic() + 60
        saw_window = False
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"EXE_EXITED_EARLY code={process.returncode}")
            saw_window = saw_window or bool(windows_for_pid(process.pid))
            time.sleep(1)
        if not saw_window:
            raise RuntimeError("EXE_WINDOW_NOT_FOUND")
        print("EXE_ALIVE_60S")
        print("EXE_VISIBLE_WINDOW_OK")
        print("EXE_READ_ONLY_SMOKE_OK")
    finally:
        for hwnd in windows_for_pid(process.pid):
            ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
        try: process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.terminate(); process.wait(timeout=5)


if __name__ == "__main__": main()
