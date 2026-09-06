---
name: maven-central-publishing
description: "Registers, configures, validates, publishes, and troubleshoots releases through the Sonatype Central Portal. Use when creating accounts or namespaces, verifying groupId ownership, generating user tokens, signing artifacts, configuring Maven or Gradle publication, building upload bundles, using the Portal API, migrating from OSSRH, publishing snapshots, or diagnosing deployment failures. Don't use for dependency consumption, private Nexus repositories, Gradle Plugin Portal, npm or PyPI, or treating an upload as legal or certification approval."
compatibility: "Targets the Sonatype Central Portal workflow documented 2026-09-06. Portal UI, APIs, supported plugins, terms, namespace rules, and snapshot behavior can change; refresh official documentation before onboarding or release. Inspector supports Maven/Gradle/JReleaser text configuration and requires Python 3.11+."
metadata:
  category: "development"
  source: "https://central.sonatype.org/register/central-portal/"
  sourceVersion: "Central Portal registration, namespace, requirements, publishing, API, tokens, OSSRH migration, and snapshot documentation inspected 2026-09-06"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-09-06T13:28:03+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-09-06T13:28:03+02:00"
---

# Maven Central Publishing

## Step 1: Define the release contract

1. CLASSIFY account onboarding | namespace verification | first release | existing release | snapshot | OSSRH migration | CI automation | failed deployment.
2. IDENTIFY owner, exact `groupId:artifactId:version` set, packaging, modules, release versus snapshot, build tool, signing owner, publication route, staging policy, target account/organization, and whether the action stops before external publication.
3. READ the current [Central registration guide](https://central.sonatype.org/register/central-portal/), [Publisher Terms](https://central.sonatype.org/publish/producer-terms/), and applicable linked documentation before account, namespace, credential, or publish actions.
4. TREAT a Central release as irreversible: published coordinates cannot be modified, replaced, or deleted; corrections require a new version.
5. REQUIRE the user to review applicable terms. Never accept terms, create an account/namespace/token, disclose credentials, or publish on the user's behalf without explicit authorization for that exact action.
6. ROUTE KMP artifact topology to `kotlin-multiplatform`, Gradle/toolchain mechanics to `kotlin-gradle`, API docs/Javadoc artifacts to `dokka`, and non-Central repositories to their own workflow.

Completion: owner, coordinates, version, artifacts, route, staging mode, credentials boundary, and maximum authorized external action are explicit.

## Step 2: Inspect the publication project

RUN from the repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

1. CONFIRM publication plugins, coordinates, release/snapshot version, POM metadata, binary/sources/Javadoc artifacts, signing, checksums/bundle tasks, current/legacy endpoints, token indirection, automatic publication, and CI workflows.
2. TREAT every finding as a lead; inspect the effective Maven publication/POM and generated repository layout before concluding compliance.
3. READ `references/artifacts-signing.md` before modifying artifact composition or signing. READ `references/publishing-routes.md` before selecting endpoints/plugins/API calls.

Completion: every publication and credential input has one owner, all produced coordinates are enumerated, and legacy/automatic paths are visible.

## Step 3: Register account and namespace

READ `references/account-namespace.md`.

1. IF no account exists, prepare the chosen Google, GitHub, or local-login path and a valid accessible email. RECORD that the Central username cannot be renamed.
2. IF a namespace already exists, identify its current Central Portal/legacy OSSRH ownership and organization administrators before creating anything.
3. SELECT the narrowest namespace matching the intended top-level `groupId`: auto-provisioned GitHub namespace, exact reversed owned domain, or supported hosted-personal namespace.
4. PREPARE the exact DNS TXT record or temporary public repository challenge. Verify the record/repository exists publicly before requesting verification; account for DNS NXDOMAIN caching.
5. STOP immediately before account creation, terms acceptance, namespace creation, verification submission, or organization invitation. Show exact account/provider, namespace, proof target/value, and side effect; obtain explicit user confirmation.
6. AFTER the user-authorized action, verify namespace status and organization membership in Central before configuring publication.

Completion: the intended account controls one verified namespace that contains every release `groupId`, with proof and administrators recorded.

## Step 4: Build Central-compliant components

1. ASSIGN immutable release versions; reject `SNAPSHOT` for a release deployment and reject reuse of any previously published coordinate/version.
2. GENERATE the primary artifact and POM. For non-`pom` packaging, generate sources and Javadoc JARs unless Central's current rules explicitly exempt that component.
3. POPULATE POM `name`, `description`, `url`, license name/URL/distribution, at least one developer, and SCM connection/developerConnection/URL from real project metadata.
4. PLACE every file under Maven repository layout derived from `groupId/artifactId/version`; use exact Maven filenames and keep all coordinates inside the verified namespace.
5. GENERATE detached ASCII-armored PGP `.asc` signatures for every artifact and POM, excluding checksum files. Generate required `.md5` and `.sha1`; add stronger checksums when the selected route/tool supports them.
6. BUILD a ZIP or `tar.gz` bundle only for routes that require one; include one or more complete components, no extra root directory, credentials, private keys, local metadata, or unrelated files, and remain below the current Portal size limit.

Completion: local staging layout contains complete uniquely versioned components, required metadata, signatures, checksums, and no secrets.

## Step 5: Configure credentials and signing safely

READ `references/ci-security-troubleshooting.md`.

1. GENERATE a Central Portal user token only after explicit user authorization. Record display name, owner, expiry, and storage location; capture the shown username/password exactly once without printing them.
2. USE Portal token credentials for Portal publishing. Never substitute legacy OSSRH credentials or the user's interactive password.
3. STORE token parts, PGP private key/passphrase, and CI variables in an approved secret store. Reference environment variables or injected Gradle/Maven properties; keep values out of source, command arguments, logs, reports, and build scans.
4. PIN the signing key fingerprint and verify public-key distribution policy. Use a noninteractive signing setup appropriate to CI without writing the key or passphrase into generated repository content.
5. ROTATE/revoke exposed or expired credentials before release. Verify masked logs with sentinel values before using real secrets.

Completion: all credentials are indirect, redacted, least-privileged, rotatable, and absent from versioned/build artifacts.

## Step 6: Select one publishing route

READ `references/publishing-routes.md`.

1. FOR Maven, prefer the current official Central Publishing Maven Plugin and configure its documented Central Portal flow.
2. FOR Gradle, select one maintained community Central Portal integration or JReleaser because Sonatype does not provide an official Gradle plugin; document ownership/version and avoid parallel publishers.
3. FOR direct integration, use the current Portal Publisher API with Bearer base64 of the Portal token username/password and preserve the returned deployment UUID.
4. FOR a legacy OSSRH migration, inventory namespace ownership, repository URLs, credentials, close/release semantics, and plugin behavior; one namespace cannot be active in incompatible legacy and Portal workflows simultaneously.
5. FOR snapshots, use only the current snapshot endpoint after namespace enablement; isolate `-SNAPSHOT` routing from releases and accept mutable retention behavior.
6. DEFAULT release staging to `USER_MANAGED`; avoid `AUTOMATIC` until a proven CI policy intentionally accepts irreversible publication immediately after validation.

Completion: exactly one route owns each release/snapshot publication and its endpoint, credentials, staging behavior, and rollback boundary are explicit.

## Step 7: Validate without publishing

1. RUN clean build, tests required by the project, POM generation, sources/Javadoc generation, signing, and local publication/bundle assembly.
2. INSPECT every generated path, filename, POM, signature, checksum, module/variant, and dependency scope; verify no coordinate collision or secret inclusion.
3. UPLOAD only to a non-publishing validation path when authorized. For Portal releases, create a `USER_MANAGED` deployment and wait for `VALIDATED` without publishing.
4. IF validation fails, preserve deployment ID and normalized errors, fix the source publication, rebuild from clean state, and use a new deployment. Drop the failed/test deployment when appropriate and authorized.
5. COPY `assets/central-release-report.md`; record namespace, exact coordinates, route, generated files, signatures, checksums, validation state, commands, and unverified conditions.

Completion: a clean immutable build is locally proven and, when authorized, Central reports `VALIDATED` while publication remains reversible.

## Step 8: Confirm, publish, and verify

1. PRESENT the exact account/organization, namespace, every coordinate/version, deployment UUID, route, `USER_MANAGED`/`AUTOMATIC` mode, validation result, and irreversible effect.
2. ASK for explicit point-of-risk confirmation immediately before `Publish`, `autoPublish`, an API publish request, or a command that performs either. Prior approval to configure or validate is not publication approval.
3. PUBLISH only the confirmed deployment. Never switch to `AUTOMATIC`, retry with a changed bundle, or publish additional modules without renewed confirmation.
4. TRACK deployment states (`PENDING`, `VALIDATING`, `VALIDATED`, `PUBLISHING`, `PUBLISHED`, `FAILED`) by UUID. Treat transport timeout as unknown state; query status before retrying.
5. AFTER `PUBLISHED`, verify the exact POM/artifacts/signatures/checksums from Central and dependency resolution through the canonical Maven Central consumer endpoint after propagation.
6. RECORD immutable release evidence and remove temporary bundles/secrets. If content is wrong, stop and prepare a corrected new version; never attempt replacement or deletion.

Completion: only explicitly confirmed coordinates are published, Central reports `PUBLISHED`, consumer resolution succeeds, and evidence contains no secrets.

## Error Handling

- Namespace verification fails -> confirm exact reversed domain or hosted-service challenge, public proof value, and DNS/repository visibility before retrying.
- DNS challenge returns NXDOMAIN -> wait for negative-cache expiry after publishing the exact TXT record; do not churn verification values.
- Namespace exists in OSSRH -> follow the documented migration path; never create competing ownership/workflows.
- 401/403 -> verify Portal token username/password, expiry, account/namespace role, Base64 construction, and secret injection without logging values.
- Missing sources/Javadoc/signatures/POM fields -> fix publication generation and rebuild; never patch an uploaded bundle by hand.
- Deployment is `FAILED` -> retrieve validation errors by deployment UUID, correct source configuration, and create a new deployment.
- Deployment request times out -> query state by UUID/name before retrying to avoid duplicate releases.
- Version already published -> choose a new version; Central releases cannot be overwritten.
- Snapshot sent to release API or release sent to snapshots -> fail before upload and correct version/endpoint routing.

## Official references

- Registration: https://central.sonatype.org/register/central-portal/
- Namespace verification: https://central.sonatype.org/register/namespace/
- Requirements: https://central.sonatype.org/publish/requirements/
- Portal publishing: https://central.sonatype.org/publish/publish-portal-guide/
- Publisher API: https://central.sonatype.org/publish/publish-portal-api/
