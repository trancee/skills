---
description: Validate a documentation build before publication.
---

# Guide

## Verify a build

Run `zensical build --strict` and inspect the generated site.

=== "pip environment"

    ```sh
    .venv/bin/zensical build --strict
    ```

=== "uv project"

    ```sh
    uv run zensical build --strict
    ```

Return to the [home page](index.md).
