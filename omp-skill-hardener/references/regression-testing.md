# Hardening regression

Goal: distinguish observed failure vs approved behavior. Preserve redacted real scenario; no easy synthetic prompt.

## Spec v1

Use `assets/regression-test.json`. Paths relative `--root`; structural text=UTF-8; regex=Python multiline.

## Red/green

1. Write structural+behavior assertions pre-edit.
2. Old target: >=1 material FAIL. If proving old state would destroy work, cited pre-fix session + newly absent structural rule supplies red.
3. Apply approved edit.
4. RUN `--skip-replay`; PASS.
5. RUN affected replay; target skill read observed; behavior PASS.
6. Run adjacent existing evals.

## Runner

`omp -p --mode json --no-session --no-title`; skill filter; forced target read; cwd=`--root`. FAIL if no `read skill://name` or no final assistant text.

Options: `--model` only model-specific; `--timeout` bounded slow replay. Fake/cache invalid behavior proof; fake executable allowed only runner self-test.

## Assertions

Observable decision/refusal/order/boundary/omission. Exact wording only if contract. Structural-only insufficient; combine replay.

Nondeterministic FAIL => inspect cause. Rerun once only identified transient. Persistent instability => sharpen rule OR report no reliable regression; do not record fix.
