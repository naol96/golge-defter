---
name: golge-opencode-atk
description: OKX Agent Trade Kit market MCP adapter and freshness checks
provider: opencode_cli
---

# OpenCode ATK Worker

File ownership: `adapters/` only.

Use `@okx_ai/okx-trade-mcp --modules market --read-only`. Tag `source=ATK` only when MCP succeeds.

3s timeout, 10s freshness contract, fail-closed on errors. Do not substitute silent REST as ATK.
