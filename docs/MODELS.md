# Model Configuration

This agent uses **`deepseek-v4-flash`** as its sole LLM. There are two ways to reach it:

| Path | Endpoint | Model id | Env var |
|---|---|---|---|
| **OpenRouter (recommended)** | `https://openrouter.ai/api/v1` | `deepseek/deepseek-v4-flash` | `OPENROUTER_API_KEY` |
| Direct DeepSeek API | `https://api.deepseek.com/v1` | `deepseek-v4-flash` | `DEEPSEEK_API_KEY` |

OpenRouter wins automatically when both keys are set.

## Pricing (verified live on OpenRouter, April 2026)

| Direction | Price |
|---|---|
| Input | $0.14 / 1M tokens |
| Output | $0.28 / 1M tokens |

Source: <https://openrouter.ai/deepseek/deepseek-v4-flash>

## Why DeepSeek V4-Flash

- Cheapest April-2026 frontier model that still handles tool-use + JSON-mode reliably.
- 1M-token context — plenty for multi-step research workloads.
- 284B total / 13B active MoE; designed for high-throughput inference.

## Environment Variables

```bash
# Recommended: one key for every frontier model
export OPENROUTER_API_KEY=sk-or-...

# Or, direct DeepSeek
export DEEPSEEK_API_KEY=sk-...
export DEEPSEEK_BASE_URL=https://api.deepseek.com/v1   # optional override

# Model id — namespaced for OpenRouter, bare for direct API
export DEEPSEEK_MODEL=deepseek/deepseek-v4-flash       # OpenRouter
# export DEEPSEEK_MODEL=deepseek-v4-flash              # direct
```

## Settings access

```python
from a2a_mcp_agent.config import get_settings

s = get_settings()
print(s.deepseek_model)        # the configured model id
print(s.effective_base_url)    # auto-picks OpenRouter when its key is set
print(s.is_mock_mode)          # True if no key (or MOCK_MODE=true)
```

## Mock Mode

Set `MOCK_MODE=true` (or run any test) and the DeepSeek client returns deterministic canned responses — no key, no network. All 64 tests run this way.
