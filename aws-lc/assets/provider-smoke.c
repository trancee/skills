/* Compile only against OpenSSL 3.5+; load AWS-LC through its provider module. */
#include <stdio.h>
#include <string.h>
#include <openssl/evp.h>
#include <openssl/err.h>
#include <openssl/provider.h>

int main(int argc, char **argv) {
  if (argc != 2) {
    fprintf(stderr, "Usage: %s PROVIDER_MODULE_DIRECTORY\n", argv[0]);
    return 2;
  }
  OSSL_LIB_CTX *ctx = OSSL_LIB_CTX_new();
  OSSL_PROVIDER *provider = NULL;
  EVP_MD *md = NULL;
  int result = 1;
  if (!ctx || !OSSL_PROVIDER_set_default_search_path(ctx, argv[1]) ||
      !(provider = OSSL_PROVIDER_load(ctx, "awslc")) ||
      !(md = EVP_MD_fetch(ctx, "SHA2-256", "provider=awslc"))) goto done;
  const char *name = OSSL_PROVIDER_get0_name(EVP_MD_get0_provider(md));
  const unsigned char expected[32] = {
    0xba,0x78,0x16,0xbf,0x8f,0x01,0xcf,0xea,0x41,0x41,0x40,0xde,0x5d,0xae,0x22,0x23,
    0xb0,0x03,0x61,0xa3,0x96,0x17,0x7a,0x9c,0xb4,0x10,0xff,0x61,0xf2,0x00,0x15,0xad
  };
  unsigned char digest[EVP_MAX_MD_SIZE];
  unsigned digest_len = 0;
  if (!name || strcmp(name, "awslc") ||
      !EVP_Digest("abc", 3, digest, &digest_len, md, NULL) ||
      digest_len != sizeof(expected) || memcmp(digest, expected, sizeof(expected))) goto done;
  printf("PASS: provider=%s; SHA2-256(abc) matches known vector\n", name);
  result = 0;
done:
  if (result) {
    fprintf(stderr, "Provider load, identity, or digest failed\n");
    ERR_print_errors_fp(stderr);
  }
  EVP_MD_free(md);
  OSSL_PROVIDER_unload(provider);
  OSSL_LIB_CTX_free(ctx);
  return result;
}
