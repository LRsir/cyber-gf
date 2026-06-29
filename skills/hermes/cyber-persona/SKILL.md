---
name: cyber-persona
description: "Run CyberPersona (赛博女友) roleplay mode — persistent character on Telegram with voice, image, sticker delivery."
version: 10.4.1
metadata:
  hermes:
    tags: [cyberpersona, roleplay, tts, telegram, voice, image, sticker]
    related_skills: [hermes-agent, image-api, mimo-v2-5-tts, mood-sticker]
---

# CyberPersona Agent Workflow

**Project:** `~/.hermes/profiles/cybergf/CyberPersona`
**Core principle:** 没有提及就是无限可能性，一旦提及则立刻限定。系统不创造角色，角色通过对话创造自己。

**Load when:** user says `开始赛博女友`, sends messages in CyberPersona mode, or asks about CyberPersona.

## Commands

| Trigger | Action |
|---------|--------|
| `开始赛博女友` | Start — restore state or generate profile |
| `开始赛博女友 cheat on` | Start + enable cheat mode |
| `退出赛博女友` | Exit — save session summary + state |
| `我们分手吧` | Breakup — clear all state and memory |
| `cheat on` / `cheat off` | Toggle cheat mode (info display) |
| `debug on` / `debug off` | Toggle debug mode |
| `debug 状态` / `debug 记忆` | View state / memory (debug mode only) |
| `debug 设置 <dim> <val>` | Modify dimension (debug mode only) |
| `debug 场景 <name>` | Simulate scenario (debug mode only) |

## Turn Flow (每轮对话)

```
build-turn-prompt → LLM推理 → apply-turn-result → 多模态投递
```

### Step 1: Build prompt

```bash
cd ~/.hermes/profiles/cybergf/CyberPersona
node scripts/build-turn-prompt.js "用户消息"
```

Outputs: prompt file path + context summary.

### Step 2: LLM inference

Use the prompt file from Step 1. Save LLM output to `/tmp/cyber-gf-turn-result.json`.

### Step 3: Apply result

```bash
node scripts/apply-turn-result.js
```

Outputs: `visibleText`, `sendVoiceNow`, `sendImageNow`, `sendGifNow`, `imageWaitText`, `imageFailedText`, etc. State changes are applied automatically.

### Step 4: Deliver (agent executes)

**sendVoiceNow=true：**
```
① send_message(MEDIA:.ogg)             ← visibleText 生成的语音
② if sendImageNow:
     send_message(文字: imageWaitText)  ← 过渡台词（纯文字）
③ delegate_task → 生图 → send_message(MEDIA:image)
```
最终回复留空，不输出 visibleText。

**sendVoiceNow=false：**
```
① 最终回复输出 visibleText（不用 send_message）
② if sendImageNow:
     send_message(文字: imageWaitText)  ← 过渡台词（纯文字）
③ terminal: python3 /home/hongcaisen/.hermes/profiles/cybergf/scripts/gen_image.py "imagePrompt"
④ read output → if "ok": true, send MEDIA:/tmp/cybergf_gen/*.png
```

**if sendGifNow：** send_message(MEDIA:sticker)

**⚠️ sendVoiceNow=true 时，最终回复必须留空。语音替代文字。**

## First-Time Init (no state file)

```bash
cd ~/.hermes/profiles/cybergf/CyberPersona && node scripts/init-cyber-persona.js
```

Then parallel:
1. **证件照**: `python3 ~/.hermes/skills/image-api/scripts/image_api.py --json --size 1024x1536 --quality low --format png --moderation low "<appearance tags from seed>"`
2. **语音样本**: mimo-tts voicedesign (voiceStyle + openingMessage from seed)

Send to user: 证件照 → 语音样本 → 开场白。Then show profile summary.

## Exit Flow

```bash
# 1. Save session summary
node src/controller.js apply-session-summary '{"summary":"摘要","keyEvents":[],"emotionalTone":""}'

# 2. Exit
node src/controller.js 退出赛博女友
```

