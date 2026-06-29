# 火山引擎 TTS 设置 (cybergf profile)

## 概览

cybergf profile 的日常语音使用 **火山引擎 TTS**（豆包大模型语音合成），非 MiMo TTS。

## 管线拓扑

```
send_voice.py → volc_tts.py → 火山引擎 API → MP3 → ffmpeg → OGG Opus
```

## 文件位置

| 文件 | 路径 |
|------|------|
| 入口脚本 | `~/.hermes/profiles/cybergf/scripts/send_voice.py` |
| 核心 TTS | `/home/hongcaisen/.hermes/scripts/volc_tts.py` |
| 语音缓存 | `~/.hermes/profiles/cybergf/audio_cache/` |

## volc_tts.py API 细节

- **API 端点**: `https://openspeech.bytedance.com/api/v3/tts/unidirectional`
- **Resource ID**: `seed-tts-2.0`
- **API Key**: 硬编码在 volc_tts.py 内（`118a2096-4994-45f2-9cdb-6786ef028ded`）
- **输出格式**: MP3（采样率 24000）→ ffmpeg 转 OGG Opus（24kbps）

## 可用音色

| 名称 | Voice ID |
|------|----------|
| 甜美桃子（默认） | `zh_female_tianmeitaozi_uranus_bigtts` |
| 甜美小源 | `zh_female_tianmeixiaoyuan_uranus_bigtts` |
| 清新女声 | `zh_female_qingxinnvsheng_uranus_bigtts` |

## send_voice.py 用法

```bash
python3 /home/hongcaisen/.hermes/profiles/cybergf/scripts/send_voice.py "要合成的文字"
```

成功返回 `{"ok": true, "path": "/tmp/cybergf_voice.ogg", ...}`。
失败返回 `{"ok": false, "error": "..."}`。

## 已知问题

### 路径陷阱
cybergf profile 的 `$HOME` 被覆写为 `~/.hermes/profiles/cybergf/home`。在脚本中使用 `os.path.expanduser("~")` 会解析到这个 profile 目录而非系统 home。

**修复**: `send_voice.py` 中 `VOLC_TTS` 路径已从 `os.path.expanduser("~/.hermes/scripts/volc_tts.py")` 改为硬编码绝对路径 `/home/hongcaisen/.hermes/scripts/volc_tts.py`。后续新增路径引用也应当使用绝对路径。

### 超时
volc_tts.py 内部 requests 超时为 30s，send_voice.py 子进程超时为 60s。超时时降级为纯文本。
