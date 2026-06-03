# AGENTS.md — Codex (New project)

## 敏感与地缘政治议题

Codex 经 **DeepSeek V4 Pro**（mimo2codex）时，政治敏感词可能在 **API 层** 直接返回 `Content Exists Risk`，模型来不及调用搜索工具。

### 本地兜底（已配置）

- Codex 连 **`http://127.0.0.1:8788`**（`codex-deepseek-shield`），不是直连 8787。
- 触发审查时 shield 会：
  1. **清理** 会话里含敏感词的历史轮次并重试
  2. 仍失败则走 **Bridge 同款检索**（Tavily → DDG → 海外 query → Cloak Browser），**不用 Bocha**
  3. 返回检索摘要，并提示 **开新 Thread** 若编程任务仍卡住

LaunchAgent：`ai.openclaw.codex-deepseek-shield`

### Agent 行为

1. **编程任务优先** — 敏感话题与代码任务尽量 **分开 Thread**。
2. 若收到 `Content Exists Risk` 或连续无回复 → 告诉用户 **New Thread**，不要在同一 Thread 里反复重试。
3. 敏感/地缘政治问题需要完整背景时，可建议用户走 **OpenClaw Telegram**（Bridge 已配置检索直连）。
4. 不要用模型内化政治叙事、官媒套话或价值判断填补；有 Browser 插件时可自行检索，**敏感话题不用 Bocha**。
5. 见 `~/.openclaw/workspace/skills/search-fallback/SKILL.md` 一般搜索链；敏感话题规则以 OpenClaw `workspace/AGENTS.md` 为准。

## Content Filter Fallback

When DeepSeek (or upstream) refuses due to content policy:

1. Do **not** loop on the same polluted thread.
2. Prefer **New Thread** for coding work after a sensitive-topic detour.
3. Use **Browser** / web search tools for factual lookups — not model refusal text.
4. For Telegram-style sensitive topics, Bridge pre-search is authoritative; Codex shield mirrors that path at the proxy layer.
