# Central Portal publishing routes

## Decision table

| Project/control need | Route | Notes |
| --- | --- | --- |
| Maven project | Official Central Publishing Maven Plugin | Prefer current official plugin and documentation |
| Gradle/Kotlin project | Maintained community Portal plugin or JReleaser | Sonatype does not provide an official Gradle plugin |
| Custom release system | Portal Publisher API | Build Maven-layout bundle and own state/error handling |
| Existing legacy plugin | OSSRH Staging compatibility service | Temporary migration bridge; confirm current support |
| Mutable development artifacts | Central snapshots repository | Separate endpoint/policy; no release validation |

Use one route per publication. Parallel plugin/API configuration causes duplicate or inconsistent deployments.

## Official Maven plugin

Read the current official plugin page/release before configuration. Pin the plugin version; do not copy a version from this skill.

Configure:

- Portal token username/password through Maven settings/server credentials.
- Deployment name when useful for traceability.
- `USER_MANAGED` publishing while establishing the pipeline.
- Bundle generation from the effective Maven reactor publications.

Exercise package/verify/deploy-to-staging behavior without final publication first. Inspect whether the selected goal uploads, validates, or publishes; Maven goal names are not an authorization boundary.

## Gradle and Kotlin

No official Sonatype Gradle plugin exists in the inspected documentation. Choose one maintained route deliberately:

- A community plugin that directly supports Central Portal.
- JReleaser with Central Portal support.
- A custom task that assembles the Maven-layout bundle and calls the Publisher API.
- A legacy Nexus/OSSRH plugin only through the documented compatibility service during migration.

Before adoption, verify plugin maintenance, current Portal API support, credential names, signing behavior, multi-module/KMP publication handling, validation versus publish task boundaries, and whether `autoPublish` is enabled.

Keep `maven-publish` as the artifact model owner. Avoid manually duplicating POM, sources, or signing configuration in the uploader.

## Publisher API

Refresh the [Publisher API](https://central.sonatype.org/publish/publish-portal-api/) before use.

Authentication uses:

```text
Authorization: Bearer base64(tokenUsername:tokenPassword)
```

Base64 is encoding, not encryption. Construct the header in memory from secret-store values; never print the combined credentials, Base64 value, or complete request command.

A deployment upload includes the bundle and publishing mode and returns a deployment UUID. Persist that UUID in nonsecret release state. Track states:

- `PENDING`
- `VALIDATING`
- `VALIDATED`
- `PUBLISHING`
- `PUBLISHED`
- `FAILED`

Use status lookup after network ambiguity. Never blindly re-upload because an HTTP client timed out after the server accepted the bundle.

## USER_MANAGED versus AUTOMATIC

`USER_MANAGED`:

1. Upload deployment.
2. Wait for validation.
3. Inspect errors or validated component list.
4. Drop the deployment or explicitly publish it.

This is the default safe first-release and CI mode because validation does not immediately make coordinates immutable.

`AUTOMATIC` publishes after validation succeeds. Treat selecting it as authorization to irreversibly release the entire validated bundle. Require an explicit pipeline policy and point-of-risk user approval before enabling or invoking it.

## OSSRH migration

Legacy concepts do not map mechanically:

- OSSRH account/token versus Portal account/user token.
- Staging repository close/release versus Portal deployment validate/publish.
- `oss.sonatype.org` or `s01.oss.sonatype.org` endpoints versus Central Portal/API endpoints.
- Namespace ownership in legacy OSSRH versus Portal organizations.

Inventory all CI jobs, Maven settings, Gradle plugins, repository URLs, environment variables, and release instructions. Follow Sonatype's current migration/compatibility documentation. Remove legacy endpoints/credentials only after the Portal route validates and a controlled release resolves successfully.

## Snapshots

Snapshots use a separate Central snapshot repository and require namespace enablement. They are not validated like release deployments, are mutable, and are subject to retention cleanup (documented as 90 days when inspected).

Enforce route from version:

```text
version endsWith "-SNAPSHOT" -> snapshot endpoint only
otherwise                     -> release deployment only
```

Snapshot success does not prove release metadata, signatures, bundle layout, or publish permissions.
