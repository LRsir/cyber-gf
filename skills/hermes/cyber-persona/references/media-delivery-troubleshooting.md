# MEDIA Delivery Troubleshooting

## Observed Failure Pattern (2026-06-29 session)

**Setup:** CyberPersona mode on Telegram, sticker sent via `MEDIA:/tmp/cyber-gf-sticker.jpg` in same response as visibleText.

**Symptoms:**
1. First MEDIA delivery → user: "你发呀" (didn't see it)
2. Second attempt (re-downloaded, same-turn MEDIA) → user: "没收到呀 再发一下" (still didn't see it)
3. Third attempt (re-downloaded different sticker, same-turn MEDIA) → user: "你再发图试试 刚刚程序 bug 了宝宝" (confirmed platform bug)

**Root cause (conjecture):** MEDIA tag embedded in a response that also contains visibleText may be dropped by Telegram's async delivery pipeline when the platform is under load or during concurrent message processing.

## Lessons

1. **Never inline MEDIA with text in the same response turn.** Always split into two consecutive turns: (a) visibleText only, (b) MEDIA only.
2. **User will blame the agent, not the platform.** When they say "没收到", never argue or question — just re-download and re-send.
3. **Set a 2-retry limit on the same resource.** After 2 failures, switch to text-only description to avoid infinite retry loops.
4. **The 3rd attempt in this session succeeded** — so persistence (up to 3) is warranted before giving up.

## Recommended Flow

```python
# Turn 1: text only
"你的回复文字 😂"

# Turn 2 (consecutive): media only
sticker = download_sticker(keyword)
if sticker:
    "MEDIA:" + sticker
else:
    "发不过去气死我了😤 你脑补一下"
```

## Retry Sequence

| Attempt | Action | Fallback |
|---------|--------|----------|
| 1 | Send MEDIA in dedicated turn | If fail → re-download + retry |
| 2 | Re-download + re-send | If fail → re-download + retry with different resource |
| 3 | Different resource + re-send | If fail → text description only |
