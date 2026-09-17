---
name: presentation-design
description: Design decks. Use for slides and pitches.
---

# Presentation Design

Build a presentation as a sequence of claims that helps a specific audience make a decision. Treat slides as visual evidence for a conversation, not containers that need filling.

## Establish the decision

Before editing, identify:

1. Who will see the deck?
2. What decision or next step should the conversation produce?
3. Which objections must the presenter be able to answer?
4. Which slides are the short live route, which are question-driven modules, and which belong only in the appendix?

If these are already clear from the conversation, state the interpretation briefly and proceed.

## Reuse before inventing

Inventory existing decks, approved slides, speaker notes, transcripts, and canonical research before creating a new visual treatment.

- Reuse an approved slide when it already performs the same job.
- Adapt company names or context only when needed; preserve the proven information hierarchy and visual mechanism.
- When replacing a slide for comparison, retain the displaced version in the appendix until the user chooses.
- Mine the presenter's own writing and transcripts for concise language. Distinguish exact quotes from paraphrases and preserve provenance in speaker notes.

Novelty is not a virtue when a prior slide has already survived review.

## Make every slide earn its place

Write the slide's job and single claim before designing it. Cut or merge the slide when its job duplicates another slide.

A strong thesis slide usually contains:

- **The familiar observation:** the common view, stated quickly.
- **The deeper cut:** the presenter's non-obvious mechanism, boundary, or implication.
- **The evidence or consequence:** what the audience should believe, measure, or do differently.

Prefer an insight the presenter can defend over a taxonomy they could find in a generic report. Avoid lecturer language when the presenter should sound like an operator sharing what they learned.

## Write titles as a hierarchy

Use the eyebrow for context and the headline for the claim.

- The eyebrow and headline must add different information.
- Use a structural label plus an insight, not two paraphrases of the same title.
- Keep headlines to one or two deliberate lines at the presentation viewport.
- Avoid a one-word final line, accidental widows, and oversized type constrained to a narrow measure.
- Put recipient-specific questions and narration in speaker notes, not in the slide artwork.

Read the pair aloud. If both lines answer the same question, rewrite one or remove it.

## Match visual form to claim

Choose the simplest form that makes the mechanism visible:

- Timeline for sequence or development
- System diagram for transformation or architecture
- Gates for a delivery lifecycle
- Table for comparable rows with shared dimensions
- Split boundary for ownership or contrast
- Funnel or path for conversion
- Compounding path for reusable assets and later leverage
- Full-bleed stopper for the end of the main deck

Do not repeat a three-card grid because it is convenient. Adjacent slides should not use the same composition unless the repetition itself communicates a deliberate comparison.

Use whitespace to establish hierarchy, not to conceal thin thinking. A sparse slide is acceptable when one visual or sentence carries the argument; a taxonomy stranded at the top of an empty canvas is unfinished.

## Separate main deck and appendix

End the main argument with a clear close and an unmistakable stopper slide. Put alternatives, detailed evidence, company-specific hypotheses, and displaced treatments after that boundary.

The audience should know when the presentation is over without inspecting the page number.

## Preserve conversational control

Design a short route rather than assuming every slide will be presented.

- Begin conversationally when the meeting is exploratory.
- Use proof slides when credibility is questioned.
- Use opportunity slides only when they answer the live question.
- Keep detailed claims, caveats, and objection answers in a durable run sheet.
- Make the final slide state the proposed decision, evidence gate, or next step.

## Verify the actual artifact

A build passing is not visual verification.

1. Render the deck at the real presentation viewport.
2. Capture every slide or a readable contact sheet.
3. Inspect titles, line composition, density, alignment, and visual repetition.
4. Check all slides for overflow.
5. Reject prominent copy with accidental one-word final lines.
6. Confirm page numbers, navigation, main-deck order, stopper, and appendix order.
7. Run the repository's formatter, tests, type checks, and production build.

Add a deck-specific browser regression when typography or viewport behavior has already caused rework. The regression should test the actual failure seam, such as heading line count or orphaned final lines, rather than merely asserting that the page renders.

## Final review

Before reporting completion, answer:

- What decision does the deck support?
- What does each main slide uniquely contribute?
- Which slides reused approved work?
- Where does the presenter's own insight appear?
- Are adjacent layouts meaningfully different?
- Is any printed copy really speaker narration?
- Can the presenter stop cleanly before the appendix?
- Was every slide inspected at the actual viewport?

If any answer is unclear, the deck is not finished.