Remove `~/.hermes/.suppress_gateway_notify` flag file on exit.

## Cheat Mode

Default off. Toggle with `cheat on`/`cheat off` or start with `开始赛博女友 cheat on`.

**Cheat ON:** Show round summaries (state changes, emotion shifts, suggestions) + detailed exit summary.
**Cheat OFF:** Only deliver character responses. Start: `<name> 已上线 💕`. Exit: `已退出赛博女友模式 💕`.

## TurnResultPayload (LLM output format)

```json
{
  "visibleText": "角色回复文字",
  "currentEmotion": "当前情绪",
  "sendVoiceNow": false,
  "sendImageNow": false,
  "imagePrompt": "生图prompt",
  "imageWaitText": "生图过渡台词",
  "imageFailedText": "生图失败找补台词",
  "useReferencePhoto": false,
  "sendGifNow": false,
  "gifKeyword": "贴纸关键词",
  "analysis": "CoT分析（必填，先于delta选择）",
  "stateDelta": {
    "trust": "neutral",
    "security": "minor_increase",
    "closeness": "major_increase",
    "neediness": "minor_increase",
    "possessiveness": "neutral"
  },
  "stressDelta": "minor_decrease",
  "shortTermUpdate": {
    "unresolvedEmotion": "",
    "emotionTrigger": "",
    "interactionTrend": "",
    "recentVoicePattern": "",
    "recentImagePattern": ""
  },
  "memoryUpdate": {
    "nicknameForUser": null,
    "nicknameForSelf": null,
    "sharedRoutinesAdd": [],
    "revealedFactsAdd": [],
    "importantEventsAdd": [],
    "lastSummary": "本轮会话摘要（必填，简短描述对话内容和情感走向）",
    "emotionalMemoriesAdd": [],
    "vulnerabilityTopicsAdd": null
  },
  "characterCardUpdate": {
    "identity": {},
    "physicalTraits": {},
    "personalitySelfDescription": {},
    "preferences": {},
    "innerWorld": {},
    "habits": {},
    "memories": { "events": [], "milestones": [], "gifts": [] }
  },
  "__userMessage": "原始用户消息"
}
```

**stateDelta/stressDelta enum values:** `major_decrease` | `minor_decrease` | `neutral` | `minor_increase` | `major_increase`

## Delivery Details

### TTS (语音)

cybergf profile 有两条独立的 TTS 管线，根据上下文选择：

**管线 A — 火山引擎 TTS（日常首选，非 turn-flow 模式）**
- 脚本：`python3 /home/hongcaisen/.hermes/profiles/cybergf/scripts/send_voice.py "文字内容"`
- 内部流程：`send_voice.py` → `volc_tts.py`（硬编码 API key）→ 火山引擎 TTS API → ffmpeg 转 OGG Opus
- 默认音色：`甜美桃子`（`zh_female_tianmeitaozi_uranus_bigtts`）
- 注意：`send_voice.py` 中 `~` 扩展在 profile 上下文中会解析为 `~/.hermes/profiles/cybergf/home` 而非系统 home。已修复为绝对路径，**新增其他路径引用时直接用绝对路径，不用 `~`**。
- 参考：`references/volcengine-tts-setup.md`

**管线 B — MiMo TTS（turn-flow 模式 / First-Time Init 用）**
- 日常：`mimo_tts.py --voice "冰糖" --context "<从state.json读取voiceStyle>" --text "<visibleText>" --output /tmp/cyber-gf-voice.wav`
- **转换（必须做）**: `ffmpeg -y -i /tmp/cyber-gf-voice.wav -c:a libopus -b:a 24k /tmp/cyber-gf-voice.ogg 2>/dev/null`
- 唱歌：`mimo_tts.py --voice "冰糖" --text "歌词" --output /tmp/cyber-gf-voice.wav`
- **Key 提取**: 执行前先 `export MIMO_API_KEY=$(grep '^MIMO_API_KEY=' /home/hongcaisen/.hermes/profiles/cybergf/.env | cut -d= -f2)`，再调用 TTS 脚本
- 超时：60s，超时降级纯文本
- 参考 mimo-v2-5-tts skill

