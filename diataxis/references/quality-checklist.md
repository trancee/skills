# Diátaxis quality assessment

Current source: [Towards a theory of quality in documentation](https://diataxis.fr/quality/).

Assess quality in two layers. Diátaxis helps reveal functional problems and create conditions for deep quality; it does not replace technical verification, user research, information design, or editorial judgement.

## Functional quality

Functional qualities are independent, objective constraints measured against the product and the user's real work.

- [ ] **Accuracy:** facts, commands, APIs, outputs, and examples match the current product.
- [ ] **Completeness:** the document covers everything required by its declared scope.
- [ ] **Consistency:** terminology, structure, examples, and cross-references agree.
- [ ] **Usefulness:** the content serves an actual user need rather than merely describing available material.
- [ ] **Precision:** claims, prerequisites, conditions, and outcomes are unambiguous.
- [ ] Executable journeys have been run end-to-end in the documented environment.
- [ ] Reference coverage has been checked against the machinery it describes.

A document can satisfy one functional quality and fail another. Verify each independently. Functional quality is a prerequisite for deep quality.

## Deep quality

Deep qualities are interdependent and assessed through judgement against human experience.

- [ ] The document fits the user's need at that moment.
- [ ] It has flow: the user's action or thought progresses without avoidable interruption.
- [ ] It anticipates the user's next concern, tool, decision, or uncertainty.
- [ ] It feels coherent and good to use.
- [ ] Its form, language, and navigation reinforce its purpose.

Diátaxis can help create these conditions but cannot guarantee beauty, flow, or excellent user experience.

## Form and boundary checks

- [ ] The dominant user need is clear: learning, a goal, information, or understanding.
- [ ] The compass confirms the form: action/cognition and acquisition/application.
- [ ] The title signals the document's purpose accurately.
- [ ] Supporting material from another form is brief and does not disrupt the dominant purpose.
- [ ] Sustained material serving another need has its own appropriate home and an intentional cross-link.
- [ ] Navigation and placement make the page predictable to find; literal four-part top-level directories are not required.
- [ ] The documentation structure has grown from real content needs rather than empty Diátaxis scaffolding.

## Tutorial checklist

- [ ] It is a practical, hands-on learning experience rather than a task guide.
- [ ] The tutor takes responsibility for the learner's safety and success.
- [ ] The setting and path are controlled, concrete, and repeatable.
- [ ] It shows the destination at the start without claiming what the user will learn.
- [ ] Every step produces a visible, meaningful result.
- [ ] It maintains a narrative of expected outcomes and points out what to notice.
- [ ] It permits useful repetition.
- [ ] Explanation, information, abstraction, choices, and alternatives are minimised.
- [ ] It has been observed or tested end-to-end with representative learners/environments.

## How-to guide checklist

- [ ] It addresses a specific real-world goal or problem from the user's perspective.
- [ ] It assumes the user is already competent and familiar with the tools.
- [ ] It provides executable actions and the judgement needed to apply them.
- [ ] Its sequence has logical flow and avoids unnecessary context switching.
- [ ] It prepares for realistic branches, alternatives, risks, and recovery paths.
- [ ] It starts and ends at meaningful points rather than forcing an end-to-end lesson.
- [ ] It prefers practical usability to completeness and links to reference for options.
- [ ] The title states exactly what the guide helps achieve.

## Reference checklist

- [ ] It describes the product or machinery succinctly and neutrally.
- [ ] It is accurate, complete, precise, consistent, and authoritative within scope.
- [ ] Its structure mirrors the logical structure of the thing described where useful.
- [ ] Similar APIs, commands, or configuration items use the same pattern.
- [ ] Facts, parameters, defaults, constraints, return values, errors, and warnings are documented.
- [ ] Examples illustrate usage without becoming lessons or goal-oriented procedures.
- [ ] Motivation, opinion, and extended interpretation link to explanation.

## Explanation checklist

- [ ] It illuminates a bounded topic and supports reflection.
- [ ] It provides context, reasons, history, implications, and connections.
- [ ] It considers useful perspectives, alternatives, opinions, and counter-examples.
- [ ] Its viewpoint is higher and wider than an immediate task or close machinery description.
- [ ] The title works with an implicit “About …” or “Why …”.
- [ ] It forms or strengthens a coherent mental model.
- [ ] Step-by-step procedures and detailed technical listings live elsewhere.

## Boundary diagnosis

| Symptom | Conflict | Improvement |
| --- | --- | --- |
| Tutorial pauses for paragraphs of background | Explanation interrupts the learning experience | Keep immediate context; link to explanation |
| How-to guide starts by teaching the domain | Study interrupts real work | Link to a tutorial; retain task guidance |
| Reference discusses motives and trade-offs | Explanation obscures authoritative facts | Move discussion to explanation |
| Explanation contains a sequence to execute | How-to content interrupts reflection | Move the procedure to a how-to guide |
| A page repeatedly changes audience or purpose | Multiple needs compete and break flow | Split coherent sections and cross-link |

## Completion

A quality review is complete when every functional claim has evidence, the dominant user need and form are explicit, boundary problems have concrete moves or edits, and deep quality has been judged against the intended user's experience—not inferred from correct classification alone.
