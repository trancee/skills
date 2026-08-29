---
name: wycheproof-crypto-test-vectors
description: "Integrates Project Wycheproof vectors to test cryptographic implementations against known attacks, specification edge cases, and implementation bugs. Use when adding Wycheproof JSON vectors, mapping result semantics, or auditing crypto test coverage. Don't use for NIST CAVP validation, generating new cryptographic vectors, or general unit tests unrelated to Wycheproof."
metadata:
  source: "https://github.com/C2SP/wycheproof"
  createdAt: "2026-08-28T19:26:56+02:00"
  updatedAt: "2026-08-29T17:06:38+02:00"
---

# Wycheproof Crypto Test Vectors

## Overview

Project Wycheproof (https://github.com/C2SP/wycheproof) is a community-managed repository of **340+ JSON test vector files** covering **30+ cryptographic algorithms**. It detects whether a library is vulnerable to **80+ categories of attacks** including invalid curve attacks, biased nonces, Bleichenbacher's attacks, padding oracle attacks, signature malleability, and more.

Test vectors are used by major crypto libraries: **OpenSSL, BoringSSL, Go crypto, pyca/cryptography, RustCrypto, swift-crypto, NSS, LibreSSL, Botan, Zig**, and many more.

## When to Use This Skill

- Validating a cryptographic library or implementation against known attack vectors
- Writing test suites for crypto code (AEAD, signatures, key exchange, MAC, KDF, etc.)
- Checking if a library correctly rejects invalid inputs (malformed keys, signatures, ciphertexts)
- Auditing crypto implementations for edge cases and specification compliance
- Testing post-quantum algorithms (ML-KEM/Kyber, ML-DSA/Dilithium)
- Verifying correct handling of ASN.1/DER/PEM/JWK encoded keys and signatures
- Regression testing after crypto library upgrades

## Do Not Use This Skill When

- You need to generate new cryptographic keys or certificates (this is for testing only)
- You need a full penetration testing framework (this provides test vectors, not a harness)
- The task involves non-cryptographic testing

## Instructions

1. **Identify the algorithm** — Determine which cryptographic primitive to test (e.g., AES-GCM, ECDSA, X25519).
2. **Clone or reference vectors** — Get the test vectors from `testvectors_v1/` in the Wycheproof repo.
3. **Load the JSON** — Parse the test vector file; use the `schema` field to understand the structure.
4. **Map inputs to your API** — For each test group, extract the key/parameters and iterate through test cases.
5. **Assert results** — For each test vector:
   - `"result": "valid"` → your implementation MUST accept this input and produce the expected output
   - `"result": "invalid"` → your implementation MUST reject this input (throw/return error)
   - `"result": "acceptable"` → your implementation MAY accept or reject; check `flags` for guidance
6. **Check flags and notes** — Use `flags` and the top-level `notes` dictionary to understand *why* a vector exists and what attack it tests.

## Algorithm Coverage

### Symmetric Encryption & AEAD
| Algorithm | Test File(s) | Test Type |
|-----------|-------------|-----------|
| AES-GCM | `aes_gcm_test.json` | AeadTest |
| AES-GCM-SIV | `aes_gcm_siv_test.json` | AeadTest |
| AES-EAX | `aes_eax_test.json` | AeadTest |
| AES-CCM | `aes_ccm_test.json` | AeadTest |
| AES-SIV-CMAC | `aes_siv_cmac_test.json` | DaeadTest |
| ChaCha20-Poly1305 | `chacha20_poly1305_test.json` | AeadTest |
| XChaCha20-Poly1305 | `xchacha20_poly1305_test.json` | AeadTest |
| AEGIS-128/128L/256 | `aegis128_test.json`, etc. | AeadTest |
| AES-CBC-PKCS5 | `aes_cbc_pkcs5_test.json` | IndCpaTest |
| AES-XTS | `aes_xts_test.json` | AeadTest |

### Digital Signatures
| Algorithm | Test File(s) | Test Type |
|-----------|-------------|-----------|
| ECDSA (multiple curves/hashes) | `ecdsa_secp256r1_sha256_test.json`, etc. (73 files) | EcdsaVerify / EcdsaP1363Verify |
| EdDSA (Ed25519, Ed448) | `ed25519_test.json`, `ed448_test.json` | EddsaVerify |
| DSA | `dsa_*.json` (8 files) | DsaVerify / DsaP1363Verify |
| RSA PKCS#1 v1.5 | `rsa_signature_*_test.json` (many files) | RsassaPkcs1Verify |
| RSA-PSS | `rsa_pss_*_test.json` | RsassaPssVerify |
| ML-DSA (Dilithium) | `mldsa_*.json` (9 files) | MldsaVerify / MldsaSign |

### Key Exchange
| Algorithm | Test File(s) | Test Type |
|-----------|-------------|-----------|
| ECDH (multiple curves) | `ecdh_secp256r1_test.json`, etc. (28 files) | EcdhTest |
| X25519 | `x25519_test.json`, `x25519_asn_test.json`, etc. | XdhComp / XdhAsnComp |
| X448 | `x448_test.json`, etc. | XdhComp |
| ML-KEM (Kyber) | `mlkem_*.json` (12 files) | MlkemTest |

### MACs & KDFs
| Algorithm | Test File(s) | Test Type |
|-----------|-------------|-----------|
| HMAC (multiple hashes) | `hmac_sha*_test.json` (12 files) | MacTest |
| AES-CMAC | `aes_cmac_test.json` | MacTest |
| KMAC128/256 | `kmac128_test.json`, `kmac256_test.json` | MacTest |
| SipHash | `siphash_*_test.json` (3 files) | MacTest |
| HKDF | `hkdf_sha*_test.json` (4 files) | HkdfTest |
| PBKDF2 | `pbkdf2_hmacsha*_test.json` (5 files) | PbkdfTest |

### RSA Encryption
| Algorithm | Test File(s) | Test Type |
|-----------|-------------|-----------|
| RSA-OAEP | `rsa_oaep_*_test.json` | RsaesOaepDecrypt |
| RSA PKCS#1 v1.5 Encrypt | `rsa_pkcs1_*_test.json` | RsaesPkcs1Decrypt |

### Other
| Algorithm | Test File(s) | Test Type |
|-----------|-------------|-----------|
| AES Key Wrap | `aes_wrap_test.json`, `aes_kwp_test.json` | KeywrapTest |
| BLS (BLS12-381) | `bls_*.json` (4 files) | Various |
| Primality Testing | `primality_test.json` | PrimalityTest |
| JSON Web Crypto/Encryption/Signature | `json_web_*.json` (4 files) | Various |

## Test Vector Structure

Every test vector JSON file follows this structure:

```
Root
├── algorithm: string        — e.g. "AES-GCM", "ECDSA"
├── schema: string           — JSON schema filename for validation
├── generatorVersion: string — currently "0.9"
├── numberOfTests: int       — total test case count
├── header: string[]         — description/documentation
├── notes: {                 — dictionary of flag descriptions
│     "FlagName": {
│       "bugType": "AUTH_BYPASS|CONFIDENTIALITY|EDGE_CASE|...",
│       "description": "...",
│       "effect": "...",
│       "links": ["..."],
│       "cves": ["CVE-..."]
│     }
│   }
└── testGroups: [            — array of test groups
      {
        "type": "AeadTest",  — test type identifier
        "keySize": 128,      — shared parameters
        "ivSize": 96,
        "tagSize": 128,
        "tests": [           — individual test vectors
          {
            "tcId": 1,
            "comment": "description",
            "flags": ["Ktv"],
            "key": "hex...",
            "iv": "hex...",
            "aad": "hex...",
            "msg": "hex...",
            "ct": "hex...",
            "tag": "hex...",
            "result": "valid|invalid|acceptable"
          }
        ]
      }
    ]
```

## Bug Types (What Tests Detect)

| Bug Type | Meaning | Severity |
|----------|---------|----------|
| `BASIC` | Basic functionality test | Low — sanity check |
| `AUTH_BYPASS` | Invalid integrity check accepted | High |
| `CONFIDENTIALITY` | Potential plaintext leakage (e.g., invalid curve attack) | Critical |
| `EDGE_CASE` | Special mathematical edge case | Medium — unclear exploitability |
| `SIGNATURE_MALLEABILITY` | Modified signature still validates | Medium-High |
| `MALLEABILITY` | Modified ciphertext decrypts to same plaintext | Medium |
| `BER_ENCODING` | BER accepted where DER is expected | Low-Medium |
| `CAN_OF_WORMS` | Small bug that can cascade to vulnerability | Medium |
| `MISSING_STEP` | Implementation skips a required step | High |
| `KNOWN_BUG` | Tests for a previously discovered vulnerability | High |
| `WRONG_PRIMITIVE` | Wrong algorithm/hash accepted | High |
| `MODIFIED_PARAMETER` | Tampered algorithm parameter not detected | High |
| `LEGACY` | Legacy/compatibility behavior | Low — informational |
| `FUNCTIONALITY` | Uncommon but valid parameter sizes | Low |
| `WEAK_PARAMS` | Below NIST 112-bit security recommendation | Medium |
| `DEFINED` | Edge case with defined behavior | Low |

## Data Types in Test Vectors

| Type | Format | Example |
|------|--------|---------|
| HexBytes | Hex-encoded byte array | `"5b9604fe14eadba931b0ccf34843dab9"` |
| BigInt | Hex twos-complement big-endian | `"0103"` = 259, `"ff40"` = -192, `"00ff"` = 255 |
| Asn | Hex-encoded ASN.1 (may be invalid) | `"3082..."` |
| Der | Valid DER encoding as hex | `"3082..."` |
| Pem | PEM-encoded key string | `"-----BEGIN PUBLIC KEY-----\n..."` |

## Key Integration Pattern

```python
# Generic pattern for any language
import json

def run_wycheproof_tests(vector_file, test_fn):
    """
    vector_file: path to a Wycheproof JSON test vector file
    test_fn: function(group, test_case) -> (passed: bool, error: str|None)
    """
    with open(vector_file) as f:
        data = json.load(f)

    failures = []
    for group in data["testGroups"]:
        for tc in group["tests"]:
            expected = tc["result"]  # "valid", "invalid", "acceptable"
            try:
                result = test_fn(group, tc)
                if expected == "valid" and not result:
                    failures.append(f"tc#{tc['tcId']}: valid vector rejected")
                elif expected == "invalid" and result:
                    failures.append(f"tc#{tc['tcId']}: invalid vector accepted")
                # "acceptable" — either accept or reject is fine
            except Exception as e:
                if expected == "valid":
                    failures.append(f"tc#{tc['tcId']}: exception on valid: {e}")

    return failures
```

## Resources

- `resources/implementation-playbook.md` for detailed language-specific examples (Python, Go, Node.js, Rust, Java).
