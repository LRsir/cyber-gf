#!/usr/bin/env python3
"""Check if there was recent user activity in CyberPersona chat.
Returns exit code 0 (recent activity) or 1 (quiet, ok to message)."""
import json, os, sys, time

STATE_PATH = os.path.expanduser("~/.hermes/profiles/cybergf/CyberPersona/data/state.json")
HISTORY_PATH = os.path.expanduser("~/.hermes/profiles/cybergf/CyberPersona/data/history.json")
QUIET_MINUTES = 30  # Skip if user messaged within this many minutes

now = time.time()

# Check state.json updatedAt
if os.path.exists(STATE_PATH):
    try:
        with open(STATE_PATH) as f:
            state = json.load(f)
        updated = state.get("meta", {}).get("updatedAt", "")
        if updated:
            # Parse ISO format
            import datetime
            try:
                dt = datetime.datetime.fromisoformat(updated.replace("Z", "+00:00"))
                elapsed = now - dt.timestamp()
                if elapsed < QUIET_MINUTES * 60:
                    print(f"RECENT_ACTIVITY: state updated {elapsed/60:.0f}min ago")
                    sys.exit(0)  # 0 = skip
            except:
                pass
    except:
        pass

# Check history.json last entry
if os.path.exists(HISTORY_PATH):
    try:
        with open(HISTORY_PATH) as f:
            history = json.load(f)
        if isinstance(history, list) and history:
            last = history[-1]
            ts = last.get("timestamp", last.get("time", last.get("createdAt", "")))
            if ts:
                import datetime
                try:
                    dt = datetime.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                    elapsed = now - dt.timestamp()
                    if elapsed < QUIET_MINUTES * 60:
                        print(f"RECENT_ACTIVITY: last message {elapsed/60:.0f}min ago")
                        sys.exit(0)  # 0 = skip
                except:
                    pass
    except:
        pass

print("QUIET: no recent activity, ok to message")
sys.exit(1)  # 1 = ok to message
