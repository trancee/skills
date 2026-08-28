---
name: diataxis
description: Write, audit, and improve documentation with Diátaxis. Use for tutorials, how-to guides, reference, explanation, documentation architecture, content classification, or documentation quality reviews.
---

# Diátaxis — systematic documentation authoring

Diátaxis is a pragmatic, systematic approach to documentation content, style, architecture, and workflow. It starts from four distinct user needs and the documentation forms that serve them.

Source: [diataxis.fr](https://diataxis.fr/) by Daniele Procida.

## The map

| Type | User need | Informs | Serves | Form |
| --- | --- | --- | --- | --- |
| **Tutorial** | Learning | Action | Acquisition of skill (study) | A guided learning experience |
| **How-to guide** | A goal or problem | Action | Application of skill (work) | Goal-oriented directions |
| **Reference** | Information | Cognition | Application of skill (work) | Technical description |
| **Explanation** | Understanding | Cognition | Acquisition of skill (study) | Discursive reflection |

The map is two-dimensional, not merely a list of content labels:

- **action ↔ cognition** distinguishes practical knowledge from propositional or theoretical knowledge;
- **acquisition ↔ application** distinguishes study from work.

The four forms are defined by user needs, not by subject matter, difficulty, product features, or document length. A basic task can require a how-to guide; an advanced topic can require a tutorial.

## The compass

When the right form is unclear, ask:

1. Does the user need **action** or **cognition**?
2. Are they **acquiring** skill through study or **applying** skill at work?

| Content… | Serving… | Belongs to… |
| --- | --- | --- |
| informs action | acquisition of skill | **tutorial** |
| informs action | application of skill | **how-to guide** |
| informs cognition | application of skill | **reference** |
| informs cognition | acquisition of skill | **explanation** |

Apply the compass at the scale of a sentence, section, whole page, user situation, or missing documentation need. Use the terms flexibly enough to expose the dominant need; do not classify from the title alone.

## Work incrementally

Use Diátaxis as a guide, not a top-down plan:

1. **Choose** a small piece of documentation already in front of you.
2. **Assess** it: What user need does it represent? How well does it serve that need? What language, content, or placement interferes?
3. **Decide** the single next action that will improve it now.
4. **Do** that action and consider the improvement complete.
5. Repeat; let larger structural needs emerge from the improved content.

Do not begin by creating four empty sections or imposing a complete information architecture. Diátaxis changes documentation from the inside out. Documentation can be never finished yet complete and useful at every stage.

For new documentation, the same principle applies: identify the immediate user need, create the smallest complete document that serves it, verify it with the intended user journey, then follow the next need revealed by the work.

## Write for the selected need

Read the detailed reference for the selected form before writing or revising it:

- [Tutorials](references/tutorials.md) — learning-oriented experiences
- [How-to guides](references/how-to-guides.md) — goal-oriented directions
- [Reference](references/reference.md) — information-oriented technical descriptions
- [Explanation](references/explanation.md) — understanding-oriented discussion

### Tutorial

- Create a safe, meaningful, repeatable learning experience.
- Take responsibility for the learner's success.
- Keep one carefully managed path with concrete actions and results.
- Show the destination; deliver visible results early and often.
- Maintain a narrative of expected outcomes and point out what to notice.
- Minimise explanation, information, abstraction, choices, and alternatives.

### How-to guide

- Address a specific real-world goal or problem from the user's perspective.
- Assume competence and familiarity; guide work rather than teach.
- Provide an executable logical sequence, including judgement where needed.
- Accommodate real-world branches, alternatives, risks, and multiple entry or exit points.
- Prefer practical usability to completeness; link to reference and explanation.
- Name the exact goal: “How to configure reconnection back-off policies”.

### Reference

- Describe the machinery succinctly, accurately, completely, and neutrally.
- Let the product lead the structure; mirror its logical architecture where useful.
- Use standard, consistent patterns so information is predictable to consult.
- State facts, options, constraints, defaults, errors, and warnings.
- Include examples that illustrate without becoming procedures or lessons.
- Link to tutorials, how-to guides, and explanation rather than absorbing them.

### Explanation

- Illuminate a bounded topic through context, reasons, history, implications, and connections.
- Permit reflection, opinion, perspectives, alternatives, and counter-examples.
- Approach the subject from a higher and wider viewpoint than the user's immediate task.
- Let the title work with an implicit “About …” or “Why …”.
- Keep step-by-step instruction and detailed technical reference in their own forms.

## Handle boundaries without rigidity

A page should have a dominant user need and form. Small supporting elements are legitimate: reference can contain illustrative examples, a tutorial can contain the minimum explanation needed to keep moving, and a how-to guide can link to options.

Intervene when another form becomes sustained enough to interrupt the page's purpose or flow. Move that material to the appropriate document and link to it. Split by user need, not mechanically at every mixed sentence.

Common boundary failures:

| Symptom | Conflict | Improvement |
| --- | --- | --- |
| Tutorial pauses for extensive background | Explanation interrupts learning action | Keep the minimum context; link to explanation |
| How-to guide teaches foundational skills | Study interrupts the user's work | Link to a tutorial; retain task guidance |
| Reference expands into motivations or opinion | Explanation obscures facts | Move the discussion to explanation |
| Explanation contains an executable procedure | Work instructions interrupt reflection | Move the procedure to a how-to guide |
| One page repeatedly changes audience and purpose | Several needs compete | Split coherent sections and cross-link them |

## Let architecture emerge

Diátaxis strongly guides architecture, but does not require literal top-level directories named `tutorials`, `how-to`, `reference`, and `explanation`. Use labels and navigation that make sense to users and the product.

As the body grows:

- organise around user needs rather than product features alone;
- make each page's purpose and expected form predictable;
- keep neighbouring forms easy to reach through intentional links;
- let reference mirror product structure;
- expose gaps after real content reveals them;
- avoid empty scaffolding created merely to complete the four-part map.

## Assess quality

Use the [quality checklist](references/quality-checklist.md), keeping two kinds of quality distinct:

- **Functional quality**: accuracy, completeness, consistency, usefulness, and precision. These are independent, objective constraints measured against the product and real user tasks. Diátaxis can expose failures here but cannot supply technical correctness.
- **Deep quality**: fitting human needs, flow, anticipation, beauty, and feeling good to use. These qualities are interdependent and require judgement. Diátaxis creates conditions for them but does not guarantee them.

Functional quality is a prerequisite for deep quality. Verify facts and executable journeys first; then judge whether the documentation fits and moves with the user.

## Official references

- [Start here](https://diataxis.fr/start-here/)
- [The four forms and practical guidance](https://diataxis.fr/application/)
- [The compass](https://diataxis.fr/compass/)
- [Workflow](https://diataxis.fr/how-to-use-diataxis/)
- [The map](https://diataxis.fr/map/)
- [Quality](https://diataxis.fr/quality/)
