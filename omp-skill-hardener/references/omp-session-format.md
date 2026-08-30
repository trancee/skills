# OMP session model

Supported: persisted JSONL v3. Newer schema => fixture-first verification.

## Branch

File=append-only tree. Active branch=ancestry of latest parented record by file order. Keep unparented `title`,`session`; exclude abandoned descendants. `reset_boundary` clears skill attribution, verifier state, plan-exit state, edit/error counters.

## Records

| type | fields | use |
|---|---|---|
| `session` | `version,id,cwd` | identity/project |
| `message:user` | `content,attribution` | human input; non-user attribution=injected |
| `message:assistant` | `content,stopReason` | text/tools/claims/abort |
| `message:toolResult` | `toolCallId,toolName,isError,content` | same-tool errors |
| `custom_message:skill-prompt` | content,skill dir | explicit skill+path |
| `mode_change` | `mode` | plan enter/exit |
| `reset_boundary` | id,parent | context reset |
| `custom:tool_execution_start` | tool,args | redundant telemetry; assistant call canonical |

Human filter: accept attribution absent/`user`; reject other attribution + known injected reminder prefixes.

## Attribution

- explicit skill prompt+dir: strongest
- `read skill://name`: loaded, provider path possibly unknown
- none: `AGENTS.md` lead only, not proof
- multiple active: most recently loaded tentative; retain all for review

## Verifier telemetry

Observed action only:
- `bash`: test/build/lint/compile/check/diagnostic/smoke
- verification `eval`
- `xd://browser` run; debugger launch/continue/evaluate/stack; LSP diagnostics

Unknown domain verifier may false-positive `claimed_done_no_verify`; inspect context.

## Privacy/limits

Sessions may contain secrets/code/PII. Local only. Miner truncates+redacts common forms, not DLP. Events keep private locators; JSON/report/ledger mode `0600`; manual redact before share/commit.

Limits: `--days` uses mtime; partial/copied leaf may be wrong; multi-skill attribution heuristic; regex signatures/verifiers incomplete; extension shapes require fixtures.
