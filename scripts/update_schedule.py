#!/usr/bin/env python3
"""Update cybergf profile cron job schedule with a new interval."""
import json, sys, os

CRON_PATH = os.path.expanduser("~/.hermes/profiles/cybergf/cron/jobs.json")
JOB_NAME_PREFIX = "赛博女友"

def update(minutes):
    if not os.path.exists(CRON_PATH):
        print(json.dumps({"ok": False, "error": "jobs.json not found"}))
        return False

    with open(CRON_PATH) as f:
        data = json.load(f)

    found = False
    for job in data.get("jobs", []):
        name = job.get("name", "")
        if JOB_NAME_PREFIX in name:
            job["schedule"] = {
                "kind": "interval",
                "minutes": minutes,
                "display": f"every {minutes}m"
            }
            job["schedule_display"] = f"every {minutes}m"
            found = True
            break

    if not found:
        print(json.dumps({"ok": False, "error": "job not found"}))
        return False

    with open(CRON_PATH, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(json.dumps({"ok": True, "next_interval_minutes": minutes}))
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("minutes", type=int, help="Interval in minutes")
    args = parser.parse_args()
    update(args.minutes)
