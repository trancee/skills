# Selection, contexts, and local services

## Select explicitly

| Intent | Command pattern |
| --- | --- |
| List repository jobs | `act --list` |
| List an event/file | `act pull_request -W .github/workflows/ci.yml --list` |
| Plan one job/dependencies | `act pull_request -W .github/workflows/ci.yml -j test --graph` |
| Validate loaded schemas | `act --validate --strict -W .github/workflows/ci.yml` |
| Reviewed container dry-run | `act pull_request -W .github/workflows/ci.yml -j test -n -P ubuntu-latest=catthehacker/ubuntu:act-latest` |
| Execute event payload | `act pull_request -W .github/workflows/ci.yml -e local-event.json -P ubuntu-latest=catthehacker/ubuntu:act-latest` |
| Narrow matrix | append `--matrix os:ubuntu-latest --matrix node:22` for existing values |
| Change project root | `act -C path/to/project ...`; workflow/payload file paths resolve relative to that root |

`-j` uses the YAML job **ID**, not its display name. Dependencies are included, and identical IDs in multiple loaded workflows can match. Supplying `-W` avoids accidental broad scope. Version 0.2.89's `-j` path calls PlanJob rather than event-trigger filtering: passing an event alongside a job supplies context, not proof that GitHub would trigger it. Listing without an event can show jobs that a default run would not execute. Name the event on execution, particularly with workflow_dispatch.

Matrix filters select existing combinations; they cannot add values and cannot override exclusions. A broad matrix or watch run can multiply side effects. Confirm actual executed cells/steps in output.

**Observed in act 0.2.89:** `-n` with `-P label=-self-hosted` still executes shell steps and produces outputs. The flag requests no container creation, not universal no-execution. Use list/graph/schema validation for pre-execution inspection; even those load config/secrets. Do not run untrusted workflows merely to dry-run them.

## Config precedence and contexts

Act reads argument files in this order: XDG `act/actrc`, HOME `.actrc`, invocation-directory `.actrc`, then CLI arguments. Files use one argument per line; keep them comment-free as documented. Scalar CLI overrides differ from repeatable flags, which accumulate; don't assume `-P` or secret/mount lists erase earlier settings. `-C` changes the project root but `.actrc` discovery uses the invocation directory.

Default local data files are `.env`, `.vars`, `.secrets`, and `.input`. Their dotenv syntax supports quoted values; keep credentials in protected ignored files, outside copied/bound workspace where feasible. CLI file overrides use `--env-file`, `--var-file`, `--secret-file`, `--input-file`.

| Workflow context | Non-sensitive example |
| --- | --- |
| `inputs.NAME` / `github.event.inputs.NAME` | `act workflow_dispatch --input NAME=local ...` or payload inputs |
| `vars.CHANNEL` | `--var CHANNEL=local` |
| `env.MODE` | `--env MODE=local` |
| `secrets.LOCAL_PROBE` | `-s LOCAL_PROBE` from inherited env, secure prompt, or protected secret file |

Act does not issue GitHub's per-run GITHUB_TOKEN. Version 0.2.89 tries GitHub CLI token discovery when that secret is absent. Use `-s GITHUB_TOKEN=` for intentionally credential-free execution. For an authorized token-dependent scenario, use least-privilege credentials from secure prompt/env/file; don't paste literals or `$(gh auth token)` into a logged argv. Redaction cannot prevent malicious code from reading an intentionally supplied secret. `--github-instance hostname` configures GitHub Enterprise; validate action-source/auth behavior separately.

## Payload construction

Copy a sanitized real event when complex fields are needed. The bundled `scripts/make-event.py` emits JSON to stdout, diagnostics to stderr, and always adds `act:true` for explicitly local job guards:

```bash
python3 scripts/make-event.py push --ref refs/tags/v1.2.3 > local-event.json
python3 scripts/make-event.py pull_request --head-ref feature --base-ref main > local-event.json
python3 scripts/make-event.py workflow_dispatch --input 'MESSAGE=Grüezi = local' > local-event.json
```

Resolve helper paths from the skill package, not the consumer repo. The PR payload supplies only `pull_request.head.ref` and `.base.ref`; it does not invent number, SHA, action, repository, sender, or changed files. Dispatch values remain strings, including `false`, empty strings, and values containing `=`. Add fields accessed by workflow expressions and choose event/typed inputs appropriate to the scenario. Generating JSON does not reproduce webhook trigger delivery.

For a reviewed local deployment skip, guard the **job** with `if: ${{ !github.event.act }}` and ensure the payload actually sets act=true. For a **step**, `if: ${{ !env.ACT }}` can use act's special environment marker. The env context is not available in job-level conditions. Any skip is an intentional local divergence, not verified deployment behavior.

## Executable fixture

Copy `assets/smoke.yml` to a disposable repository's `.github/workflows/local-smoke.yml`. It contains no external actions or real secret requirement. Run from that repo, after inspecting inherited act config:

```bash
act workflow_dispatch -W .github/workflows/local-smoke.yml --list
act --validate --strict -W .github/workflows/local-smoke.yml
act workflow_dispatch -W .github/workflows/local-smoke.yml \
  --input 'MESSAGE=Grüezi = local' --var CHANNEL=local \
  -s LOCAL_PROBE=public-smoke-sentinel -s GITHUB_TOKEN= \
  --matrix flavor:beta -P ubuntu-latest=catthehacker/ubuntu:act-latest \
  --container-daemon-socket=- --no-cache-server
```

The LOCAL_PROBE value is deliberately public test data, not a credential. Expected: only prepare/beta runs, then verify observes `Grüezi = local/local/beta` from needs.prepare.outputs.result and writes `act-smoke-result.txt` inside its workspace. Observe the printed value; copy/read the file from the selected execution workspace if artifact evidence is needed. A host-only reviewed proof substitutes `-P ubuntu-latest=-self-hosted`; report that backend explicitly.

Select flavor:alpha for an intentional failure: the producer's assertion rejects it, the command must exit nonzero, and verify must not report a successful output. Empty/no matching selections are not passing results.

## Artifacts, cache, and action sources

`--artifact-server-path path` starts act's local artifact service; choose a reachable `--artifact-server-addr`/port for containers/remote engines and inspect the output files. Without that service, artifact runtime URLs are absent. Upload/download artifact v3/v4 can work within a local run; cross-run/workflow/repo download using a GitHub token is not supported parity. Local runtime URLs in run steps can differ from GitHub's runner.

Cache storage/action cache are separate from artifacts and runner images. Inspect `--cache-server-*`, `--no-cache-server`, and `--action-cache-path` in the installed CLI; remote/container network reachability matters. Offline mode still downloads absent assets.

Default checkout handling can substitute local workspace copying. Use `--no-skip-checkout` only when actual checkout behavior is required; it may fetch remote code instead of the uncommitted tree being tested. For local `uses: ./...`, verify copied files/action metadata/build output and working-directory layout before cargo-culting old checkout@v2 path workarounds. `--local-repository repository@ref=folder` supports explicit reviewed action-source substitution; record that local divergence.

Sources: [usage](https://nektosact.com/usage/index.html), [pinned selection/config implementation](https://github.com/nektos/act/blob/4f411281417e88660bea1c1a1749aa71ae0bd60f/cmd/root.go), [path resolution](https://github.com/nektos/act/blob/4f411281417e88660bea1c1a1749aa71ae0bd60f/cmd/input.go).