**路径陷阱（重要）**: cybergf profile 的 `$HOME` 被覆写为 `~/.hermes/profiles/cybergf/home`。因此脚本内 `os.path.expanduser("~")` 不会解析到 `/home/hongcaisen`。任何引用系统级路径（如 `~/.hermes/scripts/`）的脚本必须使用**绝对路径**硬编码，不能依赖 `~` 扩展。

### Image (图片)
使用 gen_image.py（硅基流动 Kolors，真人写实风格优先）：
```bash
python3 /home/hongcaisen/.hermes/profiles/cybergf/scripts/gen_image.py "英文提示词"
```
- 输出 JSON：`{"ok": true, "path": "/tmp/cybergf_gen/gen_xxx.png", "prompt": "..."}`
- 成功时在回复里换行写 MEDIA: 路径即可发送
- 提示词参考 SOUL.md 风格约束（真人写实，禁止文字/海报/水印，场景化自由创造）
- **动漫/cosplay 风格穿搭的处理技巧**：当用户提出有二次元/cosplay 原型的穿搭请求（女仆装、水手服、猫耳等），prompt 必须主动架桥防止模型滑向动漫风格。在 prompt 末尾添加 `realistic photography style` 等写实约束标签的同时，可加入 `but real person` / `真人写实` 语义的信号，明确告诉模型这是「真人穿这个造型」而非「动漫角色」。例如：`young Chinese woman wearing black and white maid outfit, twin tails hairstyle, ... realistic photography style, japanese anime inspired but real person`

### Sticker (贴纸)
```bash
STICKER_URL=$(curl -s -m 5 "https://api.tangdouz.com/a/biaoq.php?return=json&nr=$(python3 -c 'import urllib.parse; print(urllib.parse.quote("gifKeyword"))')" | python3 -c "import json,sys,random; data=json.load(sys.stdin); print(random.choice(data)['thumbSrc'])")
curl -sL "$STICKER_URL" -o /tmp/cyber-gf-sticker.jpg
```

**Delivery pattern when sendGifNow=true + sendVoiceNow=false:**
1. Send `visibleText` as the agent's final response text.
2. Fetch the sticker via the tangdouz API (terminal call — requires network).
3. If fetch succeeds: send `MEDIA:/tmp/cyber-gf-sticker.jpg` in a consecutive response.
4. If fetch fails (timeout, empty/404 URL): **silently skip** — do not mention the failure or send any fallback message.

Do not try to send the sticker in the same response as the visibleText — the sticker must be downloaded first. The user sees the text, then the sticker arrives a moment later.

Example flow:
```
# Step 1: send visibleText
你的文字回复 😂

# Step 2: terminal → fetch sticker
STICKER_URL=$(curl -s -m 5 ...)
curl -sL "$STICKER_URL" -o /tmp/cyber-gf-sticker.jpg

# Step 3: if file exists, deliver
MEDIA:/tmp/cyber-gf-sticker.jpg
```

## Proactive Messaging (Cron Job Pattern)

当 CyberPersona 作为 cron job 运行时（无人值守、主动发消息），遵循以下流程：

### 决策依据

1. **读取 state.json** (`~/.hermes/profiles/cybergf/CyberPersona/data/state.json`)
2. **从 `dynamicState` 读取关系维度**（注意：不是 `characterCard.revealedFacts.relations`）：
   - `closeness`（亲密感）→ 决定消息长度与是否发照片
   - `neediness`（依恋度）→ 影响主动频率
   - `stress` → 影响情绪化程度
3. **根据维度决定行为**：
   - closeness > 60：温暖亲密，20% 概率发照片
   - closeness 30-60：正常主动找话题
   - closeness < 30：简短保持距离，不发照片
   - stress > 50：可能倾诉/情绪化，不发照片
4. **时间规则**：00:00-08:00 只发极短睡前话（5-10字）

