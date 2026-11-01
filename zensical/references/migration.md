# MkDocs and Material migration

## Inventory before cutover

1. RECORD original MkDocs/Material versions, configuration, plugin list/options, hooks, Python Markdown extensions, generated API pages, macros, CSS/JS, template overrides, URL layout, CI/deployment and environment-derived settings.
2. BUILD a representative baseline with the repository's existing MkDocs command and dependencies. Keep production unchanged during evaluation. Run Zensical against the existing YAML with `zensical build -f mkdocs.yml --strict`; preserve paths and outputs separately in disposable copies when comparing artifacts.
3. COMPARE home/deep pages, navigation, headings/anchors, cross-page references, search results, API docs, generated pages, scripts, custom templates, redirects, downloads and canonical URLs. A successful build is not evidence that a plugin still functions.

Source: [official reversible migration](https://zensical.org/docs/compatibility/mkdocs/migration/).

## Audit compatibility explicitly

| Boundary | Required decision |
| --- | --- |
| mkdocs.yml | Supported; TOML conversion is optional, not required for adoption. |
| hooks | Unsupported; replace with a separately invoked generation step or a verified supported mechanism before cutover. |
| Arbitrary MkDocs plugin | Not imported/run. Unsupported plugin config is silently ignored. Inventory every dependency and prove replacement behavior. |
| Supported plugin unknown option | Generally configuration error. Documented ignored settings can be silently ignored even when malformed. |
| MiniJinja theme template | No arbitrary Python calls; use supported filters/tests or a real supported customization. |
| MkDocs CLI flags/commands | No --theme, --site-dir, --use-directory-urls, gh-deploy or get-deps. Move settings into config; use explicit publishing/dependency management. |

1. READ the current [plugin matrix](https://zensical.org/docs/compatibility/mkdocs/plugins/) for **each configured plugin**, not a remembered list. Native rewrites accept familiar configuration but do not expose the MkDocs plugin API.
2. Examples available in the 0.0.74 baseline include search, tags, redirects, minify, offline, awesome-nav, autorefs, blog, macros and API-generation replacements. Install mkdocstrings-python for Python API handlers, and `markdown-exec[ansi]` only when execution is required. Most native replacements need no original plugin package.
3. CHECK installed-release evidence when docs lag: v0.0.74 added optimize support even though the documentation matrix still listed it as in progress when reviewed. Use the [release](https://github.com/zensical/zensical/releases/tag/v0.0.74) and [pinned implementation](https://github.com/zensical/zensical/blob/1b51ddc27903c947fbcb807f6d1337d17930c0fc/crates/zensical/src/compat/mkdocs/plugin/optimize.rs), then verify the requested options/output rather than inferring blanket compatibility.
4. For gen-files, use a supported autoapi/api-autonav path for API generation or invoke the existing generator separately before build. The documented uvx mkdocs-gen-files workaround requires mkdocs.yml, not zensical.toml. Retain generated-file ownership and validation in CI.
5. For macros, distinguish Markdown Jinja/Python execution from MiniJinja HTML templates: supported macro modules can execute Python, but only define_env is automatically called, environments are per-page, and page/context APIs differ. Verify required variable lifetime, hooks and missing values; do not suppress macro errors with empty output.

Sources: [supported/ignored plugins and installation caveats](https://zensical.org/docs/compatibility/mkdocs/plugins/), [Markdown compatibility](https://zensical.org/docs/compatibility/markdown/python-markdown/).

## Preserve customization and URLs

1. SELECT classic theme during Material migration:

```yaml
theme:
  variant: classic
```

2. COMPARE overrides with Material 9.6.18 or later templates, which were adapted for MiniJinja. Replace unsupported Python function calls with supported filters/tests only when behavior is preserved. Validate every overridden block; avoid reinstalling arbitrary Python plugins as a false template fix.
3. PRESERVE docs_dir, site_dir, use_directory_urls, nav, source links and deployment prefix. During dual-builder evaluation, use YAML examples so the same config remains readable by MkDocs. Move to TOML only as an intentional later configuration cutover, not a second drifting owner.
4. SWITCH local/CI commands and publishing only after every required plugin/content/customization/URL case passes. Remove obsolete dependencies/settings only when no retained path uses them; keep dual builders solely if that evaluation/rollback contract was requested.

Completion: all configured plugins/hooks/templates are classified and every required output is observed in Zensical; unsupported essential functionality remains a named prerequisite, not a silently narrowed migration.

Source: [migration and template differences](https://zensical.org/docs/compatibility/mkdocs/migration/).
