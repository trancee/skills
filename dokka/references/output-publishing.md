# Dokka output and publishing

## Formats

- HTML: default, recommended, supports single/multi-project Kotlin, Java, Android, and KMP
- Javadoc: Alpha; translates Kotlin signatures to Java-like signatures; Gradle plugin `org.jetbrains.dokka-javadoc`; Maven goals experimental
- GFM/Jekyll: Alpha plugins; not supported by DGP v2, but usable through supported Maven/CLI plugin routes

Choose format from consumer needs, not extension familiarity. Never describe Alpha/experimental output as stable.

## HTML customization

Configure built-in HTML through typed plugin/publication DSL. Supported controls include `customAssets`, `customStyleSheets`, `templatesDir`, `footerMessage`, inherited-member separation, and expect/actual merging.

`customAssets` copies files to `<output>/images`. Supplying names such as `logo-icon.svg`, `style.css`, `logo-styles.css`, or `prism.css` overrides built-ins. Keep template overrides minimal: upstream template variables/directives can change. Validate every page class, navigation, search, theme, and relative asset path after customization.

## Task consumption

Use `dokkaGenerate` for normal all-format generation. Use `dokkaGeneratePublicationHtml` when another Gradle task needs an output directory declared through Gradle task wiring. Avoid hard-coded ordering against internal/alias tasks.

## Documentation archives

Gradle does not provide a ready-made javadoc JAR task. Create/retain a `Jar` task that consumes the intended Dokka publication output, sets the repository's documentation classifier, and attach it to the existing `MavenPublication`. Maven provides experimental `dokka:javadocJar`; custom HTML archives can use Maven JAR plugin with the Dokka output directory.

Verify locally:
1. generate documentation
2. build archive
3. list archive entries; require entry page and assets
4. publish to local/disposable repository
5. inspect POM/module metadata and classifier
6. open extracted entry page and follow source/external links

Publishing requirements can demand a `javadoc.jar` classifier without demanding Javadoc-format contents; confirm repository policy.
