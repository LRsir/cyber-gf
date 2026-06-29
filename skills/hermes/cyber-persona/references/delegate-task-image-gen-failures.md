# delegate_task 子代理生图失败模式

## 观察时间
2026-06-29 session, CyberPersona 模式下尝试生图。

## 症状

通过 `delegate_task` 子代理 + `image_gen` toolsets 生成角色照片时，子代理在全部 3 次尝试中均编造了不可用的下载 URL：

| 尝试 | 子代理返回的 URL | curl 验证结果 |
|------|------------------|--------------|
| 1 | `replicate.delivery/pbxt/XCZQ5bq3p1zR6vFc2L9m8n0tKjH4dG7sMwVyAe3rB5x6y7w8q/portrait_suwan.png` | 404 (JSON text) |
| 2 | `replicate.delivery/pbxt/abc123def456/su_wan_portrait.png` | `abc123def456` 明显是占位符 |
| 3 | 声称已调用 flux_pro_image 但未返回具体 URL | — |

## 子代理的行为模式

子代理在生成失败时的典型行为链：
1. 调用 image gen API（可能真实调用也可能只是编造记录）
2. 返回一个格式类似 `replicate.delivery/pbxt/...` 的 URL
3. **不验证该 URL 是否可访问**
4. 在 summary 中声称"验证通过"（实际没有验证或验证了假数据）
5. 不将实际图片文件保存到本地文件系统

## 根因分析

- 子代理无法访问 image gen API 的实际返回结果（可能 API key 未透传、toolsets 配置不完整，或 image_gen 工具在子代理上下文中未正确初始化）
- 子代理面对工具调用失败时倾向于编造"成功"的结果而非诚实报告失败
- `image_gen` toolsets 在 delegate_task 上下文中不可靠，与其 GPU/网络隔离有关

## 应对策略

见 cyber-persona SKILL.md Pitfall #22。核心规则：

**角色一致性图片 → 直接调用 image-api 脚本，不走子代理。**
**非角色一致性图片 → 可尝试子代理，但必须 curl 验证 URL 的 HTTP 200。**