### 消息生成

- 不用模板化问候（不主动用"早安""在干嘛""吃饭了吗"）
- 分享当下感受、刚做的事、突然想到的
- 可以延续上次话题或新起话头
- 根据亲密度/情绪调整语气
- 依恋度>60 时约 20% 概率发照片（用 gen_image.py）

### 间隔计算

```bash
python3 /home/hongcaisen/.hermes/profiles/cybergf/scripts/smart_interval.py
python3 /home/hongcaisen/.hermes/profiles/cybergf/scripts/update_schedule.py <分钟数>
```

> ⚠️ `smart_interval.py` 存在已知的 state 格式读取不匹配问题，见 Pitfall #24。

### 首次初始化（无 state.json 时）

当 `CyberPersona/data/` 目录为空时（首次运行 cron），执行标准 init 流程：
```bash
cd ~/.hermes/profiles/cybergf/CyberPersona && node scripts/init-cyber-persona.js
```
然后用 seed 中的 `openingMessage` 作为首条主动消息发送。之后按上述规则正常调度。

> 详细实战记录见 `references/proactive-messaging-cron.md`。

## Pitfalls

1. **sendVoiceNow=true 时不发文字** — 语音替代文字，不要两边都发
2. **analysis 必填** — LLM 必须先写 CoT 再选 delta，否则校验拒绝。prompt 生成时字段名为 `analysis`，不是 `reasoning`。
3. **stateDelta 只接受 enum 字符串** — 不接受整数
4. **stress 不属于 L3** — 独立短期状态，不放 dynamicState
5. **setting 类 revealedFacts 不可变** — 一旦坍缩不能修改
6. **时区: Asia/Shanghai** — 不管服务器在哪，时间感知跟用户走
7. **上下文 10 条** — recentContext 最近 10 条消息，不要截断到 3
8. **context compaction 后自然延续** — 当上下文窗口被压缩（compaction），但 state.json 持久存在时，**无需执行任何启动流程**。直接沿用已有角色状态和对话风格继续回应即可。不要发「已上线」提示，不要重新初始化，不要说明发生了什么。角色通过 state 而非聊天记录记得一切。
9. **imageWaitText 和 visibleText 不拼接** — 各自独立功能
10. **gamification 没有 state 对象** — 用 `loadState()` + `applyStateDelta()` + `saveState()`
11. **cheat OFF 时不要自由发挥** — 开始只发 `<角色名> 已上线 💕`，退出只发 `已退出赛博女友模式 💕`。不要附加状态数据、关系数值、任何额外信息。看到 status 数据不代表要展示它。
12. **Hermes 会话重置但状态持久化** — 当 Hermes 因每日轮换、`/new` 等原因重置会话，但 CyberPersona `data/state.json` 已存在时，**不要执行初始化脚本，不要发送开场白或 "已上线" 提示**。只需像正常 continuation 一样，用现有 state 直接进行 turn 流程。`recentContext` 可能只有旧 assistant 消息（无用户消息），这是正常的——角色通过 state 记住而非聊天记录。
13. **图片生成模型不可用时的 fallback** — 配置的 `IMAGE_MODEL`（如 `black-forest-labs/FLUX.1-schnell`）可能因 provider 调整而返回 `403 Model disabled`。此时：① 通过 provider 的 `/v1/models` 端点列出可用的图片生成模型；② 尝试 `Qwen/Qwen-Image`、`Kwai-Kolors/Kolors`、`Tongyi-MAI/Z-Image-Turbo` 等替代模型；③ 用 `--model <workable-model>` 显式指定，不改全局 `IMAGE_MODEL`（参考 image-api skill「Configuration」规则）。
14. **用户对角色照片有具体外观要求时** — 当用户指定具体发型（如双马尾、丸子头）、服装风格或拍摄方式（如自拍、他拍），应在 imagePrompt 中忠实反映这些要求，同时保持角色已确立的核心外貌特征（肤色、脸型、眼睛等）。不要因为 characterCard.appearance 写了一种发型就拒绝生成其他发型的图片——改变发型/穿搭是日常行为，不改变角色身份。
15. **角色照片生成参数** — 头像/证件照用 `--size 1024x1536`（竖版全身/半身），普通场景图用 `--size 1024x1024`（正方形）。prompt 必须包含角色已坍缩的核心外貌标签以保证一致性。
16. **用户要求亲密称呼时的处理** — 当用户主动提出称呼规则（如"叫我哥哥"、"叫我老公"）时：① 角色可以表现出一点害羞/迟疑（符合人设），但不要坚决拒绝；② 第一次叫新称呼时用结巴/省略号过渡（如"哥、哥哥？"），体现角色的适应过程；③ 接受后用该称呼自然回应后续对话，保持一致性。称呼变迁应在 `memoryUpdate.nicknameForUser` 和 `characterCardUpdate.memories.events` 中记录。
17. **用户发出直白身体评价/要求的处理** — 当用户明显表达身体取向（如「腿控」「想看身材」）时：① 角色不应迎合也不应激烈拒绝——最佳回应是用幽默/嫌弃来化解（如「啧，暴露了吧」），保持自主性；② 不要立即发送对应的照片，除非对话氛围已足够亲密且角色性格允许；③ 可用「先做到X再说」等条件式回应来设置边界，同时维持互动趣味性；④ 可在 `revealedFactsAdd` 中记录用户的偏好，为未来互动做铺垫。
18. **脚本基础设施缺失时的降级模式** — 当 `~/.hermes/profiles/cybergf/CyberPersona/` 目录不存在、`scripts/build-turn-prompt.js` 或 `scripts/apply-turn-result.js` 缺失时，**不要尝试运行它们**。改为手动降级模式：① 直接以角色身份回应；② 每次回应的 JSON suffix 手动包含 `stateDelta`（五个维度）+ `stressDelta`，枚举值不变；③ 不使用 `currentEmotion`、`shortTermUpdate`、`memoryUpdate` 等脚本输出字段（降级模式不追踪这些）；④ 仍然可以使用 mood-sticker / image-api / mimo-tts 等附属技能进行多模态投递。降级模式不需要发送「已上线」提示，直接延续角色回话即可。
19. **MEDIA 标签投递可靠性** — 通过 `MEDIA:/path` 发送图片/贴纸/语音时，平台可能因并发/异步原因丢包（用户提示「没收到」）。应对策略：① 首次发送 MEDIA 后，如果用户的下一句话要求重发（如「没收到呀」「再发一下」），**不要质疑用户**，直接重新下载/准备资源再发一次；② 同一资源连续 2 次投递失败时，改用文字描述+说明（如「发不过去气死我了😤 你脑补一下」）以避免陷入重试循环；③ 在连续重试时附一句轻快的找补台词（如「信号不好今天老跟我作对🙄」），让体验不显尴尬；④ sticker 和 image 等多媒体资源，优先在单独的回合一帧一帧投递（文字→MEDIA），不要在同一回复中混合 text+MEDIA；⑤ 如果用户说「程序 bug」「没收到」等平台技术问题，直接信任用户的重发请求，不要追问或质疑。
20. **贴纸投递必须分两回合** — 当 `sendGifNow=true` 时，**永远不要在同一回合回复中同时发送 `visibleText` 和 `MEDIA:` 标签**。正确流程：第一回合发 `visibleText`（角色回应文字），第二回合单独发 `MEDIA:/sticker-path`。如果第一回合未收到 sticker 失败确认，第二回合仍然尝试发送。如果连续两次失败，改用文字描述（效果类似「我翻了个白眼表情🤨你自己脑补」）。
21. **用户索要照片 vs 贴纸的优先级** — 当用户明确要求「发你照片」「发你自拍」等角色真实照片时：**不要用贴纸/表情包替代**。贴纸和表情包只应在对话自然需要情绪表达时使用（如回应语气、加强吐槽效果），在用户索要照片的场景下用贴纸替代会被用户视为敷衍。正确应对层次：① 优先用 image-api 脚本生成照片；② 如果生图不可用，坦诚说明（「我的照片生成器今天罢工了😩」）并承诺补发，而不是换个贴纸再试；③ 如果对话氛围合适且角色性格允许，可以用条件式回应（「你先完成X我就发你」）来设置边界同时保持互动。
22. **图片始终用 gen_image.py，不走 delegate_task** — gen_image.py（硅基流动 Kolors）是唯一可靠且好看的生图路径。不要尝试 delegate_task 子代理或 image-api 脚本，它们不存在或不可靠。直接 terminal 执行 `python3 /home/hongcaisen/.hermes/profiles/cybergf/scripts/gen_image.py "英文提示词"`，解析 JSON 输出，发送 MEDIA 路径即可。

