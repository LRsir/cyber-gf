---
name: mood-sticker
description: "表情包搜索 — tangdouz API，免费无需 API key"
---

# Mood Sticker

使用 tangdouz API 搜索表情包，免费无 API key。

## 用法

```bash
# 搜索表情包
STICKER_URL=$(curl -s -m 5 "https://api.tangdouz.com/a/biaoq.php?return=json&nr=$(python3 -c 'import urllib.parse; print(urllib.parse.quote("关键词"))')" | python3 -c "import json,sys,random; data=json.load(sys.stdin); print(random.choice(data)['thumbSrc'])")

# 下载到本地
curl -sL "$STICKER_URL" -o /tmp/cyber-gf-sticker.jpg
```
