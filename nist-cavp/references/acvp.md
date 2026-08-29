# ACVP and ACVTS workflow

Read this reference when implementing an ACVP client, using ACVTS Demo, or preparing formal algorithm validation.

## Environments

- **ACVTS Demo:** sandbox-style, no-cost environment for exercising implementations and ACVP clients. Treat stored data as semi-volatile.
- **ACVTS Production:** certificate-issuing environment restricted to NVLAP-accredited CST and 17ACVT laboratories.

Follow the current [ACVTS access procedure](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/how-to-access-acvts). Protect client private keys, certificates, JWTs, and access credentials; keep them out of repositories, command arguments, chat, and logs.

Passing Demo or locally generated vectors is not a production validation. Only qualifying Production work through an accredited laboratory can create a listed algorithm certificate.

## Specifications

Read the [ACVP base protocol](https://pages.nist.gov/ACVP/draft-fussell-acvp-spec.html), the current [supported-algorithms index](https://pages.nist.gov/ACVP/#supported), and the linked algorithm-specific specification. Implement exact algorithm names, revisions, modes, capability properties, test types, request fields, and response fields.

Read the current [prerequisite table](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/prerequisites). Register and complete required primitive validations separately.

## Session hierarchy

- A test session contains vector sets.
- `vsId` identifies one algorithm vector-set request and response.
- `testGroups` contain shared properties and are identified by `tgId`.
- Individual tests are identified by `tcId`.

Preserve every identifier unchanged. Fail closed on an unknown revision, mode, test type, group property, or case field.

## Exchange

1. Authenticate according to the current base protocol and server instructions.
2. Register only capabilities the implementation actually supports.
3. Create a test session and retrieve its vector-set URLs.
4. Download each vector set from `/testSessions/{testSessionId}/vectorSets/{vectorSetId}`.
5. Execute each group and case against the implementation under test.
6. Build the algorithm-specific response with the same `vsId`, `tgId`, and `tcId` hierarchy.
7. Submit initial results to `/testSessions/{testSessionId}/vectorSets/{vectorSetId}/results`.
8. Retrieve the vector-set disposition and diagnose failures by identifiers.
9. Complete every vector set and required prerequisite before pursuing certification.

One request and one response correspond to each `vsId`. Do not merge vector sets or reuse one revision's response schema for another.

## Test types and expected values

Algorithm specifications define AFT, MCT, LDT, verification, generation, and stateful response shapes. MCT often returns a `resultsArray`; DRBG and KAS operations can require ordered multi-step data. Implement the specification, not a generic `{tcId, result}` assumption.

For sample sessions with `isSample: true`, the server can expose expected results at `/testSessions/{testSessionId}/vectorSets/{vectorSetId}/expected`. Production clients must not depend on expected-answer access.

The server generates vectors and validates submitted results; it does not run the cryptographic implementation. Keep the client adapter black-box and exercise the real implementation boundary.

## Diagnostics and records

Record server environment, protocol version, algorithm/revision/mode, capabilities, test-session ID, vector-set IDs, client version, implementation version, dispositions, and prerequisite status. Redact tokens, certificates, private keys, account identifiers, and sensitive operational data.
