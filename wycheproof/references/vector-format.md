# Wycheproof format

Source truth: each vector's declared `schemas/` JSON schema at same pinned commit. `doc/` may be stale.

## Corpus

Current=`testvectors_v1/`; removed `testvectors/`; v0 only `wycheproof-v0-vectors`. Never mix loaders.
Unknown `schema` => reject, never infer from filename/`algorithm`.

Typical root:
- `algorithm`,`schema`,`header`,`notes`,`numberOfTests`,`testGroups`
- group: shared algorithm inputs, test `type`, `tests`, often `source{name,version}`
- root `generatorVersion` deprecated
- case: `tcId`,`comment`,`flags`,`result`, algorithm inputs/expected outputs

Read group before case; no flatten/cross-schema assumptions.

## Result

Interpret header+schema+flags+operation together.
- `valid`: accept + exact specified output/behavior
- `invalid`: reject; auth decrypt/key validation releases nothing
- `acceptable`: resolve every flag via `notes`; explicit compatibility/security policy; accept OR reject may be allowed; accepted requires output+safety

Never skip/default `acceptable`; report accept/reject+flags separately.

Pin `3fa63dd0344abb611f1fb1d77e119938603ea230` adds ML-KEM seed-key `MalleableCiphertext` cases. They are marked `valid`: decapsulation must take implicit rejection and return the exact expected `K`, not throw solely because ciphertext was modified. Use the group's operation and flag notes, not English meanings of `valid`/`invalid`.

## Encodings

- `HexBytes`: even hex bytes
- `BigInt`: signed two's-complement BE hex; width significant
- `Asn`: hex bytes, possibly malformed ASN.1
- `Der`: valid DER hex
- `Pem`: PEM string

Preserve leading zeros, signed semantics, malformed bytes, empty values, group lengths. No pre-API normalization.

## Verify

Full clone, pinned docs:
```bash
GOEXPERIMENT=jsonv2 go run ./tools/vectorgen fmt --check 'testvectors_v1/*.json'
GOEXPERIMENT=jsonv2 go run ./tools/vectorgen lint
```
vectorgen requires Go 1.26+ (go.mod pins `go 1.26.4`). On Go 1.26 set `GOEXPERIMENT=jsonv2` to expose `encoding/json/jsontext`; Go 1.27+ ships `json/v2` and `jsontext` as standard packages (no flag needed). Recheck `doc/vectorgen.md`.
Vendored subset: exact JSON Schema+transitive refs, then `scripts/check-vectors.py` for duplicate keys/count/ID/result/flag. Structural checker != schema validation.
