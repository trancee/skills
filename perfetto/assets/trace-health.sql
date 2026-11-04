-- Nanoseconds in the trace clock, not Unix time.
SELECT start_ts, end_ts, (end_ts - start_ts) / 1e6 AS trace_duration_ms
FROM trace_bounds;

-- Missing sources and valid zero activity are different: inspect the config too.
SELECT 'slice' AS signal, COUNT(*) AS rows FROM slice
UNION ALL SELECT 'sched', COUNT(*) FROM sched
UNION ALL SELECT 'thread_state', COUNT(*) FROM thread_state
UNION ALL SELECT 'counter', COUNT(*) FROM counter
UNION ALL SELECT 'perf_sample', COUNT(*) FROM perf_sample
UNION ALL SELECT 'heap_profile_allocation', COUNT(*) FROM heap_profile_allocation
UNION ALL SELECT 'heap_graph_object', COUNT(*) FROM heap_graph_object;

-- Ring overwrite/discard may be marked info, so severity alone is insufficient.
SELECT name, idx, severity, source, value
FROM stats
WHERE value != 0 AND (
  severity IN ('error', 'data_loss') OR
  name GLOB '*overrun*' OR
  name GLOB '*chunks_overwritten*' OR
  name GLOB '*chunks_discarded*'
)
ORDER BY severity, name, idx
LIMIT 50;
