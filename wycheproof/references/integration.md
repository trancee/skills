# Wycheproof integration

## Pin/select

Source = full commit/release via submodule, vendored corpus+recorded commit, or versioned package preserving vector/schema revision. RECORD repo, commit, vectors, schemas, update path. Keep vector + exact declared schema + transitive refs. Validate corpus before crypto debugging.

Select from real public API:
1. primitive/operation/params/encodings/sizes
2. matching `testvectors_v1/` files at pin
3. read `algorithm`,`schema`,`header`,groups,sources
4. include every claimed group; unsupported explicit + API reason

No static filename/group catalog in adapter; discover from pin+schema.

## Adapter

One adapter per operation/encoding; generic parse separate. Test caller boundary.
Distinguish parser | primitive | verify/auth result | output compare | unsupported | internal error.
Only documented API rejection satisfies invalid case; crash/resource/adapter error != reject.
Pass raw ASN.1/DER/PEM/JWK/key/signature/ciphertext into public parser; normalization may erase attack.

## Assert

Apply `references/vector-format.md`.
- valid: accept + exact output
- invalid: explicit reject + no unauthorized output
- acceptable: named flag policy + accepted/rejected report

All directions: AEAD encrypt+decrypt/auth; signature exact key/signature encoding; key exchange complete secret+invalid-key policy; KEM keygen/encap/decap/invalid ciphertext by group.

Failure fields: commit,file,schema,algorithm,group type/source,`tcId`,result,flags/comment,expected,observed error/output. Resolve flag via root `notes`; flag != root cause.

## CI/update

Full selected corpus deterministic CI. Fast subset only if full job remains.
Update:
1. schema+structural validation
2. added/removed/reclassified review
3. schema/group-type review before adapter change
4. old+new corpus against same implementation for changed result
5. record acceptable-policy change

Invalid accepted => potential vulnerability. Minimize outside source vector; private report to affected maintainer before public exploit/vector.