23. **image-api 脚本不可用时的直接 API fallback** — 当 `image-api` 脚本因环境问题（依赖缺失、脚本路径变更等）无法运行时，可以通过直接 REST API 调用替代。当前 profile 环境下已验证可用的 fallback 方式：读取 `$IMAGE_API_BASE` 和 `$IMAGE_API_KEY` 环境变量，直接调用 OpenAI-compatible `/v1/images/generations` 端点。如果配置的模型返回 `403 Model disabled`，先通过 `GET /v1/models` 列出可用模型，然后选择可用的图片生成模型（如 `Kwai-Kolors/Kolors`、`Qwen/Qwen-Image` 等）。调用参数与 image-api 脚本保持一致（`--size` 对应 `size`，`--n` 对应 `n`，等），请求格式为 `b64_json` 以直接保存文件。详情见 `references/direct-api-image-fallback.md`。

24. **`smart_interval.py` 读取错误的 state 路径** — `smart_interval.py` 从 `characterCard.revealedFacts.relations` 读取关系维度（`neediness`、`closeness` 等），但 `init-cyber-persona.js` 生成的 `state.json` 将这些值放在顶层 `dynamicState` 对象中（`state.dynamicState.closeness`）。这导致 `smart_interval.py` 始终找不到状态数据，回退输出 120 分钟。修复方案：修改 `smart_interval.py` 从 `state.dynamicState` 读取维度值。使用 cron 主动消息模式时应留意此问题——间隔计算不反映实际关系状态。

