#!/usr/bin/env python3
"""A CLI alarm clock: beeps after a delay or at a wall-clock time."""
import argparse
import datetime as dt
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import wave

def write_beep(path: str, seconds: float = 0.6, frequency: int = 880) -> None:
    """Write a mono 16-bit sine-wave WAV file."""
    rate = 44100
    frames = int(rate * seconds)
    with wave.open(path, "w") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(rate)
        data = bytearray()
        for i in range(frames):
            sample = int(32767 * 0.4 * math.sin(2 * math.pi * frequency * i / rate))
            data += struct.pack("<h", sample)
        fh.writeframes(bytes(data))

def play_sound() -> None:
    """Play a beep with the first available system player, else ring the terminal bell."""
    players = [("aplay", ["aplay", "-q"]), ("paplay", ["paplay"]),
               ("afplay", ["afplay"]), ("play", ["play", "-q"])]
    path = None
    try:
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        write_beep(path)
        for name, cmd in players:
            if shutil.which(name):
                subprocess.run(cmd + [path], check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
        sys.stdout.write("\a")
        sys.stdout.flush()
    finally:
        if path and os.path.exists(path):
            os.unlink(path)

def parse_time(text: str) -> dt.datetime:
    """Parse HH:MM (24h) into the next occurrence of that time."""
    try:
        hour, minute = (int(part) for part in text.split(":"))
        target = dt.datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    except (ValueError, TypeError) as exc:
        raise ValueError("time must be HH:MM in 24-hour format") from exc
    if target <= dt.datetime.now():
        target += dt.timedelta(days=1)
    return target

def countdown(seconds: float, quiet: bool = False) -> None:
    end = time.monotonic() + seconds
    while True:
        remaining = end - time.monotonic()
        if remaining <= 0:
            break
        if not quiet:
            mins, secs = divmod(int(remaining) + 1, 60)
            print(f"\rAlarm in {mins:02d}:{secs:02d}", end="", flush=True)
        time.sleep(min(0.2, remaining))
    if not quiet:
        print("\rAlarm!          ")

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, help="ring after this many seconds")
    parser.add_argument("--at", help="ring at HH:MM (next occurrence)")
    parser.add_argument("--demo", action="store_true", help="0.5 second demo")
    args = parser.parse_args()

    if args.demo:
        print("Demo: ringing in 0.5 seconds")
        countdown(0.5, quiet=True)
        play_sound()
        print("Demo: alarm rang after 0.5 seconds")
        return

    if args.at:
        target = parse_time(args.at)
        seconds = (target - dt.datetime.now()).total_seconds()
        print(f"Alarm set for {target:%Y-%m-%d %H:%M}")
    elif args.seconds is not None:
        if args.seconds < 0:
            print("Error: seconds cannot be negative")
            return
        seconds = args.seconds
        print(f"Alarm set for {seconds:g} seconds from now")
    else:
        raw = input("Ring after how many seconds (or 'at HH:MM')? ").strip()
        if raw.lower().startswith("at "):
            target = parse_time(raw[3:].strip())
            seconds = (target - dt.datetime.now()).total_seconds()
        else:
            seconds = float(raw)
    countdown(seconds)
    play_sound()
    print("Alarm!")

if __name__ == "__main__":
    main()
