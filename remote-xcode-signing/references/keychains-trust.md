# SSH keychain and certificate trust

## Separate the gates

| Gate | Evidence | Repair |
|---|---|---|
| Identity | `security find-identity -v -p codesigning KEYCHAIN` | Certificate **and matching private key**; valid code-signing EKU/expiry |
| Chain | No chain warning; issuer/intermediate available under System Default trust | Correct Apple intermediate from Apple PKI, visible in the SSH account's context |
| Unlock | Intended file-based keychain unlocked for the job | Unlock that keychain; bounded lock timeout |
| Key access | Real `codesign` operation succeeds in SSH without a dialog | Narrow codesign access/partition list on the intended key |
| Provisioning | Per-target profile authorizes identity/bundle/entitlements/distribution | Correct target-specific profiles; portal access only if authorized |

Sources: [TN3161 identities/trust](https://developer.apple.com/documentation/technotes/tn3161-inside-code-signing-certificates), [TN3125 profiles](https://developer.apple.com/documentation/technotes/tn3125-inside-code-signing-provisioning-profiles), installed `man security`/`man codesign`. [Rendered security manual](https://keith.github.io/xcode-man-pages/security.1.html) is a secondary mirror; installed help wins.

`security find-identity` without a policy defaults to a different policy; use `-p codesigning`. The supplied discussion's `verify-cert -p ssl -s example.com` tests SSL/hostname/CT policy, not app code signing. For a leaf certificate, use the installed `security verify-cert` code-signing policy (`codeSign`) and inspect the chain; do not turn a certificate into a trusted root.

## Supplied threads: specific chain failure

- [Developer thread 690923](https://developer.apple.com/forums/thread/690923): September 2021, SSH build reports `unable to build chain to self-signed root` then `errSecInternalComponent`; GUI Terminal succeeds. Author's accepted workaround imports **WWDR G3 intermediate** into `/Library/Keychains/System.keychain` rather than only the ephemeral custom keychain. Root cause is not established by that anecdote.
- [Support thread 253761477](https://discussions.apple.com/thread/253761477): March 2022, SSH reports `CSSMERR_TP_NOT_TRUSTED`; partition-list attempt did not solve it. Author links the first thread as the solution.

Use these as evidence to inspect chain discovery, not a universal instruction to install G3. Match the actual leaf issuer and current [Apple PKI](https://www.apple.com/certificateauthority/). If required, an administrator may import the **public matching intermediate** into System under existing trust; no private signing key, arbitrary downloaded root, or `Always Trust` override belongs there by default.

## Dedicated CI keychain

Prerequisites: authorized `.p12`, its password, a fresh keychain password, trusted full Xcode, dedicated account, Python 3 for the search-list snapshot snippets, and serialized jobs under that account. A unique keychain does not isolate the **per-user global search list**.

Security changes require approval of the exact account, identity, and scope. Secret manager injection is outside the package: never place real values in source/chat/logs. Disable shell tracing (`set +x`), history capture and command logging. **CLI password flags below expand secrets into process arguments**; environment variables do not eliminate that exposure. Use an isolated runner with trusted processes or an approved Security-framework integration/interactive provisioning if that exposure is unacceptable.

Use the keychain's actual password, not an assumed current macOS login password. `-D` selects key description; verify actual key attributes before matching. The documented codesign requirement is `apple:`; this research does not establish a `codesign:` token as necessary.

Run on the Mac inside the authorized job, not on the SSH client:

```bash
set -e
set +x
umask 077
: "${KC_PASSWORD:?inject job keychain password privately}"
: "${P12_PASSWORD:?inject PKCS12 password privately}"
: "${P12_FILE:?absolute authorized PKCS12 path}"
JOB_DIR=$(mktemp -d "${TMPDIR:-/tmp}/remote-xcode-sign.XXXXXX")
KEYCHAIN="$JOB_DIR/build.keychain-db"
SEARCH_SNAPSHOT="$JOB_DIR/original-search-list.json"

python3 - "$SEARCH_SNAPSHOT" <<'PY'
import json, shlex, subprocess, sys
original = shlex.split(subprocess.check_output(
    ["security", "list-keychains", "-d", "user"], text=True))
with open(sys.argv[1], "x", encoding="utf-8") as output:
    json.dump(original, output)
PY

cleanup() {
    original_status=$?
    trap - EXIT INT TERM
    set +e
    if [ -f "$SEARCH_SNAPSHOT" ]; then
        python3 - "$SEARCH_SNAPSHOT" <<'PY'
import json, subprocess, sys
with open(sys.argv[1], encoding="utf-8") as source:
    original = json.load(source)
subprocess.run(["security", "list-keychains", "-d", "user", "-s", *original], check=True)
PY
        if [ $? -ne 0 ]; then
            security lock-keychain "$KEYCHAIN" >/dev/null 2>&1
            printf '%s\n' "Search-list restoration failed; private snapshot retained at $SEARCH_SNAPSHOT" >&2
            [ "$original_status" -ne 0 ] || original_status=1
            exit "$original_status"
        fi
    fi
    if [ -f "$KEYCHAIN" ] && ! security delete-keychain "$KEYCHAIN"; then
        printf '%s\n' "Job-keychain deletion failed; private state retained at $JOB_DIR" >&2
        [ "$original_status" -ne 0 ] || original_status=1
        exit "$original_status"
    fi
    # JOB_DIR was created exclusively by this job and contains no build artifacts.
    if ! rm -rf "$JOB_DIR"; then
        [ "$original_status" -ne 0 ] || original_status=1
    fi
    exit "$original_status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

security create-keychain -p "$KC_PASSWORD" "$KEYCHAIN"
security set-keychain-settings -lut 21600 "$KEYCHAIN"
security unlock-keychain -p "$KC_PASSWORD" "$KEYCHAIN"
security import "$P12_FILE" -k "$KEYCHAIN" -P "$P12_PASSWORD" -T /usr/bin/codesign
security set-key-partition-list -S apple-tool:,apple: -s -k "$KC_PASSWORD" "$KEYCHAIN"

python3 - "$SEARCH_SNAPSHOT" "$KEYCHAIN" <<'PY'
import json, subprocess, sys
with open(sys.argv[1], encoding="utf-8") as source:
    original = json.load(source)
subprocess.run(["security", "list-keychains", "-d", "user", "-s", sys.argv[2], *original], check=True)
PY

security find-identity -v -p codesigning "$KEYCHAIN"
# Continue with the approved signing probe/build while this shell/job remains alive.
```

This is the CI keychain setup/teardown sequence, not a whole build runner. Keep it in the same job shell as probe/archive/export. Select timeout from job duration; the six-hour example is not an unlimited unlock. Do not use `security import -A`; partition-list changes affect matching keys, so this keychain must contain only the intended job identity. No default-keychain mutation is needed here. Persisting the secret outside the job keychain or extending unlock on login/System needs separate policy.

Cleanup restores the captured list and deletes only the job keychain/temp directory. If restoration fails, retain the private snapshot for operator repair rather than treating cleanup as successful; a production job wrapper must surface that failure. SIGKILL/power loss cannot execute shell traps: retain a narrowly scoped stale-job cleanup policy and bounded unlock settings. Never purge all keychains/profiles as recovery.

## Prove private-key use

After selecting the intended valid identity's certificate SHA-1 fingerprint (not a password):

```bash
: "${SIGNING_IDENTITY:?selected certificate fingerprint}"
cp /usr/bin/true "$JOB_DIR/signing-probe"
codesign --force --sign "$SIGNING_IDENTITY" --keychain "$KEYCHAIN" "$JOB_DIR/signing-probe"
codesign --verify --strict --verbose=2 "$JOB_DIR/signing-probe"
```

Only sign the disposable copy. Do not run it or modify the original system binary. This proves the selected private-key signing operation in the current SSH session; it does not prove iOS provisioning or deployment. Use Xcode to sign the app and embedded targets; never repair their signatures by blindly re-signing everything with `codesign --deep`.
