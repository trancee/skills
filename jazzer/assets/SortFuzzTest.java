package example;

import com.code_intelligence.jazzer.junit.FuzzTest;
import com.code_intelligence.jazzer.mutation.annotation.NotNull;
import com.code_intelligence.jazzer.mutation.annotation.WithSize;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Collections;
import org.junit.jupiter.params.provider.MethodSource;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class SortFuzzTest {
  static List<List<Integer>> seeds() {
    return List.of(List.of(), List.of(3, -1, 3, 0), List.of(Integer.MIN_VALUE, Integer.MAX_VALUE));
  }

  @MethodSource("seeds")
  @FuzzTest(maxDuration = "10s", maxExecutions = 10000)
  void sortPreservesValues(@NotNull @WithSize(max = 64) List<@NotNull Integer> input) {
    List<Integer> sorted = new ArrayList<>(input);
    Collections.sort(sorted);
    for (int i = 1; i < sorted.size(); i++) {
      assertTrue(sorted.get(i - 1) <= sorted.get(i), "sort order");
    }
    Map<Integer, Integer> before = new HashMap<>();
    Map<Integer, Integer> after = new HashMap<>();
    input.forEach(value -> before.merge(value, 1, Integer::sum));
    sorted.forEach(value -> after.merge(value, 1, Integer::sum));
    assertEquals(before, after, "sort must preserve each value's multiplicity");
  }
}
