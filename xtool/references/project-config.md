# xtool project

REFRESH [bundle controls](https://xtool.sh/documentation/xtool/control)+[first app](https://xtool.sh/tutorials/xtool/first-app).

## Generate

```bash
xtool new Hello
cd Hello
```
Roles: `Package.swift`=products/targets; `xtool.yml`=bundle metadata; `.sourcekit-lsp/config.json`=Darwin `arm64-apple-ios`; `Sources/Hello/`=app.

## Commands

Check `xtool help SUBCOMMAND` first.
- `xtool dev build`: compile+bundle, no device
- `xtool dev`: build+sign+install+dev loop
- `devices`, `install`, `uninstall`, `launch`
- `auth`, `sdk`, `ds`
Default artifact: `xtool/<Name>.app` unless flags differ.

## `xtool.yml`

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
`bundleID` unique; `product` SwiftPM app product; `infoPath` partial merge; icon/entitlements paths; `resources` copied to `.app` root.
Ordinary resources: SwiftPM + `Bundle.module`. Top-level `resources` only bundle-root need.

Extension = separate SwiftPM library product+target; follow [app-extension guide](https://xtool.sh/documentation/xtool/appex):
```yaml
extensions:
  - product: HelloWidget
    infoPath: HelloWidget-Info.plist
```
Plist identifies extension point. Verify current ExtensionKit/legacy support.

Editor: Swift/SourceKit-LSP; Windows=WSl remote; preserve `.sourcekit-lsp/config.json`.
