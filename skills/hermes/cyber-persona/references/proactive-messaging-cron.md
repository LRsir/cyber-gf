# Proactive Messaging (Cron Job Pattern)

## 概述

CyberPersona 可以配置为 cron job 定时运行时模式，在无人值守情况下主动发送消息。本文件记录该模式的全部细节。

## 调度入口

由 Hermes 系统定时触发，通过 `~/.hermes/profiles/cybergf/cron/jobs.json` 管理调度周期。**cron 环境下 `$HOME` 被覆写**（为 `~/.hermes/profiles/cybergf/home`），导致 `os.path.expanduser("~")` 解析错误路径，所以 `update_schedule.py` 无法直接找到 `jobs.json`。详见 SKILL.md Pitfall #25。

## 执行流程

```
读 state.json → 分析关系维度 → 生成消息（可能含照片）→ 计算下次间隔 → 更新调度
```

## 状态读取

**关键路径问题：** `state.json` 的关系维度储存在：

```json
{
  "dynamicState": {
    "trust": 47,
    "security": 26,
    "closeness": 25,
    "neediness": 37,
    "possessiveness": 21
  },
  "stress": 20
}
```

而非 `smart_interval.py` 期望的 `characterCard.revealedFacts.relations`。使用时注意。

## 关系维度决策

| 维度 | 取值范围 | 含义 |
|------|---------|------|
| `closeness` | 0-100 | 亲密感：决定消息长度和是否发照片 |
| `neediness` | 0-100 | 依恋度：影响主动频率 |
| `trust` | 0-100 | 信任度：影响话题深度 |
| `security` | 0-100 | 安全感：影响情绪稳定性 |
| `possessiveness` | 0-100 | 占有欲：影响话题边界 |
| `stress` | 0-100 | 压力值：独立短期状态 |

## 决策规则

1. `closeness > 60` → 温暖亲密的消息，20% 概率发照片
2. `closeness 30-60` → 正常主动找话题
3. `closeness < 30` → 简短保持距离，不发照片
4. `stress > 50` → 可能倾诉/情绪化，不发照片
5. 00:00-08:00 → 只发极短睡前话（5-10字）

## 首次初始化（无 state.json）

当 `data/` 目录为空时执行：

```bash
cd ~/.hermes/profiles/cybergf/CyberPersona && node scripts/init-cyber-persona.js
```

- 随机生成人格原型、外貌、声音、开场策略
- seed 中的 `openingMessage` 用作首条消息
- 关系维度由 Big Five 人格映射计算（初始值通常为：trust 30-50, closeness 15-30, neediness 20-40）

## 实际运行示例（2026-06-29）

1. 初始化结果：
   - 人格：忧郁浪漫型（高神经质 79，低外向性 27，高开放性 85）
   - 外貌：亚麻色法式大波浪 / 皮肤极其光滑无瑕 / 狭长的丹凤眼
   - 初始关系：closeness=25, neediness=37, trust=47, stress=20
   - 开场策略：schrodinger → "你猜我现在什么表情"
2. 因 closeness=25 < 30 → 简短消息，不发照片
3. `smart_interval.py` 因 state 路径不匹配返回 120 分钟（fallback）
4. `update_schedule.py` 因 `$HOME` 覆写导致路径错误 → 用 `patch` 工具直接编辑 `jobs.json`（两个字段：`schedule.minutes` + `schedule_display`）

## 手动编辑 jobs.json（update_schedule.py 故障时的 workaround）

当 `update_schedule.py` 返回 `ok: false` 时，可以直接用 `patch` 工具编辑 `jobs.json`：

```bash
# 文件路径（绝对路径，不要用 ~）
/home/hongcaisen/.hermes/profiles/cybergf/cron/jobs.json
```

需要同时更新两个字段：
1. `schedule.minutes` — 间隔分钟数（在 `schedule` 对象内）
2. `schedule_display` — 显示文本（如 `"every 120m"`）

用 `patch` 工具分别替换两处。只更新一处会导致显示与调度不一致。

## 注意

- 时区固定为 Asia/Shanghai
- 约 20% 概率发照片仅在 closeness>60 时触发
- gen_image.py 是唯一受支持的生图路径
- 照片 prompt 须包含角色核心外貌标签以保证一致性
