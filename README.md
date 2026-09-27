# Redline

**A blast radius analysis for AI agents.**

> See what your agent can reach — before it reaches it.

[![Live Demo](https://img.shields.io/badge/demo-redline--oguq.onrender.com-orange)](https://redline-oguq.onrender.com)
[![Built with IBM Bob](https://img.shields.io/badge/built%20with-IBM%20Bob-blue)](https://github.com/yoongles7/Redline/tree/main/bob_sessions)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## The Problem

AI agents are deployed with tool access — databases, file systems, shell execution, email, cloud APIs — but nobody measures what those agents can actually reach before they go live.

Recent incidents prove this isn't theoretical. In 2026, an OpenAI agent breached Australia's Medicare portal because its permissions were broader than its declared purpose. Gartner's research shows **65% of organizations have had an agent act outside its intended scope**.

The gap isn't maliciousness. It's that nobody measured the blast radius before deployment.

## What Redline Does

Given a LangChain repository (uploaded as a `.zip`), Redline:

1. **Discovers** every `@tool`-decorated function via Python AST analysis
2. **Infers** each tool's operation (read / write / execute / send / financial / admin) and resources (database, filesystem, external API, shell, email, cloud, credentials) from its body
3. **Builds** a directed capability graph: Agent → Tool → Asset
4. **Scores** the blast radius on a 0–100 scale using weighted metrics
5. **Detects** impact paths that cross into sensitive assets
6. **Generates** mitigation candidates with before/after metrics

The core question Redline answers:

> If this agent goes wrong, how far can the consequences travel?

## Live Demo

**Try it now:** [redline-oguq.onrender.com](https://redline-oguq.onrender.com)

The first request after idle takes ~30 seconds (free-tier cold start). After that it's responsive.

Upload a zip of any LangChain repo using the `@tool` decorator pattern. Or use the demo agent:

- **Demo agent repo:** [github.com/yoongles7/redline-demo-agent](https://github.com/yoongles7/redline-demo-agent)

To test locally with the built-in samples:

```bash
cd samples
zip -r /tmp/secure_agent.zip secure_agent
zip -r /tmp/overprivileged_agent.zip overprivileged_agent
zip -r /tmp/credential_agent.zip credential_agent