/* Disposable integration probe; fixed keys/nonces are test vectors only. */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <openssl/aead.h>
#include <openssl/crypto.h>
#include <openssl/err.h>
#include <openssl/evp.h>
#include <openssl/service_indicator.h>

#ifndef OPENSSL_IS_AWSLC
#error "Compile with the selected AWS-LC headers, not system OpenSSL"
#endif

int main(int argc, char **argv) {
  if (argc != 2 || (strcmp(argv[1], "0") && strcmp(argv[1], "1"))) {
    fprintf(stderr, "Usage: %s EXPECT_FIPS_MODE (0 or 1)\n", argv[0]);
    return 2;
  }
  const int expect_fips = argv[1][0] == '1';
  if (strncmp(awslc_version_string(), "AWS-LC ", 7) != 0 ||
      FIPS_mode() != expect_fips) {
    fprintf(stderr, "Wrong linked library or mode: %s; FIPS_mode=%d\n",
            awslc_version_string(), FIPS_mode());
    return 1;
  }
  static const uint8_t sha256_abc[32] = {
    0xba,0x78,0x16,0xbf,0x8f,0x01,0xcf,0xea,0x41,0x41,0x40,0xde,0x5d,0xae,0x22,0x23,
    0xb0,0x03,0x61,0xa3,0x96,0x17,0x7a,0x9c,0xb4,0x10,0xff,0x61,0xf2,0x00,0x15,0xad
  };
  uint8_t digest[EVP_MAX_MD_SIZE];
  unsigned digest_len = 0;
  const uint64_t before = FIPS_service_indicator_before_call();
  const int digest_ok = EVP_Digest("abc", 3, digest, &digest_len, EVP_sha256(), NULL);
  const uint64_t after = FIPS_service_indicator_after_call();
  if (!digest_ok || digest_len != sizeof(sha256_abc) ||
      memcmp(digest, sha256_abc, sizeof(sha256_abc)) ||
      (expect_fips && before == after)) {
    fprintf(stderr, "SHA-256 vector or FIPS service indicator failed\n");
    ERR_print_errors_fp(stderr);
    return 1;
  }
  static const uint8_t gcm_expected[32] = {
    0x03,0x88,0xda,0xce,0x60,0xb6,0xa3,0x92,0xf3,0x28,0xc2,0xb9,0x71,0xb2,0xfe,0x78,
    0xab,0x6e,0x47,0xd4,0x2c,0xec,0x13,0xbd,0xf5,0x3a,0x67,0xb2,0x12,0x57,0xbd,0xdf
  };
  const uint8_t key[16] = {0}, nonce[12] = {0}, plaintext[16] = {0};
  uint8_t ciphertext[32], opened[16];
  size_t ciphertext_len = 0, opened_len = 0;
  EVP_AEAD_CTX ctx;
  EVP_AEAD_CTX_zero(&ctx);
  int result = 1;
  if (!EVP_AEAD_CTX_init(&ctx, EVP_aead_aes_128_gcm(), key, sizeof(key),
                         EVP_AEAD_DEFAULT_TAG_LENGTH, NULL) ||
      !EVP_AEAD_CTX_seal(&ctx, ciphertext, &ciphertext_len, sizeof(ciphertext),
                         nonce, sizeof(nonce), plaintext, sizeof(plaintext), NULL, 0) ||
      ciphertext_len != sizeof(gcm_expected) ||
      memcmp(ciphertext, gcm_expected, sizeof(gcm_expected)) ||
      !EVP_AEAD_CTX_open(&ctx, opened, &opened_len, sizeof(opened),
                         nonce, sizeof(nonce), ciphertext, ciphertext_len, NULL, 0) ||
      opened_len != sizeof(plaintext) || memcmp(opened, plaintext, sizeof(plaintext))) {
    fprintf(stderr, "AES-128-GCM vector or authenticated decrypt failed\n");
    goto done;
  }
  ciphertext[sizeof(ciphertext) - 1] ^= 1;
  if (EVP_AEAD_CTX_open(&ctx, opened, &opened_len, sizeof(opened),
                        nonce, sizeof(nonce), ciphertext, ciphertext_len, NULL, 0)) {
    fprintf(stderr, "AES-128-GCM accepted a modified tag\n");
    goto done;
  }
  ERR_clear_error();
  printf("PASS: %s; FIPS_mode=%d; SHA-256 vector; AES-GCM vector/decrypt/tamper rejection; SHA approval=%s\n",
         awslc_version_string(), FIPS_mode(), expect_fips ? "approved" : "not applicable");
  result = 0;
done:
  if (result) ERR_print_errors_fp(stderr);
  EVP_AEAD_CTX_cleanup(&ctx);
  return result;
}
