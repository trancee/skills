# Friction signatures

Every signature is triage evidence. Accept a hardening candidate only after reading the source context and finding the same failure mode in at least three events across at least two sessions.

| Signature | Detector | Confirm manually | Common false positive |
| --- | --- | --- | --- |
| `user_frustration` | Corrective/frustrated phrases or sustained all-caps in a human message | The user corrects agent behavior governed by the target | Quoted text, emphasis, or frustration with an external system |
| `user_interrupt` | Assistant message ends with `stopReason: aborted` | The user stopped an unhelpful or unsafe direction | Network cancellation, terminal closure, or intentional early stop |
| `repeated_tool_error` | Third, fifth, or eighth consecutive error result from the same tool before a successful result | Retries share an unchanged approach or missed prerequisite | Different invocations of one tool fail for unrelated reasons |
| `plan_reversal` | A reversal phrase within two human turns after leaving plan mode | The implementation diverged from the approved plan | The user deliberately changed requirements |
| `hook_block` | Error result mentions a hook, denial, block, or approval rejection | Agent behavior should have anticipated or handled the policy | Correct policy enforcement with no agent mistake |
| `repeated_edit` | Same path edited for the third, fifth, or eighth time in one session | Fragmented edits came from weak skill guidance | Legitimate staged migration in a large file |
| `claimed_done_no_verify` | Completion phrase after the last human turn without an observed verifier | The claim concerns changed behavior and verification was required | Pure writing/research task, verifier unknown to the miner, or quoted completion text |

## Ranking

The report groups by `(signature, target)`. Its score is a review-order heuristic: signature severity multiplied by independent session count, plus event count. It is not a confidence measure and must not override weak attribution.

## Turning evidence into a rule

Write a rule only when a controllable decision caused the recurrence. Prefer this shape:

> When `<observable condition>`, MUST `<replacement behavior>`; NEVER `<failed branch>` because `<specific risk>`.

Omit the reason when the risk is already obvious in surrounding text. Place the rule immediately before the decision it governs. Delete a directly contradicted obsolete rule rather than adding a later exception.

Reject proposed rules that:

- describe the single transcript instead of the general decision;
- name incidental file paths, people, sessions, or tools;
- say only “be careful,” “verify,” or “follow instructions”;
- duplicate an active system or repository rule;
- suppress an error instead of fixing the behavioral cause;
- encode a user preference that was never stated as durable.

## Recurrence after a fix

The ledger records a precise `fixedAt` timestamp. The report counts later matching events for the same signature and target. Inspect one recurrence for an attribution or coverage mistake. Two independent recurrences justify a new review but do not authorize automatic edits.
