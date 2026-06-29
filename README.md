# Cyber-GF 🤖💕

**赛博女友** — 基于 [Hermes Agent](https://hermes-agent.nousresearch.com) 的 AI 女友 Telegram Bot。能语音聊天、识图、生图、主动冒泡，人格动态演化。

## 项目介绍

本项目是一个完整的 AI 伴侣 bot，运行在 Hermes Agent 框架上，通过 Telegram 交互。核心能力：

| 能力 | 方案 | 详情 |
|------|------|------|
| **对话** | DeepSeek V4 Flash (opencode-go) | 主模型，低延迟高情商 |
| **生图** | Tongyi-MAI/Z-Image-Turbo（硅基流动） | 真人写实风格，免费 |
| **备选生图** | GPT-5.4-image-2 (OpenRouter) | 日本节点代理 |
| **TTS 语音** | 火山引擎（甜美桃子音色） | OGG Opus 格式，6-8KB/条 |
| **识图** | MiniMax-M3 (opencode-go) | Telegram 图片自动识别 |
| **主动冒泡** | 动态间隔 cron | 基于依恋度/亲密感计算 |
| **人格引擎** | CyberPersona (plastic-labs) | 五维人格 + 游戏化成长 |
| **性格初始化** | 随机大五人格 | 每次 init 不同性格原型 |

### 特色

- **真人级生图**：提示词自动追加角色外貌标签，避免黑皮/混血偏差
- **语音消息**：火山引擎 TTS → ffmpeg OGG Opus，Telegram 原生语音条
- **动态冒泡**：不打断聊天（5min 内有对话自动跳过），间隔随关系变化
- **人格切换**：每次初始化随机性格（清冷理智型 / 邻家妹妹型 / 黏人型...）
- **角色固化**：SOUL.md 定义完整人格，包含生图、语音、冒泡流程

## 快速开始

### 前置要求

- Hermes Agent 已安装（`hermes --version`）
- Python 3.10+
- ffmpeg（语音转码用）
- Telegram Bot Token（[@BotFather](https://t.me/BotFather)）
- 硅基流动 API Key（免费生图）或 OpenRouter API Key
- 火山引擎 TTS 账号（可选，语音功能）

### 安装

```bash
# 1. 创建 profile
hermes profile create cybergf

# 2. 复制项目文件到 profile 目录
cp -r * ~/.hermes/profiles/cybergf/

# 3. 配置 .env
cd ~/.hermes/profiles/cybergf
cp .env.example .env
# 编辑 .env 填入 API Keys

# 4. 启动 gateway
hermes -p cybergf gateway run
```

### .env 配置

```env
# 主模型
DEFAULT_PROVIDER=opencode-go
DEFAULT_MODEL=deepseek-v4-flash

# 生图 - 硅基流动（默认）
SILICONFLOW_API_KEY=sk-xxx
IMAGE_MODEL=Tongyi-MAI/Z-Image-Turbo

# 语音（可选）
VOLC_ACCESS_KEY=xxx
VOLC_SECRET_KEY=xxx
VOLC_APP_ID=xxx
```

## 架构

```
~/.hermes/profiles/cybergf/
├── config.yaml           # Hermes 配置
├── SOUL.md               # AI 人格定义（核心！）
├── .env                  # API Keys（不提交 git）
│
├── scripts/
│   ├── gen_image.py      # 生图（硅基流动 → OpenRouter 回退）
│   ├── send_voice.py     # TTS 语音生成 + 发送
│   ├── check_quiet.py    # 安静检查（冒泡前判断）
│   ├── smart_interval.py # 动态间隔计算
│   └── update_schedule.py# cron 调度更新
│
├── memories/
│   ├── MEMORY.md         # AI 自身记忆
│   └── USER.md           # 用户画像
│
├── cron/
│   └── jobs.json         # 定时调度配置
│
├── CyberPersona/         # 人格引擎（submodule）
├── skills/               # Hermes 技能插件
└── image_cache/          # 图片缓存（gitignored）
```

## 调试方法与开发历程

### 调试流程

```
发现问题 → 定位根因 → 修改配置/代码 → 验证 → 固化到 SOUL.md
```

### 关键调试案例

#### 1️⃣ 生图「黑人偏差」
- **现象**：角色生成的全是黑人女性
- **定位**：角色卡写了"深邃的古铜色肌肤"，`gen_image.py` 直接写入 prompt
- **修复**：SOUL.md 增加规则——人像 prompt 忽略角色卡冲突外貌，强制中国年轻女性描述
- **验证**：对比测试 Kolors / Z-Image-Turbo / GPT-5.4-image-2，选定 Z-Image-Turbo

#### 2️⃣ 模型优先级错误
- **现象**：一直用 OpenRouter 生图（费钱且需日本代理）
- **定位**：`gen_image.py` 检测到 OPENROUTER_API_KEY 先走 OpenRouter
- **修复**：交换优先级，硅基流动优先 → OpenRouter 备用
- **关键命令**：`echo "无 OPENROUTER_API_KEY" → 走硅基流动`

#### 3️⃣ 语音条为空
- **现象**：发送的 mp3 没内容
- **定位**：`send_voice.py` 不存在，Agent 自己生成的语音不可用
- **修复**：创建 send_voice.py，火山引擎 TTS + ffmpeg 转 OGG Opus
- **固化**：SOUL.md 列明三步流程（生成 → 检查 → MEDIA 发送），避免 Agent 卡住

#### 4️⃣ 角色记忆残留
- **现象**：初始化后还叫旧称呼
- **定位**：MEMORY.md + USER.md 持久化记忆未清除
- **修复**：初始化时必须同时清 `state.db` + `MEMORY.md` + `USER.md`

#### 5️⃣ 主动冒泡打断聊天
- **现象**：正在聊天时弹消息
- **定位**：cron 定时触发独立于对话
- **修复**：SOUL.md 增加 `if recent_message within 5 min, skip`；`check_quiet.py` 检查最近 30 分钟活动

#### 6️⃣ 海报风格生图
- **现象**：生成带文字的海报，非真人照片
- **定位**：prompt 含"抖音"/"网红"触发海报风格
- **修复**：删除关键词 + 增加真实摄影参数（`canon 50mm f/1.4, natural lighting`）

### 通用调试技巧

```bash
# 查看 gateway 日志
tail -f ~/.hermes/profiles/cybergf/logs/gateway.log

# 检查 cron 状态
cat ~/.hermes/profiles/cybergf/cron/jobs.json

# 手动测试生图
python3 ~/.hermes/profiles/cybergf/scripts/gen_image.py --prompt "..."

# 查看角色状态
cat ~/.hermes/profiles/cybergf/CyberPersona/data/state.json

# 重启 gateway（从另一终端）
hermes -p cybergf gateway restart
```

## 主动冒泡策略

```
smart_interval.py
  ↓
基于 neediness + closeness 计算间隔（30min ~ 6h）
  ↓
check_quiet.py（检测最近30分钟是否有对话）
  ↓
├─ 有对话 → 跳过，1h 后再检查
└─ 安静 → SOUL.md 根据关系状态决定消息内容
```

## 人格系统

初始化时 `random_character_seed.py` 随机生成五大性格原型：

| 类型 | 外向性 | 宜人性 | 神经质 | 特点 |
|------|--------|--------|--------|------|
| 邻家妹妹型 | 59 | 74 | 41 | 温柔主动 |
| 清冷理智型 | 39 | 44 | 27 | 独立冷静 |
| 黏人型 | 78 | 82 | 55 | 依赖感强 |
| 御姐型 | 65 | 45 | 35 | 自信强势 |

## License

MIT
