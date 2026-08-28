# Wycheproof Crypto Test Vectors — Implementation Playbook

This file contains detailed implementation patterns, code examples, and checklists for integrating Wycheproof test vectors into cryptographic library test suites across multiple languages.

---

## Table of Contents

1. [Setup & Installation](#setup--installation)
2. [Python Implementation](#python-implementation)
3. [Go Implementation](#go-implementation)
4. [Node.js/TypeScript Implementation](#nodejstypescript-implementation)
5. [Rust Implementation](#rust-implementation)
6. [Java Implementation](#java-implementation)
7. [Algorithm-Specific Testing Patterns](#algorithm-specific-testing-patterns)
8. [CI/CD Integration](#cicd-integration)
9. [Interpreting Results](#interpreting-results)
10. [Common Pitfalls](#common-pitfalls)

---

## Setup & Installation

### Option 1: Git Submodule (Recommended)
```bash
git submodule add https://github.com/C2SP/wycheproof.git tests/wycheproof
git submodule update --init
```

### Option 2: Direct Clone
```bash
git clone https://github.com/C2SP/wycheproof.git tests/wycheproof
```

### Option 3: Go Module (for Go projects)
```go
// The repo exposes testvectors via go:embed
import "github.com/C2SP/wycheproof"
```

### Directory Structure
```
tests/wycheproof/
├── testvectors_v1/    # 340+ JSON test vector files
├── schemas/           # JSON Schema files for validation
└── doc/               # Algorithm-specific documentation
```

---

## Python Implementation

### AES-GCM Testing with pyca/cryptography

```python
import json
import pytest
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VECTORS_DIR = Path("tests/wycheproof/testvectors_v1")


def load_vectors(filename):
    """Load a Wycheproof test vector file."""
    with open(VECTORS_DIR / filename) as f:
        return json.load(f)


class TestAESGCM:
    """Test AES-GCM against Wycheproof vectors."""

    @pytest.fixture
    def vectors(self):
        return load_vectors("aes_gcm_test.json")

    def test_aes_gcm_vectors(self, vectors):
        for group in vectors["testGroups"]:
            key_size = group["keySize"]
            iv_size = group["ivSize"]
            tag_size = group["tagSize"]

            for tc in group["tests"]:
                tc_id = tc["tcId"]
                key = bytes.fromhex(tc["key"])
                iv = bytes.fromhex(tc["iv"])
                aad = bytes.fromhex(tc["aad"])
                msg = bytes.fromhex(tc["msg"])
                ct = bytes.fromhex(tc["ct"])
                tag = bytes.fromhex(tc["tag"])
                result = tc["result"]

                aesgcm = AESGCM(key)

                if result == "valid":
                    # Must encrypt correctly
                    ciphertext = aesgcm.encrypt(iv, msg, aad)
                    assert ciphertext == ct + tag, (
                        f"tc#{tc_id}: encryption mismatch"
                    )
                    # Must decrypt correctly
                    plaintext = aesgcm.decrypt(iv, ct + tag, aad)
                    assert plaintext == msg, (
                        f"tc#{tc_id}: decryption mismatch"
                    )

                elif result == "invalid":
                    # Must reject invalid ciphertext/tag
                    with pytest.raises(Exception):
                        aesgcm.decrypt(iv, ct + tag, aad)

                elif result == "acceptable":
                    # Either accept or reject is fine
                    try:
                        plaintext = aesgcm.decrypt(iv, ct + tag, aad)
                        # If accepted, must produce correct plaintext
                        assert plaintext == msg, (
                            f"tc#{tc_id}: wrong plaintext for acceptable"
                        )
                    except Exception:
                        pass  # Rejection is also acceptable


class TestECDSA:
    """Test ECDSA signature verification against Wycheproof vectors."""

    CURVE_MAP = {
        "secp256r1": "SECP256R1",
        "secp384r1": "SECP384R1",
        "secp521r1": "SECP521R1",
    }

    HASH_MAP = {
        "SHA-256": "SHA256",
        "SHA-384": "SHA384",
        "SHA-512": "SHA512",
    }

    def test_ecdsa_verify(self):
        from cryptography.hazmat.primitives.asymmetric import ec, utils
        from cryptography.hazmat.primitives import hashes, serialization

        vectors = load_vectors("ecdsa_secp256r1_sha256_test.json")

        for group in vectors["testGroups"]:
            # Load the public key from DER
            key_der = bytes.fromhex(group["keyDer"])
            try:
                public_key = serialization.load_der_public_key(key_der)
            except Exception:
                continue  # Skip unsupported key formats

            hash_name = group["sha"]
            hash_algo = getattr(hashes, self.HASH_MAP.get(hash_name, ""), None)
            if hash_algo is None:
                continue

            for tc in group["tests"]:
                tc_id = tc["tcId"]
                msg = bytes.fromhex(tc["msg"])
                sig = bytes.fromhex(tc["sig"])
                result = tc["result"]

                try:
                    public_key.verify(sig, msg, ec.ECDSA(hash_algo()))
                    verified = True
                except Exception:
                    verified = False

                if result == "valid":
                    assert verified, (
                        f"tc#{tc_id}: valid signature rejected — "
                        f"flags={tc.get('flags', [])}"
                    )
                elif result == "invalid":
                    assert not verified, (
                        f"tc#{tc_id}: invalid signature accepted — "
                        f"flags={tc.get('flags', [])}"
                    )
                # "acceptable" — no assertion, either is fine


class TestX25519:
    """Test X25519 key exchange against Wycheproof vectors."""

    def test_x25519_vectors(self):
        from cryptography.hazmat.primitives.asymmetric.x25519 import (
            X25519PrivateKey, X25519PublicKey
        )

        vectors = load_vectors("x25519_test.json")

        for group in vectors["testGroups"]:
            for tc in group["tests"]:
                tc_id = tc["tcId"]
                public_bytes = bytes.fromhex(tc["public"])
                private_bytes = bytes.fromhex(tc["private"])
                expected_shared = bytes.fromhex(tc["shared"])
                result = tc["result"]

                try:
                    private_key = X25519PrivateKey.from_private_bytes(
                        private_bytes
                    )
                    public_key = X25519PublicKey.from_public_bytes(
                        public_bytes
                    )
                    shared = private_key.exchange(public_key)
                    computed = True
                except Exception:
                    shared = None
                    computed = False

                if result == "valid":
                    assert computed and shared == expected_shared, (
                        f"tc#{tc_id}: valid X25519 exchange failed"
                    )
                elif result == "invalid":
                    if computed:
                        # Some invalid vectors have all-zero shared secret
                        # which libraries may either reject or compute
                        pass


class TestHMAC:
    """Test HMAC against Wycheproof vectors."""

    def test_hmac_sha256(self):
        import hmac as hmac_mod
        import hashlib

        vectors = load_vectors("hmac_sha256_test.json")

        for group in vectors["testGroups"]:
            tag_size = group["tagSize"] // 8  # bits to bytes

            for tc in group["tests"]:
                tc_id = tc["tcId"]
                key = bytes.fromhex(tc["key"])
                msg = bytes.fromhex(tc["msg"])
                expected_tag = bytes.fromhex(tc["tag"])
                result = tc["result"]

                computed_tag = hmac_mod.new(
                    key, msg, hashlib.sha256
                ).digest()[:tag_size]

                if result == "valid":
                    assert computed_tag == expected_tag, (
                        f"tc#{tc_id}: HMAC mismatch"
                    )
                elif result == "invalid":
                    assert computed_tag != expected_tag, (
                        f"tc#{tc_id}: invalid HMAC matched"
                    )
```

### Generic Test Runner (Python)

```python
"""
Generic Wycheproof test runner that works with any algorithm.
Subclass WycheproofTestBase and implement the test method.
"""
import json
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TestResult:
    tc_id: int
    expected: str
    passed: bool
    error: str = ""
    flags: list = None


class WycheproofTestBase(ABC):
    """Base class for Wycheproof test implementations."""

    VECTORS_DIR = Path("tests/wycheproof/testvectors_v1")

    def load(self, filename: str) -> dict:
        with open(self.VECTORS_DIR / filename) as f:
            return json.load(f)

    @abstractmethod
    def setup_group(self, group: dict) -> any:
        """Initialize state from test group parameters (e.g., load key)."""
        ...

    @abstractmethod
    def run_test(self, group_state: any, group: dict, tc: dict) -> bool:
        """
        Run a single test case. Return True if the operation succeeded,
        False if it was rejected/failed. Raise on unexpected errors.
        """
        ...

    def run(self, filename: str) -> list[TestResult]:
        data = self.load(filename)
        results = []

        for group in data["testGroups"]:
            try:
                state = self.setup_group(group)
            except Exception as e:
                # Can't set up this group (unsupported params)
                continue

            for tc in group["tests"]:
                tc_id = tc["tcId"]
                expected = tc["result"]
                flags = tc.get("flags", [])

                try:
                    success = self.run_test(state, group, tc)
                except Exception as e:
                    success = False

                if expected == "valid":
                    passed = success
                elif expected == "invalid":
                    passed = not success
                else:  # acceptable
                    passed = True  # Either outcome is fine

                results.append(TestResult(
                    tc_id=tc_id,
                    expected=expected,
                    passed=passed,
                    error="" if passed else f"Expected {expected}, got {'pass' if success else 'fail'}",
                    flags=flags,
                ))

        return results

    def summary(self, results: list[TestResult]) -> dict:
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = [r for r in results if not r.passed]
        return {
            "total": total,
            "passed": passed,
            "failed": len(failed),
            "failure_details": [
                {"tcId": r.tc_id, "expected": r.expected, "flags": r.flags, "error": r.error}
                for r in failed
            ],
        }
```

---

## Go Implementation

### AES-GCM Testing

```go
package crypto_test

import (
    "crypto/aes"
    "crypto/cipher"
    "encoding/hex"
    "encoding/json"
    "os"
    "testing"
)

type WycheproofAEAD struct {
    Algorithm    string            `json:"algorithm"`
    Schema       string            `json:"schema"`
    NumberOfTests int              `json:"numberOfTests"`
    Notes        map[string]any    `json:"notes"`
    TestGroups   []AEADTestGroup   `json:"testGroups"`
}

type AEADTestGroup struct {
    IvSize  int           `json:"ivSize"`
    KeySize int           `json:"keySize"`
    TagSize int           `json:"tagSize"`
    Type    string        `json:"type"`
    Tests   []AEADTestVector `json:"tests"`
}

type AEADTestVector struct {
    TcId    int      `json:"tcId"`
    Comment string   `json:"comment"`
    Flags   []string `json:"flags"`
    Key     string   `json:"key"`
    Iv      string   `json:"iv"`
    Aad     string   `json:"aad"`
    Msg     string   `json:"msg"`
    Ct      string   `json:"ct"`
    Tag     string   `json:"tag"`
    Result  string   `json:"result"`
}

func TestAESGCMWycheproof(t *testing.T) {
    data, err := os.ReadFile("testdata/wycheproof/testvectors_v1/aes_gcm_test.json")
    if err != nil {
        t.Fatal(err)
    }

    var vectors WycheproofAEAD
    if err := json.Unmarshal(data, &vectors); err != nil {
        t.Fatal(err)
    }

    for _, group := range vectors.TestGroups {
        for _, tc := range group.Tests {
            t.Run(fmt.Sprintf("tc%d", tc.TcId), func(t *testing.T) {
                key, _ := hex.DecodeString(tc.Key)
                iv, _ := hex.DecodeString(tc.Iv)
                aad, _ := hex.DecodeString(tc.Aad)
                msg, _ := hex.DecodeString(tc.Msg)
                ct, _ := hex.DecodeString(tc.Ct)
                tag, _ := hex.DecodeString(tc.Tag)

                block, err := aes.NewCipher(key)
                if err != nil {
                    if tc.Result == "valid" {
                        t.Fatalf("tc#%d: failed to create cipher for valid test: %v", tc.TcId, err)
                    }
                    return
                }

                gcm, err := cipher.NewGCMWithNonceSize(block, len(iv))
                if err != nil {
                    if tc.Result == "valid" {
                        t.Fatalf("tc#%d: failed to create GCM for valid test: %v", tc.TcId, err)
                    }
                    return
                }

                // Test decryption
                ciphertext := append(ct, tag...)
                plaintext, err := gcm.Open(nil, iv, ciphertext, aad)

                switch tc.Result {
                case "valid":
                    if err != nil {
                        t.Errorf("tc#%d: valid decryption failed: %v", tc.TcId, err)
                    } else if !bytes.Equal(plaintext, msg) {
                        t.Errorf("tc#%d: plaintext mismatch", tc.TcId)
                    }
                case "invalid":
                    if err == nil {
                        t.Errorf("tc#%d: invalid ciphertext was accepted", tc.TcId)
                    }
                case "acceptable":
                    // Either outcome is fine
                }
            })
        }
    }
}
```

### Using the Go Embed Package

```go
package crypto_test

import (
    "github.com/C2SP/wycheproof"
    "testing"
)

func TestWithEmbed(t *testing.T) {
    // The wycheproof module provides embedded test vectors
    data, err := wycheproof.ReadFile("testvectors_v1/aes_gcm_test.json")
    if err != nil {
        t.Fatal(err)
    }
    // ... parse and test
}
```

### ECDH Testing (Go)

```go
package crypto_test

import (
    "crypto/ecdh"
    "encoding/hex"
    "encoding/json"
    "os"
    "testing"
)

type XdhTestFile struct {
    Algorithm  string         `json:"algorithm"`
    TestGroups []XdhTestGroup `json:"testGroups"`
}

type XdhTestGroup struct {
    Curve string          `json:"curve"`
    Type  string          `json:"type"`
    Tests []XdhTestVector `json:"tests"`
}

type XdhTestVector struct {
    TcId    int      `json:"tcId"`
    Comment string   `json:"comment"`
    Flags   []string `json:"flags"`
    Public  string   `json:"public"`
    Private string   `json:"private"`
    Shared  string   `json:"shared"`
    Result  string   `json:"result"`
}

func TestX25519Wycheproof(t *testing.T) {
    data, _ := os.ReadFile("testdata/wycheproof/testvectors_v1/x25519_test.json")
    var vectors XdhTestFile
    json.Unmarshal(data, &vectors)

    for _, group := range vectors.TestGroups {
        if group.Curve != "curve25519" {
            continue
        }
        for _, tc := range group.Tests {
            privBytes, _ := hex.DecodeString(tc.Private)
            pubBytes, _ := hex.DecodeString(tc.Public)
            expectedShared, _ := hex.DecodeString(tc.Shared)

            privKey, err := ecdh.X25519().NewPrivateKey(privBytes)
            if err != nil {
                if tc.Result == "valid" {
                    t.Errorf("tc#%d: cannot create private key: %v", tc.TcId, err)
                }
                continue
            }

            pubKey, err := ecdh.X25519().NewPublicKey(pubBytes)
            if err != nil {
                if tc.Result == "valid" {
                    t.Errorf("tc#%d: cannot create public key: %v", tc.TcId, err)
                }
                continue
            }

            shared, err := privKey.ECDH(pubKey)
            if tc.Result == "valid" {
                if err != nil {
                    t.Errorf("tc#%d: ECDH failed: %v", tc.TcId, err)
                } else if !bytes.Equal(shared, expectedShared) {
                    t.Errorf("tc#%d: shared secret mismatch", tc.TcId)
                }
            } else if tc.Result == "invalid" && err == nil {
                // Check if shared secret is all zeros (low-order point)
                allZero := true
                for _, b := range shared {
                    if b != 0 { allZero = false; break }
                }
                if !allZero {
                    t.Errorf("tc#%d: invalid exchange succeeded with non-zero result", tc.TcId)
                }
            }
        }
    }
}
```

---

## Node.js/TypeScript Implementation

### AES-GCM Testing

```typescript
import { readFileSync } from "fs";
import { createCipheriv, createDecipheriv } from "crypto";
import { describe, it, expect } from "vitest";

interface AeadTestVector {
  tcId: number;
  comment: string;
  flags: string[];
  key: string;
  iv: string;
  aad: string;
  msg: string;
  ct: string;
  tag: string;
  result: "valid" | "invalid" | "acceptable";
}

interface AeadTestGroup {
  ivSize: number;
  keySize: number;
  tagSize: number;
  type: string;
  tests: AeadTestVector[];
}

interface WycheproofFile {
  algorithm: string;
  schema: string;
  numberOfTests: number;
  notes: Record<string, { bugType: string; description: string }>;
  testGroups: AeadTestGroup[];
}

function loadVectors(filename: string): WycheproofFile {
  const raw = readFileSync(
    `tests/wycheproof/testvectors_v1/${filename}`,
    "utf-8"
  );
  return JSON.parse(raw);
}

describe("AES-GCM Wycheproof", () => {
  const vectors = loadVectors("aes_gcm_test.json");

  for (const group of vectors.testGroups) {
    // Only test standard 96-bit IV (Node.js crypto default)
    if (group.ivSize !== 96) continue;

    const tagLength = group.tagSize / 8;

    for (const tc of group.tests) {
      it(`tc#${tc.tcId}: ${tc.result} — ${tc.comment || tc.flags.join(",")}`, () => {
        const key = Buffer.from(tc.key, "hex");
        const iv = Buffer.from(tc.iv, "hex");
        const aad = Buffer.from(tc.aad, "hex");
        const msg = Buffer.from(tc.msg, "hex");
        const ct = Buffer.from(tc.ct, "hex");
        const tag = Buffer.from(tc.tag, "hex");

        if (tc.result === "valid") {
          // Test encryption
          const cipher = createCipheriv(
            `aes-${group.keySize}-gcm` as any,
            key,
            iv,
            { authTagLength: tagLength }
          );
          cipher.setAAD(aad);
          const encrypted = Buffer.concat([cipher.update(msg), cipher.final()]);
          const computedTag = cipher.getAuthTag();
          expect(encrypted).toEqual(ct);
          expect(computedTag).toEqual(tag);

          // Test decryption
          const decipher = createDecipheriv(
            `aes-${group.keySize}-gcm` as any,
            key,
            iv,
            { authTagLength: tagLength }
          );
          decipher.setAAD(aad);
          decipher.setAuthTag(tag);
          const decrypted = Buffer.concat([
            decipher.update(ct),
            decipher.final(),
          ]);
          expect(decrypted).toEqual(msg);
        } else if (tc.result === "invalid") {
          // Must reject
          expect(() => {
            const decipher = createDecipheriv(
              `aes-${group.keySize}-gcm` as any,
              key,
              iv,
              { authTagLength: tagLength }
            );
            decipher.setAAD(aad);
            decipher.setAuthTag(tag);
            decipher.update(ct);
            decipher.final();
          }).toThrow();
        }
        // "acceptable" — no assertion
      });
    }
  }
});
```

### ECDSA Verification (Node.js)

```typescript
import { createVerify } from "crypto";
import { readFileSync } from "fs";

interface EcdsaTestVector {
  tcId: number;
  comment: string;
  flags: string[];
  msg: string;
  sig: string;
  result: "valid" | "invalid" | "acceptable";
}

interface EcdsaTestGroup {
  keyDer: string;
  keyPem: string;
  sha: string;
  type: string;
  tests: EcdsaTestVector[];
}

describe("ECDSA Wycheproof", () => {
  const data = JSON.parse(
    readFileSync(
      "tests/wycheproof/testvectors_v1/ecdsa_secp256r1_sha256_test.json",
      "utf-8"
    )
  );

  const hashMap: Record<string, string> = {
    "SHA-256": "sha256",
    "SHA-384": "sha384",
    "SHA-512": "sha512",
  };

  for (const group of data.testGroups) {
    const pem = group.keyPem;
    const hashAlgo = hashMap[group.sha];
    if (!hashAlgo) continue;

    for (const tc of group.tests) {
      it(`tc#${tc.tcId}: ${tc.result}`, () => {
        const msg = Buffer.from(tc.msg, "hex");
        const sig = Buffer.from(tc.sig, "hex");

        const verifier = createVerify(hashAlgo);
        verifier.update(msg);

        let verified: boolean;
        try {
          verified = verifier.verify(pem, sig);
        } catch {
          verified = false;
        }

        if (tc.result === "valid") {
          expect(verified).toBe(true);
        } else if (tc.result === "invalid") {
          expect(verified).toBe(false);
        }
      });
    }
  }
});
```

---

## Rust Implementation

### AES-GCM Testing with aes-gcm crate

```rust
use aes_gcm::{Aes128Gcm, Aes256Gcm, Key, Nonce};
use aes_gcm::aead::{Aead, KeyInit, Payload};
use serde::Deserialize;
use std::fs;

#[derive(Deserialize)]
struct WycheproofAead {
    algorithm: String,
    #[serde(rename = "testGroups")]
    test_groups: Vec<AeadTestGroup>,
}

#[derive(Deserialize)]
struct AeadTestGroup {
    #[serde(rename = "ivSize")]
    iv_size: usize,
    #[serde(rename = "keySize")]
    key_size: usize,
    #[serde(rename = "tagSize")]
    tag_size: usize,
    tests: Vec<AeadTestVector>,
}

#[derive(Deserialize)]
struct AeadTestVector {
    #[serde(rename = "tcId")]
    tc_id: u32,
    comment: String,
    flags: Vec<String>,
    key: String,
    iv: String,
    aad: String,
    msg: String,
    ct: String,
    tag: String,
    result: String,
}

#[test]
fn test_aes_gcm_wycheproof() {
    let data = fs::read_to_string(
        "tests/wycheproof/testvectors_v1/aes_gcm_test.json"
    ).unwrap();
    let vectors: WycheproofAead = serde_json::from_str(&data).unwrap();

    for group in &vectors.test_groups {
        // Only test standard 96-bit nonce
        if group.iv_size != 96 { continue; }

        for tc in &group.tests {
            let key = hex::decode(&tc.key).unwrap();
            let nonce_bytes = hex::decode(&tc.iv).unwrap();
            let aad = hex::decode(&tc.aad).unwrap();
            let msg = hex::decode(&tc.msg).unwrap();
            let ct = hex::decode(&tc.ct).unwrap();
            let tag = hex::decode(&tc.tag).unwrap();

            let nonce = Nonce::from_slice(&nonce_bytes);
            let mut ciphertext_with_tag = ct.clone();
            ciphertext_with_tag.extend_from_slice(&tag);

            match group.key_size {
                128 => {
                    let cipher = Aes128Gcm::new(Key::<Aes128Gcm>::from_slice(&key));
                    let payload = Payload { msg: &ciphertext_with_tag, aad: &aad };
                    let result = cipher.decrypt(nonce, payload);

                    match tc.result.as_str() {
                        "valid" => {
                            let plaintext = result.unwrap_or_else(|_| {
                                panic!("tc#{}: valid decryption failed", tc.tc_id)
                            });
                            assert_eq!(plaintext, msg, "tc#{}: plaintext mismatch", tc.tc_id);
                        }
                        "invalid" => {
                            assert!(result.is_err(),
                                "tc#{}: invalid ciphertext accepted", tc.tc_id);
                        }
                        _ => {} // acceptable
                    }
                }
                256 => {
                    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(&key));
                    let payload = Payload { msg: &ciphertext_with_tag, aad: &aad };
                    let result = cipher.decrypt(nonce, payload);

                    match tc.result.as_str() {
                        "valid" => {
                            let plaintext = result.unwrap_or_else(|_| {
                                panic!("tc#{}: valid decryption failed", tc.tc_id)
                            });
                            assert_eq!(plaintext, msg, "tc#{}: plaintext mismatch", tc.tc_id);
                        }
                        "invalid" => {
                            assert!(result.is_err(),
                                "tc#{}: invalid ciphertext accepted", tc.tc_id);
                        }
                        _ => {}
                    }
                }
                _ => continue,
            }
        }
    }
}
```

---

## Java Implementation

### AES-GCM Testing

```java
import com.google.gson.*;
import javax.crypto.*;
import javax.crypto.spec.*;
import java.nio.file.*;
import java.util.*;
import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

public class AesGcmWycheproofTest {

    record TestVector(int tcId, String comment, List<String> flags,
                      String key, String iv, String aad, String msg,
                      String ct, String tag, String result) {}

    @Test
    void testAesGcm() throws Exception {
        String json = Files.readString(
            Path.of("src/test/resources/wycheproof/testvectors_v1/aes_gcm_test.json"));
        JsonObject root = JsonParser.parseString(json).getAsJsonObject();

        for (JsonElement groupEl : root.getAsJsonArray("testGroups")) {
            JsonObject group = groupEl.getAsJsonObject();
            int ivSize = group.get("ivSize").getAsInt();
            int keySize = group.get("keySize").getAsInt();
            int tagSize = group.get("tagSize").getAsInt();

            for (JsonElement testEl : group.getAsJsonArray("tests")) {
                JsonObject tc = testEl.getAsJsonObject();
                int tcId = tc.get("tcId").getAsInt();
                String result = tc.get("result").getAsString();

                byte[] key = hexToBytes(tc.get("key").getAsString());
                byte[] iv = hexToBytes(tc.get("iv").getAsString());
                byte[] aad = hexToBytes(tc.get("aad").getAsString());
                byte[] msg = hexToBytes(tc.get("msg").getAsString());
                byte[] ct = hexToBytes(tc.get("ct").getAsString());
                byte[] tag = hexToBytes(tc.get("tag").getAsString());

                try {
                    Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
                    GCMParameterSpec spec = new GCMParameterSpec(tagSize, iv);
                    SecretKeySpec keySpec = new SecretKeySpec(key, "AES");

                    // Decrypt
                    cipher.init(Cipher.DECRYPT_MODE, keySpec, spec);
                    cipher.updateAAD(aad);
                    byte[] ctWithTag = new byte[ct.length + tag.length];
                    System.arraycopy(ct, 0, ctWithTag, 0, ct.length);
                    System.arraycopy(tag, 0, ctWithTag, ct.length, tag.length);
                    byte[] plaintext = cipher.doFinal(ctWithTag);

                    if ("invalid".equals(result)) {
                        fail("tc#" + tcId + ": invalid ciphertext was accepted");
                    }
                    if ("valid".equals(result)) {
                        assertArrayEquals(msg, plaintext,
                            "tc#" + tcId + ": plaintext mismatch");
                    }
                } catch (Exception e) {
                    if ("valid".equals(result)) {
                        fail("tc#" + tcId + ": valid decryption threw: " + e);
                    }
                    // "invalid" throwing is expected; "acceptable" either way
                }
            }
        }
    }

    private static byte[] hexToBytes(String hex) {
        int len = hex.length();
        byte[] data = new byte[len / 2];
        for (int i = 0; i < len; i += 2) {
            data[i / 2] = (byte) ((Character.digit(hex.charAt(i), 16) << 4)
                + Character.digit(hex.charAt(i + 1), 16));
        }
        return data;
    }
}
```

---

## Algorithm-Specific Testing Patterns

### AEAD (AES-GCM, ChaCha20-Poly1305, AEGIS, etc.)

**Test inputs:** `key`, `iv` (nonce), `aad`, `msg` (plaintext), `ct` (ciphertext), `tag`
**Test flow:**
1. For `valid`: encrypt(key, iv, aad, msg) → verify ct and tag match; decrypt(key, iv, aad, ct||tag) → verify plaintext matches
2. For `invalid`: decrypt MUST fail (corrupted ct, wrong tag, wrong key, etc.)
3. Watch for: counter wrap (GCM), nonce reuse, non-standard IV sizes, non-standard tag sizes

### Digital Signatures (ECDSA, EdDSA, RSA, DSA)

**Test inputs:** Public key (DER/PEM/JWK), `msg`, `sig`
**Test flow:**
1. Load public key from group
2. For each vector: verify(pubkey, msg, sig)
3. `valid` → MUST verify; `invalid` → MUST NOT verify
4. Watch for: signature malleability, BER vs DER encoding, wrong hash, small r/s values

### Key Exchange (ECDH, X25519, X448)

**Test inputs:** `private` key, `public` key, expected `shared` secret
**Test flow:**
1. Compute shared_secret = DH(private, public)
2. `valid` → must match expected; `invalid` → must reject or produce all-zeros
3. Watch for: invalid curve attacks, low-order points, twist points, wrong curve

### MAC (HMAC, CMAC, KMAC, SipHash)

**Test inputs:** `key`, `msg`, `tag`
**Test flow:**
1. Compute MAC(key, msg) and compare with expected `tag`
2. `valid` → must match; `invalid` → must not match (typically truncation issues)
3. Watch for: tag truncation, key length edge cases

### KDF (HKDF, PBKDF2)

**Test inputs vary:**
- HKDF: `ikm` (input key material), `salt`, `info`, `size`, `okm` (output)
- PBKDF2: `password`, `salt`, `iterationCount`, `dkLen`, `dk` (derived key)

### RSA Encryption (OAEP, PKCS#1)

**Test inputs:** Private key (in group), `msg`, `ct` (ciphertext)
**Test flow:**
1. Decrypt ct using private key
2. `valid` → plaintext must match msg; `invalid` → must reject
3. Watch for: Bleichenbacher attacks, padding oracle, Manger's attack

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Crypto Tests
on: [push, pull_request]

jobs:
  wycheproof:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive   # Pull wycheproof submodule

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -e ".[test]"
      - run: pytest tests/wycheproof/ -v --tb=short
```

### Keeping Vectors Updated

```bash
# In CI or as a periodic task
git submodule update --remote tests/wycheproof
# Run tests to catch regressions with new vectors
```

---

## Interpreting Results

### Failure Triage Checklist

1. **Check the `result` field** — Is it `valid`, `invalid`, or `acceptable`?
2. **Check the `flags`** — Look up each flag in the top-level `notes` dictionary
3. **Check the `bugType`** — Prioritize by severity:
   - 🔴 `CONFIDENTIALITY`, `AUTH_BYPASS`, `KNOWN_BUG` — Critical, fix immediately
   - 🟠 `MISSING_STEP`, `WRONG_PRIMITIVE`, `MODIFIED_PARAMETER` — High priority
   - 🟡 `SIGNATURE_MALLEABILITY`, `CAN_OF_WORMS`, `EDGE_CASE` — Medium, investigate
   - 🟢 `BER_ENCODING`, `LEGACY`, `FUNCTIONALITY`, `WEAK_PARAMS` — Low, policy decision
4. **Check for CVEs** — The `cves` field in notes links to known vulnerabilities
5. **Check the `comment`** — Often describes the specific attack or edge case

### Handling "acceptable" Results

`"result": "acceptable"` means the test vector is in a gray area. Your library can either accept or reject it. Use the `flags` to decide:

- **BER encoding flags** → If your library is strict DER-only, reject. If it needs legacy compat, accept.
- **Weak parameter flags** → If your security policy requires ≥112-bit, reject.
- **Legacy flags** → Accept if you need backward compatibility with older implementations.

---

## Common Pitfalls

### 1. Ignoring Tag Size
Many AEAD test groups use non-standard tag sizes (e.g., 32-bit, 64-bit). Make sure your test code respects the `tagSize` from the test group, not a hardcoded value.

### 2. Hex Decoding
All binary data in test vectors is hex-encoded. An empty string `""` means zero-length data (not null). Always decode hex, don't skip empty strings.

### 3. BigInt Encoding
Wycheproof uses twos-complement hex for integers. `"00ff"` = 255 (not -1). The leading zero is significant. Use the correct BigInt parser for your language.

### 4. Mixed Key Formats
Test groups often provide keys in multiple formats (DER, PEM, JWK, raw). Use whichever your API accepts, but don't mix them within a test.

### 5. Non-Standard IV/Nonce Sizes
GCM vectors include non-96-bit IVs. If your library only supports 96-bit (12-byte) nonces, skip those groups rather than failing.

### 6. Test Vector Versioning
The `generatorVersion` field tracks the vector format version (currently 0.9). If you pin to a specific commit, update periodically to get new attack vectors.

### 7. Acceptable vs Invalid
Don't treat `"acceptable"` as `"valid"`. Many developers accidentally assert that acceptable vectors must pass, causing false failures when their library correctly rejects legacy formats.
