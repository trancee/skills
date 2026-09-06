# Account, namespace, and organization

## Account registration

Central Portal supports Google, GitHub, and local username/password registration. Use a valid email that remains accessible for verification and support.

Record these constraints before signup:

- Social login discloses the associated email address to Sonatype.
- Local password reset uses the Central sign-in flow; Sonatype states it will not request a password directly.
- Username cannot be renamed. A different username requires a new account.
- Lost username plus inaccessible email can make account recovery impossible.
- Full-name/email changes can require Central Support and new email verification.

Account creation and terms acceptance are external account/legal actions. Present the chosen provider/account and current terms link, then obtain explicit user confirmation at the point of action. Never paste credentials into chat or automation logs.

## Namespace meaning

A namespace is the allowed top-level Maven `groupId` prefix. A verified namespace permits publication under itself and descendants. Select the narrowest durable identity the publisher controls.

Examples:

- `com.example` verifies control of `example.com`; publication may use `com.example.library`.
- GitHub login can auto-provision `io.github.<username>` according to current Portal behavior.
- Supported hosted identities use their documented reversed-host namespace and repository challenge.

Do not invent a namespace from a project display name. Verify every publication `groupId` begins with the approved namespace at a segment boundary.

## Domain verification

For an owned domain:

1. Enter the exact reversed domain namespace.
2. Copy the Central-provided verification key.
3. Publish the required DNS TXT record at the exact domain/host Central specifies.
4. Query authoritative/public DNS and confirm the exact value.
5. Submit verification only after the record resolves.

DNS providers differ in whether the UI expects a relative host or full domain. Inspect the actual resulting record; do not infer it from the provider form. If a lookup returned NXDOMAIN before creation, recursive resolvers may cache that negative answer until TTL expiry.

Keep verification records unless current Central documentation explicitly permits removal and the organization accepts future re-verification risk.

## Hosted personal namespace verification

For supported services such as GitHub-based namespaces, Central may require a temporary public repository named exactly from the verification key.

1. Use the account that owns the namespace identity.
2. Create the exact public repository challenge only after user confirmation.
3. Verify its public URL from a logged-out request.
4. Submit namespace verification.
5. Delete or retain the challenge repository only according to current Central guidance and explicit user choice.

Repository creation/deletion and public disclosure are external side effects; obtain confirmation for each action.

## Existing namespaces and OSSRH

Before creating or migrating:

- Search the account's namespaces and organizations.
- Identify current admins and publishers.
- Determine whether the namespace is legacy OSSRH-managed or Central Portal-native.
- Preserve ownership evidence and support tickets.

A namespace cannot safely operate through conflicting OSSRH and Portal ownership/workflows. Follow Sonatype's documented migration path rather than creating a similar namespace or changing `groupId` to bypass ownership.

## Organizations and access

Creating a namespace can map it to an existing organization of the same name or create a new organization with the creator as administrator. A user without a namespace cannot self-join an organization; an administrator must invite them.

Apply least privilege:

- Separate organization administration from routine CI publishing where possible.
- Keep at least two recoverable administrators for team-owned coordinates.
- Remove departed publishers and rotate affected tokens.
- Record namespace, organization, role, and recovery owner in the release report without credentials.

## Completion evidence

Capture:

- Central account identifier and login method, excluding secrets.
- Verified namespace and proof method.
- Organization and administrators.
- Exact allowed `groupId` prefixes.
- Legacy OSSRH/migration status.
- Date and official documentation version checked.
