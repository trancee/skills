package example;

import java.util.Arrays;
import java.util.Base64;

/** Raw parser probe: reject documented invalid input; preserve decoded bytes. */
public final class Base64Target {
  public static void fuzzerTestOneInput(byte[] input) {
    byte[] decoded;
    try {
      decoded = Base64.getDecoder().decode(input);
    } catch (IllegalArgumentException expectedInvalidBase64) {
      return;
    }
    byte[] canonical = Base64.getEncoder().encode(decoded);
    if (!Arrays.equals(decoded, Base64.getDecoder().decode(canonical))) {
      throw new AssertionError("Base64 canonical round trip changed decoded bytes");
    }
  }
}
