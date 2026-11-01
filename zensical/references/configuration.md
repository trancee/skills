# Configuration and authoring

## Select the configuration owner

1. USE `zensical.toml` for a new Zensical site and keep settings under `[project]`. For existing MkDocs sites, preserve `mkdocs.yml` until migration acceptance; YAML settings remain at the root, not under `project`.
2. SET `site_name`; set `site_url` to the real canonical deployment URL including any repository/subdirectory prefix. It is required for instant navigation/previews and useful sitemap/404 behavior. Do not leave a sample example.com URL in a deployed site.
3. RESOLVE `docs_dir` and `site_dir` relative to the config file, and `nav`, extra_css and extra_javascript paths relative to docs_dir. Keep both source/output within the project; use a docs subdirectory, not docs_dir=".". Keep output separate from source and outside source traversal.
4. PASS `-f path/to/config` to build/serve when configuration selection could be ambiguous. Set site_dir and use_directory_urls in configuration: corresponding MkDocs CLI flags do not exist in Zensical.

Sources: [basics](https://zensical.org/docs/setup/basics/), [new project](https://zensical.org/docs/usage/new/), [configuration path validation](https://github.com/zensical/zensical/blob/1b51ddc27903c947fbcb807f6d1337d17930c0fc/python/zensical/config.py).

## Navigation and publication boundaries

| Setting | Production build | Local preview |
| --- | --- | --- |
| exclude_docs | Omitted pages and matching assets | Omitted |
| draft_docs | Omitted pages and matching assets | Included; draft notice, omitted from automatic nav |
| not_in_nav | Built, searchable, in sitemap, omitted from automatic nav | Included, omitted from automatic nav |

1. USE multiline **strings** with one gitignore-style pattern per line; resolve patterns from docs_dir. A leading slash anchors at docs_dir; patterns without a slash match at any depth; `!` reverses a prior match only within the same setting. exclude_docs wins over draft_docs/not_in_nav.
2. KEEP secrets outside documentation sources. not_in_nav is not access control; excluded/draft files may still exist in repositories or previews. Bind previews locally by default.
3. USE automatic navigation for a simple folder hierarchy. For explicit navigation, set `[project].nav` to page strings or inline tables such as `{ "Guide" = "guide.md" }`; nested arrays form sections. Verify every intended entry resolves: unresolved navigation strings can be interpreted as URLs, so a green build alone is insufficient.
4. USE source-relative Markdown link targets such as `guide.md#verify-a-build`, not generated HTML paths. With directory URLs, guide.md normally emits guide/index.html at /guide/; with use_directory_urls=false it emits guide.html. Verify the actual generated paths and host routing.
5. ENABLE instant navigation only with a correct site_url/sitemap; custom scripts must handle page replacement.

Sources: [file patterns](https://zensical.org/docs/setup/basics/#file-patterns), [explicit navigation](https://zensical.org/docs/setup/navigation/#explicit-navigation), [Markdown links](https://zensical.org/docs/authoring/markdown/#linking-between-pages).

## Markdown and theme customization

1. WRITE Python Markdown, not an assumed CommonMark/GFM dialect. Indent nested list paragraphs, admonition bodies and tab bodies by four spaces. Keep one index.md per directory; README.md also maps to index.html, and having both is currently undefined.
2. DECLARE only the extensions the site uses under `[project.markdown_extensions]`, e.g. `admonition = {}`, `pymdownx.superfences = {}` and `pymdownx.tabbed.alternate_style = true`. Preserve existing YAML extension configuration during MkDocs evaluation.
3. USE page YAML frontmatter for description, template, hide and metadata. Include an explicit H1 and verify both navigation title and page heading; they are not always derived identically. Page metadata is not skill-package frontmatter.
4. PLACE CSS/JS inside docs_dir and register it with extra_css/extra_javascript. Use `document$.subscribe(...)` for page initialization with instant navigation; DOMContentLoaded alone does not cover internal navigation. Make initialization idempotent and dispose handlers/widgets where necessary.
5. USE `theme.variant = "classic"` for Material-compatible appearance or modern for a new site's chosen design. Configure custom_dir relative to the config file; prefer overrides/main.html block overrides and `{{ super() }}` to copying base.html wholesale. MiniJinja template rendering cannot call arbitrary Python functions.
6. For math, diagrams, icons or execution fences, read that feature's current documentation and include its required JS/extension dependencies. Enabling an extension is not proof its browser rendering works. Treat Markdown execution/macros and imported Python names as executable repository input; do not build an untrusted site with secrets available.

Sources: [Markdown dialect](https://zensical.org/docs/authoring/markdown/), [frontmatter](https://zensical.org/docs/authoring/frontmatter/), [extensions](https://zensical.org/docs/compatibility/markdown/python-markdown-extensions/), [customization](https://zensical.org/docs/customization/).

## Validation and diagnostics

1. RUN `zensical build --strict`. invalid_links and invalid_link_anchors are enabled by default. Keep validation enabled; fix the source target/anchor, not a generated HTML file. strict mode exits 1 when reported issues abort the build; verify that contract with a disposable broken link when setting up a new gate.
2. USE documented current validation keys, e.g. `[project.validation] invalid_links = true`. The unresolved/unused/shadowed reference/footnote checks are deprecated in their current form and have known edge cases. Do not enable them indiscriminately or call strict mode an exhaustive semantic/privacy/plugin audit.
3. USE `zensical build --clean` for suspected stale incremental output, especially after upgrades, then reproduce the original path. --clean clears the build cache, not merely an alias for MkDocs output cleanup.
4. For missing rebuilds, add the actual external source directory to watch. docs, themes and supported configured snippets/macros are watched automatically. Symlink targets outside watched directories need their containing directory in watch; do not enlarge watch roots to the whole workstation.
5. On import/theme errors, confirm the active project's Python environment, installed Zensical/UI dependency pair and supported wheel; uv symlink installation mode is unsupported. Use a supported uv link mode instead.
6. CHECK installed command help before copying flags. In 0.0.74, serve exposes --strict but labels it currently unsupported; production validation must run build --strict separately.

Sources: [validation](https://zensical.org/docs/setup/validation/), [clean builds](https://zensical.org/docs/usage/build/), [watch/symlinks](https://zensical.org/docs/setup/basics/#watch), [installation](https://zensical.org/docs/get-started/), exercised 0.0.74 CLI help.
