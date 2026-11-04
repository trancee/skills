-- Change roi to the required [start_ns, end_ns) in this trace's clock.
-- Exclude incomplete sched rows (dur < 0); this can undercount the final run.
WITH roi AS (SELECT start_ts, end_ts FROM trace_bounds),
clipped AS (
  SELECT s.utid,
    MIN(s.ts + s.dur, roi.end_ts) - MAX(s.ts, roi.start_ts) AS dur
  FROM sched AS s CROSS JOIN roi
  WHERE roi.start_ts < roi.end_ts
    AND s.dur > 0 AND s.ts < roi.end_ts AND s.ts + s.dur > roi.start_ts
)
SELECT t.utid, t.upid, t.tid, p.pid, t.name AS thread_name,
  p.name AS process_name, SUM(c.dur) / 1e6 AS cpu_ms
FROM clipped AS c
JOIN thread AS t ON t.utid = c.utid
LEFT JOIN process AS p ON p.upid = t.upid
WHERE NOT t.is_idle
GROUP BY t.utid, t.upid, t.tid, p.pid, t.name, p.name
ORDER BY cpu_ms DESC, t.utid
LIMIT 20;
