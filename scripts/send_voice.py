#!/usr/bin/env python3
"""Send voice message for cybergf profile.
Uses Volcano Engine TTS (same engine as tg-bot2), outputs OGG Opus for Telegram voice bubbles.
Usage: python3 send_voice.py "文字内容"
"""
import sys, os, subprocess, time, json

# Use the existing volc_tts.py which handles 火山引擎TTS + ffmpeg to OGG
VOLC_TTS = "/home/hongcaisen/.hermes/scripts/volc_tts.py"
VOICE = "甜美桃子"  # zh_female_tianmeitaozi_uranus_bigtts

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "Usage: send_voice.py <text>"}))
        sys.exit(1)

    text = sys.argv[1]
    if not text.strip():
        print(json.dumps({"ok": False, "error": "Empty text"}))
        sys.exit(1)

    # Override TEMP to use /tmp with timestamp for unique output
    ts = int(time.time() * 1000)
    tmpdir = f"/tmp/cybergf_voice_{ts}"
    os.makedirs(tmpdir, exist_ok=True)
    env = os.environ.copy()
    env["TEMP"] = tmpdir

    result = subprocess.run(
        ["python3", VOLC_TTS, text, VOICE],
        capture_output=True, text=True, timeout=60, env=env
    )

    output = result.stdout.strip()
    if result.returncode != 0 or not output.startswith("OK:"):
        print(json.dumps({"ok": False, "error": output or result.stderr[:200]}))
        sys.exit(1)

    ogg_path = output[3:].strip()  # Remove "OK: " prefix
    # If relative, resolve to absolute
    if not os.path.isabs(ogg_path):
        ogg_path = os.path.join(tmpdir, os.path.basename(ogg_path))
    if not os.path.exists(ogg_path):
        print(json.dumps({"ok": False, "error": f"Output file not found: {ogg_path}"}))
        sys.exit(1)

    # Copy to a stable path
    final_path = f"/tmp/cybergf_voice.ogg"
    subprocess.run(["cp", ogg_path, final_path], capture_output=True)
    if not os.path.exists(final_path):
        final_path = ogg_path

    print(json.dumps({"ok": True, "path": final_path, "text": text}))

if __name__ == "__main__":
    main()
