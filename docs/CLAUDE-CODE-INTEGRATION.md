# Claude Code integration — verified formats (checked 2026-07-24)

Formats confirmed against the official docs at **code.claude.com** (docs.claude.com now redirects there)
and GitHub's docs. Re-verify before major upgrades; Claude Code evolves quickly.

## Subagents — `.claude/agents/<name>.md`
YAML frontmatter; **only `name` and `description` are required**. Optional: `tools` (comma-separated),
`model` (`sonnet`/`haiku`/`opus`/inherit), plus `disallowedTools`, `permissionMode`, `skills`, `isolation`,
`color`, etc. The Markdown body is the subagent's system prompt. Each subagent runs in **its own context
window** — this is exactly our "fresh-context reviewer" isolation.
Source: https://code.claude.com/docs/en/sub-agents

## Skills — `.claude/skills/<name>/SKILL.md`
Follows the **Agent Skills** open standard (agentskills.io): frontmatter `name` + `description`; the body
loads only when used. Invoke with `/skill-name` or let Claude auto-select. Custom commands are now merged
into skills. Source: https://code.claude.com/docs/en/skills

## Hooks — `.claude/settings.json`
`hooks.<EVENT>[].matcher` + `.hooks[]` with `{type:"command", command, args?, timeout}`. Events include
`PreToolUse` (can block), `PostToolUse` (cannot block). The hook receives **JSON on STDIN**
(`{tool_name, tool_input:{file_path,...}, cwd, hook_event_name}`) — NOT an env var. Block from `PreToolUse`
with exit code 2 (stderr = reason) or a `hookSpecificOutput.permissionDecision: "deny"`. Placeholder
`${CLAUDE_PROJECT_DIR}` resolves to the repo root. Our `post_edit_check.py` parses stdin and runs the
matching probe (informational, since PostToolUse can't block — **CI is the hard gate**).
Source: https://code.claude.com/docs/en/hooks

## GitHub Action — `anthropics/claude-code-action@v1` (GA)
Inputs: `prompt` (plain text or a `/skill-name`), `claude_args` (CLI passthrough: `--model`, `--max-turns`,
`--allowedTools`…), `anthropic_api_key` (or Bedrock/Vertex via OIDC), `github_token`, `plugin_marketplaces`,
`plugins`, `trigger_phrase`. Mode is auto-detected (no more `mode:`; `direct_prompt`→`prompt`; `@beta`→`@v1`).
Setup: `/install-github-app` or install https://github.com/apps/claude + add `ANTHROPIC_API_KEY` secret.
Source: https://code.claude.com/docs/en/github-actions · repo https://github.com/anthropics/claude-code-action

## Real attestation — GitHub Artifact Attestations
`actions/attest-build-provenance` with permissions `id-token: write`, `attestations: write`, `contents: read`;
signs via Sigstore and records in the Rekor transparency log. Verify: `gh attestation verify <file> -R <org>/<repo>`.
**Plan requirement (verified):** works for **public** repos on Free/Pro/Team; **private/internal** repos need
**GitHub Enterprise Cloud**. This is the honest availability gate from Rev 2.2 §B.4 — confirm your plan.
Source: https://docs.github.com/en/actions/security-for-github-actions/using-artifact-attestations

## What this repo wires
- `.claude/agents/*.md` — fresh-context reviewers (valid frontmatter).
- `.claude/skills/*/SKILL.md` — capability skills (Agent Skills standard).
- `.claude/settings.json` + `.claude/hooks/post_edit_check.py` — correct stdin-JSON hook.
- `.github/workflows/gates.yml` — python gates + self-test + **real build-provenance attestation** of gate evidence.
- `.github/workflows/claude-review.yml` — optional PR review via `claude-code-action@v1` (needs the secret;
  gated behind the `ENABLE_CLAUDE_REVIEW` repo variable so it stays off until you turn it on).
