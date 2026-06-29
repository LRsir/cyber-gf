#!/usr/bin/env python3
"""Read CyberPersona state.json and calculate next message interval (minutes)."""
import json, os, math, random

STATE_PATH = os.path.expanduser("~/.hermes/profiles/cybergf/CyberPersona/data/state.json")

def load_state():
    if not os.path.exists(STATE_PATH):
        return None
    with open(STATE_PATH) as f:
        return json.load(f)

def main():
    state = load_state()
    if not state:
        # Fallback: 120 min
        print(json.dumps({"minutes": 120, "reason": "no state"}))
        return

    cc = state.get("characterCard", {})
    facts = cc.get("revealedFacts", {})
    relations = facts.get("relations", {})
    mood = facts.get("mood", {})
    stress = mood.get("stress", 0) if isinstance(mood, dict) else 0
    if not isinstance(relations, dict):
        relations = {}

    neediness = relations.get("neediness", 50)
    closeness = relations.get("closeness", 50)
    possessiveness = relations.get("possessiveness", 50)
    trust = relations.get("trust", 50)

    # Base interval: inversely correlated with neediness + closeness
    # High neediness/closeness = shorter interval
    avg = (neediness + closeness) / 2.0

    if avg >= 80:
        base = 60     # 1h - very attached
    elif avg >= 60:
        base = 90     # 1.5h
    elif avg >= 40:
        base = 120    # 2h
    elif avg >= 20:
        base = 180    # 3h
    else:
        base = 240    # 4h - cold

    # Stress modifier: stressed = need space
    if stress > 60:
        base = int(base * 1.5)
        reason = f"stress high ({stress})"
    elif stress > 40:
        base = int(base * 1.2)
        reason = f"stress moderate ({stress})"
    else:
        reason = f"neediness={neediness}, closeness={closeness}"

    # Random jitter: ±15%
    jitter = random.uniform(0.85, 1.15)
    minutes = max(30, min(360, int(base * jitter)))

    print(json.dumps({"minutes": minutes, "reason": reason}))

if __name__ == "__main__":
    main()
