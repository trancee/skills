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
Current pin requires Go 1.26+ and `GOEXPERIMENT=jsonv2` until Go 1.27; recheck `doc/vectorgen.md`.
Vendored subset: exact JSON Schema+transitive refs, then `scripts/check-vectors.py` for duplicate keys/count/ID/result/flag. Structural checker != schema validation.
