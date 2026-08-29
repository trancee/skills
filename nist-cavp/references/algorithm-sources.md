# NIST algorithm vector sources

Read this reference when locating the authoritative static CAVP archive or current ACVP specification. Start from the landing page instead of guessing a media URL.

| Primitive family | CAVP landing page |
| --- | --- |
| AES/TDES and ECB, CBC, CFB, OFB, CTR | [Block Ciphers](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/block-ciphers) |
| CCM, CMAC, GCM/GMAC/XPN, KW/KWP/TKW, XTS | [Block Cipher Modes](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/cavp-testing-block-cipher-modes) |
| SHA-1, SHA-2, SHA-3, SHAKE | [Secure Hashing](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/secure-hashing) |
| HMAC | [Message Authentication](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/message-authentication) |
| DSA, ECDSA, RSA signatures and key tests | [Digital Signatures](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/digital-signatures) |
| SP 800-108 KBKDF | [Key Derivation](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/key-derivation) |
| SP 800-90A DRBG | [Random Number Generators](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/random-number-generators) |
| KAS FFC/ECC and key confirmation | [Key Establishment](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/key-management/key-establishment) |
| ECC CDH, ECDSA sigGen component, SP 800-135 KDFs, RSADP, RSASP1 | [Component Testing](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/component-testing) |
| Historical algorithms | [Retired Testing](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/retired-testing) |

For a primitive component, inspect Component Testing before selecting a full-algorithm archive. For current algorithms and revisions, use the [ACVP supported-algorithms index](https://pages.nist.gov/ACVP/#supported) and open the linked algorithm specification.

Check the [algorithm prerequisite table](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/prerequisites) before formal ACVP work. Higher-level algorithms require separate validation of listed primitive dependencies.

The existence of a historical ZIP does not prove current approval or ACVTS support. Record the current standard/revision, landing page, test-system document, and retirement/support status with the selected vectors.
