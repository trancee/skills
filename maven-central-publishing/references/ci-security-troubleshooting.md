# CI, credentials, safety, and troubleshooting

## Portal user tokens

Generate tokens from the Central Portal user-token page only after explicit user authorization. Tokens have a display name and may have an expiry. The username/password pair is shown once.

- Store both parts in an approved secret manager immediately.
- Do not use the interactive account password.
- Do not reuse legacy OSSRH tokens.
- Scope access through Central organization/namespace roles where available.
- Record owner, purpose, creation/expiry, rotation, and revocation without values.
- Rotate immediately after suspected exposure.

## Secret injection

Maven:

- Put server credentials in user/CI `settings.xml` generated at runtime or referenced through environment variables.
- Match the settings server ID to the publishing plugin/repository configuration.
- Keep settings files out of artifacts and clean them after the job.

Gradle:

- Read environment variables or injected Gradle properties through provider APIs.
- Keep values out of `gradle.properties` in the repository, task inputs printed by diagnostics, configuration-cache reports, and build scans.
- Mark custom task properties sensitive and avoid logging request headers.

PGP:

- Inject the armored/binary private key and passphrase from secrets.
- Import into an ephemeral keyring or use in-memory signing supported by the selected plugin.
- Pin/verify fingerprint without printing private material.
- Remove temporary keyring files on success, failure, and cancellation.

## CI release gates

Require:

1. Protected immutable tag/commit.
2. Expected branch/tag/version relationship.
3. Clean build from the selected commit.
4. Tests and project quality gates.
5. Complete generated publication inspection.
6. No coordinate already published.
7. `USER_MANAGED` validation for new or changed pipelines.
8. Environment approval immediately before irreversible publish.
9. Exact deployment UUID passed from validation to publish job.
10. No rebuild between validation and publish.

A publish job must consume the already validated deployment, not silently regenerate or upload different bytes.

## Point-of-risk confirmation

Immediately before publication, present:

```text
Central account / organization:
Verified namespace:
Coordinates and versions:
Source commit/tag:
Deployment UUID:
Publishing mode:
Validation state:
Irreversible effect: published files cannot be modified or deleted
```

Request explicit confirmation for that exact deployment. A prior request to “set up publishing,” successful validation, or approval of a pull request is not sufficient authorization to publish.

## Common failures

### Namespace/permissions

- `groupId` outside verified namespace -> correct coordinates or verify the exact parent namespace.
- Namespace owned elsewhere -> identify organization admin or legacy OSSRH migration; do not create a lookalike.
- Publisher lacks role -> organization admin grants the least required role.

### Authentication

- 401 -> verify Portal token pair, Base64 of `username:password`, expiry, and header scheme.
- 403 -> verify namespace/organization permissions and endpoint; rotating a valid token does not grant a missing role.
- Token works locally but not CI -> inspect variable scope/protection/newline encoding without echoing values.

### Component validation

- Missing POM metadata -> inspect generated POM and add required project/license/developer/SCM fields at source.
- Missing sources/Javadoc -> attach classified JARs to every applicable publication.
- Missing/invalid signature -> sign exact uploaded bytes, publish public key as currently required, and verify fingerprint/expiry.
- Invalid checksum -> regenerate after final signing and bundling inputs settle.
- Invalid path/name -> rebuild canonical Maven repository layout; avoid hand patching.
- Namespace mismatch -> inspect every module/publication coordinate, including Gradle/KMP target artifacts.

### Deployment lifecycle

- `FAILED` -> retrieve validation details by UUID, fix source, rebuild, upload a new deployment.
- Stuck `PENDING`/`VALIDATING` -> query current status and official service information before retrying.
- Timeout after upload/publish -> query by UUID/deployment name; never assume failure.
- Duplicate coordinate -> verify Central; issue a new version if already published.
- Published wrong content -> stop; publish a corrected new version and communicate deprecation/migration. Central does not support replacement/deletion.

## Redaction test

Before real credentials, use sentinel values and run the full dry path. Search captured logs, reports, build scans, task diagnostics, generated settings, and bundles for the sentinels. Fix every leak before injecting production tokens or signing keys.
