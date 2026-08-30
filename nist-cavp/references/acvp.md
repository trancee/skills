# ACVP/ACVTS

## Environment

- Demo: free practice; semi-volatile; no certificate
- Production: certificate path; NVLAP CST/17ACVT lab only
- access: [procedure](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/how-to-access-acvts)
- secrets (`key`,`cert`,`JWT`,`credential`) never repo/argv/chat/log

## Specs

READ [base protocol](https://pages.nist.gov/ACVP/draft-fussell-acvp-spec.html), [supported algorithms](https://pages.nist.gov/ACVP/#supported), exact algorithm spec, [prerequisites](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/prerequisites). Implement exact algorithm/revision/mode/capability/test/request/response schema.

Hierarchy: session -> vector set `vsId` -> group `tgId` -> case `tcId`. Preserve IDs. Unknown revision/mode/type/group/case field => FAIL CLOSED.

## Exchange

1. AUTH per live protocol/server.
2. REGISTER implemented capability+prereqs only.
3. CREATE session; fetch all vector-set URLs.
4. GET `/testSessions/{session}/vectorSets/{vectorSet}`.
5. EXECUTE every group/case at real implementation boundary.
6. BUILD algorithm-specific response with same ID hierarchy.
7. POST `/testSessions/{session}/vectorSets/{vectorSet}/results`.
8. GET disposition; diagnose by IDs.
9. Complete all sets+prereqs before certificate work.

Invariant: one request+response per `vsId`; no merge/schema reuse across revisions.
MCT may require `resultsArray`; DRBG/KAS ordered multistep data. Never assume generic `{tcId,result}`.
Expected endpoint allowed only `isSample:true`: `/expected`. Production client independent.
Server generates+grades vectors; client executes local crypto.

RECORD environment, protocol, algorithm/revision/mode, capabilities, session/set IDs, client+implementation versions, dispositions, prereqs. Redact sensitive identifiers/material.
