# xtool project configuration and commands

Read this reference when creating, configuring, building, or deploying an xtool project. Refresh the [bundle controls](https://xtool.sh/documentation/xtool/control) and [first-app tutorial](https://xtool.sh/tutorials/xtool/first-app) before using newly introduced fields or commands.

## Generated project

Create a SwiftPM iOS application:

```bash
xtool new Hello
cd Hello
```

The generated project contains:

- `Package.swift`: SwiftPM products and targets;
- `xtool.yml`: app-bundle metadata;
- `.sourcekit-lsp/config.json`: SourceKit-LSP configuration for `arm64-apple-ios` and the Darwin Swift SDK;
- `Sources/Hello/`: application source.

## Build and deployment commands

Inspect current options with `xtool help <subcommand>` before composing flags.

- `xtool dev build`: compile and bundle without requiring a connected device.
- `xtool dev`: build, sign, install, and support the device development loop.
- `xtool devices`: list connected devices.
- `xtool install`: install an IPA.
- `xtool uninstall`: remove an installed app.
- `xtool launch`: launch an installed app.
- `xtool auth`: manage Apple Developer Services authentication.
- `xtool sdk`: manage the Darwin Swift SDK.
- `xtool ds`: interact with Apple Developer Services.

A successful build writes `xtool/<Name>.app` unless current command options select another artifact.

## `xtool.yml`

Start from the generated file. A minimal configuration is:

```yaml
version: 1
bundleID: com.example.Hello
```

Common controls include:

```yaml
version: 1
bundleID: com.example.Hello
product: Hello
infoPath: Info.plist
iconPath: Resources/AppIcon.png
entitlementsPath: App.entitlements
resources:
  - Resources/GoogleServices-Info.plist
```

- `bundleID`: unique application bundle identifier.
- `product`: SwiftPM product used as the application.
- `infoPath`: partial plist merged into the generated `Info.plist`.
- `iconPath`: application icon image.
- `entitlementsPath`: entitlement plist.
- `resources`: files copied to the root of the `.app` bundle.

Prefer SwiftPM target resources for normal package resources and access them through `Bundle.module`. Use top-level `resources` only for files that must be placed at the app-bundle root.

For app extensions, add a separate SwiftPM library product and target, then follow the current [app-extension guide](https://xtool.sh/documentation/xtool/appex). A typical declaration is:

```yaml
version: 1
bundleID: com.example.Hello
product: Hello
extensions:
  - product: HelloWidget
    infoPath: HelloWidget-Info.plist
```

Define the extension point in the extension's plist and verify current framework support before choosing an ExtensionKit or legacy extension design.

## Editor workflow

Install the editor's Swift/SourceKit-LSP integration. On Windows, open the project through the WSL remote. Preserve `.sourcekit-lsp/config.json`; it selects the Darwin SDK required for UIKit and SwiftUI modules.
