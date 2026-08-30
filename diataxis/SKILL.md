---
name: diataxis
description: "Authors, audits, and restructures technical documentation with the Diátaxis framework. Use when creating or reviewing tutorials, how-to guides, reference, explanation, documentation architecture, content classification, or documentation quality. Don't use for general prose editing without a documentation need, API implementation, or product design."
metadata:
  category: "documentation"
  source: "https://diataxis.fr/"
  sourceVersion: "evildmp/diataxis-documentation-framework@957c09ca40b4a1edc23874f713e01937d50d54d5"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-28T19:26:56+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T11:16:59+02:00"
---

# Diátaxis documentation workflow

## Procedures

**Step 1: Establish the documentation task**

1. Identify whether the request creates documentation, audits existing documentation, or restructures a documentation set.
2. Identify the documented product or craft, intended practitioner, competence level, immediate situation, and desired outcome.
3. Bound the work to named pages, a directory, or a specific user journey. If the boundary is absent, derive it from the repository's documentation structure and the request.
4. Inspect the current product, commands, APIs, configuration, examples, and documentation conventions before writing. Treat product behavior as the source of truth for functional claims.

**Step 2: Classify the user need with the compass**

1. Ask whether the content informs **action** or **cognition**.
2. Ask whether the practitioner is **acquiring** skill through study or **applying** skill at work.
3. Select the form at the intersection:

   | Content | Practitioner context | Form |
   | --- | --- | --- |
   | Action | Acquisition/study | Tutorial |
   | Action | Application/work | How-to guide |
   | Cognition | Application/work | Reference |
   | Cognition | Acquisition/study | Explanation |

4. Apply the compass at the scale of a sentence, section, page, user situation, or missing documentation need.
5. Classify by the need served, not by title, difficulty, product feature, document length, or whether steps appear. A basic procedure can be a how-to guide; an advanced learning experience can be a tutorial.
6. If several needs compete, identify one dominant need for each coherent page or section. Permit brief supporting material only when it preserves the dominant purpose and flow.

**Step 3: Load the form-specific rules**

1. If the selected form is a tutorial, read `references/tutorials.md`.
2. If the selected form is a how-to guide, read `references/how-to-guides.md`.
3. If the selected form is reference, read `references/reference.md`.
4. If the selected form is explanation, read `references/explanation.md`.
5. If the request spans several forms, read only the corresponding references, assign each output a distinct need, and define cross-links between them.

**Step 4: Choose the branch**

1. If creating documentation, define the smallest complete document that serves the selected need, then continue to Step 5.
2. If revising a document, identify the smallest add, remove, move, split, merge, rename, or rewrite that improves the selected need, then continue to Step 5.
3. If auditing documentation, copy the structure from `assets/audit-report.md`, fill it with evidence-backed findings, and continue to Step 5.
4. If restructuring a documentation set, avoid imposing four empty top-level sections. Improve real pages first and let navigation and architecture emerge from demonstrated content needs.

**Step 5: Create or revise the content**

1. For a tutorial, construct a safe, concrete, repeatable learning experience with one managed path, visible results, expected outcomes, observations, and minimal explanation or choice.
2. For a how-to guide, address a specific real-world goal from the competent practitioner's perspective. Provide an executable sequence with necessary judgement, branches, risks, and recovery paths; prefer usability to completeness.
3. For reference, describe the machinery succinctly and neutrally. Mirror its logical structure, use consistent patterns, and cover facts, parameters, defaults, constraints, errors, warnings, and illustrative examples.
4. For explanation, illuminate one bounded topic through context, reasons, history, implications, connections, perspectives, alternatives, and reflection.
5. Move sustained material serving another need into its appropriate form and add an intentional cross-link. Avoid mechanical splitting when a short supporting sentence preserves flow.
6. Match the repository's established terminology, heading style, navigation, code-block conventions, and link style.

**Step 6: Improve architecture from the inside out**

1. Organize documentation around practitioner needs rather than product features alone.
2. Keep each page's purpose predictable from its title, introduction, placement, and form.
3. Keep neighbouring forms reachable through purposeful links without duplicating their content.
4. Let reference mirror the product's logical structure where that helps practitioners consult it during work.
5. Create new sections or navigation categories only after real content demands them. Use labels that fit the product; literal `tutorials/`, `how-to/`, `reference/`, and `explanation/` directories are optional.
6. Complete and publish each useful improvement before expanding the restructuring scope. Keep documentation complete at its current stage even though it remains open to future improvement.

**Step 7: Assess quality**

1. Read `references/quality-checklist.md` and evaluate every applicable item.
2. Verify functional quality independently: accuracy, completeness within scope, consistency, usefulness, and precision.
3. Exercise tutorial and how-to journeys in the documented environment. Compare reference coverage with the current machinery. Ground explanation in accurate product and domain facts.
4. Judge deep quality against the practitioner's experience: fit to need, flow, anticipation, coherence, and ease of use.
5. Treat functional quality as a prerequisite for deep quality. Do not infer correctness from successful Diátaxis classification.
6. For audits, rank findings by user impact and provide concrete changes rather than labels alone.

**Step 8: Validate and deliver**

1. Run the repository's documentation formatter, linter, or build when available.
2. Check local Markdown links with:

   ```bash
   python3 scripts/check-links.py path/to/docs
   ```

3. Inspect external links required by the changed user journey with the available URL-reading tool; the bundled checker intentionally skips network validation.
4. Re-run every executable example or scenario affected by the change and record exact evidence.
5. Confirm that titles, navigation, and cross-links expose the intended need without requiring knowledge of Diátaxis terminology.
6. Deliver created or revised documentation, or an audit following `assets/audit-report.md`, with verification evidence and any unresolved factual limitation.

## Error Handling

- If the compass result remains ambiguous, state the practitioner's immediate situation and choose the form that best serves that moment. Split only when distinct sustained needs compete.
- If product facts cannot be verified, mark the affected claim as unresolved and complete all other reachable documentation work. Do not convert assumptions into reference claims.
- If a tutorial cannot be exercised reliably, fix the environment and expected-result gaps before calling it complete.
- If a how-to guide branches uncontrollably, narrow its goal or split distinct real-world goals into separate guides.
- If reference completeness cannot be bounded, define the machinery and version in scope before assessing it.
- If explanation expands without limit, restate the governing “why” question and remove material that does not illuminate it.
- If `scripts/check-links.py` reports a missing target, correct the relative path or create the intended document. If it reports a missing fragment, update the fragment to the target heading's generated anchor.
- If the checker flags syntax it cannot model, verify the link with the documentation toolchain and document the checker limitation rather than weakening the content.