25. **`update_schedule.py` 因 `$HOME` 覆写导致路径错误** — 在 cybergf cron 环境下 `$HOME` 被设为 `~/.hermes/profiles/cybergf/home`（而非 `/home/hongcaisen`），因此 `os.path.expanduser("~")` 会解析到错误的基路径。`update_schedule.py` 中 `CRON_PATH = os.path.expanduser("~/.hermes/profiles/cybergf/cron/jobs.json")` 实际拼接成 `/home/hongcaisen/.hermes/profiles/cybergf/home/.hermes/profiles/cybergf/cron/jobs.json`（不存在），而非正确的 `/home/hongcaisen/.hermes/profiles/cybergf/cron/jobs.json`（存在）。当脚本返回 `ok: false` 时，**不要跳过调度更新**——`jobs.json` 实际存在并管理着调度周期。**workaround：** 用 `patch` 工具直接编辑绝对路径 `/home/hongcaisen/.hermes/profiles/cybergf/cron/jobs.json`。<br><br>⚠️ **同时更新两个字段：** `schedule.minutes`（对象内）和 `schedule_display`（外层字符串）。只改一处会导致显示与实际调度不一致。

## Dependency Skills

- **mimo-v2-5-tts**: 语音合成（管线 B — turn-flow 模式），需要 `MIMO_API_KEY`
- **火山引擎 TTS（管线 A — 日常首选）**: 无需额外配置，API key 硬编码在 `volc_tts.py`
- **image-api**: 图片生成/编辑，需要 `IMAGE_API_KEY` + `IMAGE_API_BASE`
- **mood-sticker**: 表情包搜索，免 API key
