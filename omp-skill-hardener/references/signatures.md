# Friction signatures

Gate: same failure >=3 events AND >=2 sessions. Detector=lead only; read source.

| signature | detector | confirm | false positive |
|---|---|---|---|
| `user_frustration` | corrective phrase/all-caps human | agent behavior corrected | quote/external frustration |
| `user_interrupt` | assistant `stopReason:aborted` | unhelpful/unsafe path stopped | network/intentional stop |
| `repeated_tool_error` | same tool errors #3/#5/#8 before success | unchanged approach/prereq | unrelated invocations |
| `plan_reversal` | reversal <=2 human turns post-plan | approved plan diverged | requirement changed |
| `hook_block` | error says hook/deny/block/approval | policy should be anticipated/handled | correct policy |
| `repeated_edit` | same path edit #3/#5/#8/session | fragmented root-cause miss | legitimate staged migration |
| `claimed_done_no_verify` | done phrase after human turn; no verifier | changed behavior required proof | writing/research/unknown verifier/quote |

Rank key=`(signature,target)`; score orders review only, not confidence.

## Rule test

Only controllable recurring decision:
`WHEN <condition>: MUST <replacement>; NEVER <failure> [because <risk>]`
Place at decision point; delete direct contradiction.

REJECT rule if session-specific, incidental names/paths, generic advice, duplicate stronger rule, symptom suppression, or unstated durable preference.

Post-fix: count events after exact `fixedAt`; 1=>inspect; >=2 independent=>review, never auto-edit.
