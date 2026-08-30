---
name: nist-cavp
description: "Finds/parses/integrates NIST CAVP and ACVP vectors. Use for primitive/component vectors, offline regression corpora, ACVP clients, or validation preparation. Don't use for Wycheproof attack vectors, certification claims from static vectors, or non-crypto fixtures."
metadata:
  category: "cryptography"
  source: "https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/"
  sourceVersion: "CAVP page revision 2026-08-12; draft-ietf-acvp-spec-01"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-28T19:38:42+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T11:48:01+02:00"
---

# NIST CAVP/ACVP

## 1. Track

- static CAVP: deterministic offline legacy regression
- ACVP/ACVTS: capability-matched current vectors/client/validation prep
- Demo: practice only
- Production: certificate path only via accredited CST/17ACVT lab
- static/Demo success != certificate

## 2. Capability

RECORD exact algorithm, standard revision, mode/component operation, parameters, sizes, lengths, byte/bit orientation, test types, directions, implementation API.
Distinguish nearby operations (`GCM`/`GMAC`, `sigVer`/`sigGen`, full algorithm/component, `keyGen`/`encapDecap`). Define implemented capability before vector selection/registration.

## 3. Source

1. READ `references/algorithm-sources.md`.
2. Static: current landing page -> Test Vectors link; never guessed media URL.
3. Component: check Component Testing.
4. ACVP: supported index -> exact algorithm spec/revision/schema.
5. Formal path: include current prerequisite table.
6. Historical download availability != current approval/support.

## 4. Acquire

- static -> READ `references/legacy-vectors.md`; HTTPS; temp download; archive test; path/symlink safety; SHA-256; atomic rename; same checks nested archives
- preserve original + landing/direct URLs + UTC retrieval + digest + algorithm/revision/operation + members/README/governing doc
- ACVP -> READ `references/acvp.md`; preserve envelope/IDs; secrets never repo/argv/chat/log

## 5. Parse

1. READ bundled README + governing spec.
2. Legacy CAVS = ordered headers/fields/repeats/markers/cases/source lines, not INI.
3. RUN:
   ```bash
   python3 scripts/check-rsp.py path/to/vectors
   ```
4. Add `--require-field`, `--hex-field`, `--allow-marker` only from selected spec.
5. PRESERVE empty values, leading zeros, widths, repeats, bit lengths, case IDs.
6. REJECT malformed hex, unknown revision/type, impossible length, missing field, duplicate singleton, unsupported bit input.

## 6. Execute

Static:
- KAT/AFT/MMT: exact operation+group context
- MCT: exact recurrence; carry key/IV/state/message/output
- LDT: prescribed generator; stream input
- authenticated decrypt `FAIL`: reject; no plaintext
- signature `P`=>accept; `F`=>reject
- DRBG: exact prediction-resistance/reseed sequence
- randomized generation: only controlled entropy/nonce/private-state seam

ACVP:
1. Register implemented capabilities+prerequisites only.
2. Preserve every `vsId/tgId/tcId`; dispatch exact algorithm/revision/mode/group/`testType`; unknown=>FAIL CLOSED.
3. Emit spec-required response fields/order; one response per `vsId`.
4. Submit; retrieve disposition; diagnose by original IDs.
5. Expected endpoint only if `isSample:true`; Production independent.

## 7. Coverage+report

- run every applicable positive/negative/direction/size/parameter/stateful group for each claimed capability
- unsupported groups explicit; no silent filtering
- fast subset allowed only with defined full-corpus job
- parser/API separated by narrow operation adapter
- failure: source, entry/vector set, group context, `COUNT` or IDs, operation, lengths, expected, actual, first divergent state
- OUT: copy `assets/integration-report.md`; exact provenance/coverage/prereqs/commands/outcomes/limits
- formal-validation claim only with qualifying Production lab work + listed certificate

## Fail

- ambiguous algorithm/revision => STOP selection
- direct URL absent from landing => historical
- unsafe archive path/symlink => reject extraction
- checker vs documented shape => read governing doc before parser change
- bit case vs byte API => unsupported OR verified bit adapter; never round
- MCT/DRBG divergence => compare first internal checkpoint
- unknown ACVP revision/type => update from its spec; never borrow another revision
- Production unavailable => complete offline/Demo; status=not validated
