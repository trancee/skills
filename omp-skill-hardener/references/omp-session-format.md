# OMP session evidence model

The miner supports persisted OMP session JSONL version 3. Treat newer versions as unverified until fixtures cover their changed records.

## Active branch

A session file is an append-only tree, not a flat conversation. Conversation entries carry `id` and `parentId`; forks leave abandoned descendants in the same file. The active persisted branch is the ancestry of the latest parented entry in file order. Unparented `title` and `session` metadata remain available, but abandoned branch events must not count toward recurrence.

`reset_boundary` is part of the branch. It clears active-skill attribution, verification state, plan-exit state, and other context that cannot safely cross a reset.

## Material record shapes

| Record | Fields used | Meaning |
| --- | --- | --- |
| `session` | `version`, `id`, `cwd` | Session identity and project scope |
| `message` / user | `content`, `attribution` | Human request or correction; non-user attribution is injected context |
| `message` / assistant | `content`, `stopReason` | Text, tool calls, completion claims, and aborts |
| `message` / toolResult | `toolCallId`, `toolName`, `isError`, `content` | Tool outcome and same-tool consecutive error evidence |
| `custom_message` / `skill-prompt` | content, skill directory | Explicit skill invocation and exact authored target |
| `mode_change` | `mode` | Entry to or exit from plan mode |
| `reset_boundary` | identity and parent | Context reset on the active branch |
| `custom` / `tool_execution_start` | tool name and args | Redundant lifecycle telemetry; assistant tool calls remain canonical |

The miner accepts older user messages without `attribution`, but rejects messages attributed to a system, extension, skill, replay, or other non-human source. Known injected reminder and interruption prefixes are excluded even if imported data omitted attribution.

## Skill attribution

Explicit skill prompts provide the strongest link because OMP supplies both the skill name and installation directory. A `read` call to `skill://<name>` proves the skill was loaded but may not expose its winning provider path. Absence of an active skill is not proof that `AGENTS.md` caused a failure; it is a low-confidence review lead.

Skills remain active along their branch until a reset. When several skills were loaded, the most recently loaded skill is the tentative target and all active names remain in the event record for manual review.

## Verification telemetry

Verification means an observed action, not words such as “tested” in assistant prose. Supported actions are:

- test, build, lint, compile, check, diagnostic, or smoke commands executed by `bash`;
- verification-oriented code executed by `eval`;
- browser `run`, debugger execution/evaluation, and LSP diagnostics sent through `write` to the corresponding `xd://` device.

This list is intentionally narrow. A domain-specific verifier not represented here can produce a false `claimed_done_no_verify` event; confirm the surrounding records before acting.

## Privacy and integrity

Raw sessions can contain source code, secrets, prompts, credentials, paths, and personal data. Keep them local. The miner truncates whitespace-normalized excerpts and redacts common emails, home-directory user names, token forms, and key/value secrets. This is risk reduction, not a data-loss-prevention guarantee.

Generated JSON retains private source locators for review and is written with mode `0600`. Reports and ledgers use the same mode. Do not commit or share these artifacts without a separate manual redaction pass.

## Known limits

- Session discovery uses file modification time for `--days`; imported old sessions may appear recent.
- A copied or partially written JSONL file may have a latest entry that is not the user's intended leaf.
- Attribution after several simultaneously active skills is heuristic.
- Frustration language, completion language, and verification commands are regex-based and can produce false positives or false negatives.
- Extension-defined record and tool shapes require new fixtures before reliance.
