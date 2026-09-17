# Prompt Construction Guide

A recipe for writing system prompts and project prompts that produce high-quality AI output. Use this guide alongside the concerns checklist below to draft, audit, and iterate on prompts.

## Core Principle

A system prompt is a behavioral contract. Every line should change what the model does. If removing a line wouldn't change the output, cut it. Prompts are code, not essays.

## Structure

A good system prompt has three layers, in order of priority:

1. **Identity and goal** (1-2 sentences). What is the model's role and what outcome should it optimize for? This anchors everything else. Example: "You are a rigorous intellectual partner. Your job is to make me smarter, not to validate me."

2. **Behavioral directives**. How should the model communicate, reason, and act? These are the rules. Write them as concrete instructions, not abstract values. "State confidence explicitly" beats "be honest about uncertainty."

3. **Constraints and style**. What to avoid, what patterns to use, formatting preferences. These are guardrails. Banned phrases, writing tics to avoid, output format requirements.

Project prompts add a fourth layer:

4. **Domain context**. What the model needs to know about this specific project, codebase, or domain that it can't infer. Keep this factual and current; don't duplicate what's in the code itself.

## Writing Effective Directives

### Be Behavioral, Not Aspirational

Bad: "Be rigorous and thoughtful in your analysis."
Good: "Ground claims in benchmarks, data, or prior art. If you're inferring, say so."

The first is a vibe. The second changes output.

### Be Specific About Failure Modes

Don't just say what you want. Name the failure you're preventing.

Bad: "Give good answers."
Good: "Go deep on the crux rather than surveying five things shallowly."

The second works because it names the specific bad behavior (shallow surveys) and redirects to the desired behavior (depth on what matters).

### Use Examples Sparingly But Precisely

An example in a prompt is worth 10 lines of description, but only if it's the *right* example. Use examples for behaviors that are hard to describe abstractly:

- Tone calibration (what "direct but not rude" sounds like)
- Output format (show the structure you want)
- Edge cases (what to do when two rules conflict)

Don't use examples for simple directives. "Never open with praise" doesn't need an example.

### Use Negative Constraints Sparingly

A specific negative constraint can correct a recurring failure, but a long banned-words list makes prose unnatural and diverts attention from the task. Prefer the desired outcome ("write direct, natural prose") and add a narrow ban only after observing a persistent problem such as performative praise or canned transitions.

### Order Matters

Models weight earlier content more heavily. Put your most important directives first. Identity and goal up top, style constraints at the bottom.

### Token Budget

Shorter prompts leave more context for the actual conversation. Every token in your system prompt is a token not available for the model's reasoning about your question.

Rules of thumb:
- Account-wide web-chat instructions: fit within the tightest provider limit and aim for well under 1500 characters
- System prompt (general, all conversations): aim for under 1000 words
- Project prompt (specific context): add only what's not inferable from the project itself
- If a section doesn't change behavior, cut it
- If two directives say the same thing differently, merge them

## Concerns Checklist

Use this list when drafting or auditing a prompt. Each concern is a failure mode to prevent. You don't need to address every one; pick the ones relevant to your use case.

### Reasoning Quality

- [ ] **Depth over breadth.** Does the prompt prevent shallow survey answers?
- [ ] **Evidence grounding.** Does it require claims to be backed by specifics, not vibes?
- [ ] **Counterargument awareness.** Does it surface credible disagreement when it could change the answer?
- [ ] **Epistemic honesty.** Does it require distinguishing confidence levels and knowledge sources?
- [ ] **Research rigor.** Does it push for correctness over speed on research questions?
- [ ] **Prior art awareness.** Does it ask the model to cite known solutions rather than reinventing?
- [ ] **Failure mode analysis.** Does it require stress-testing ideas, not just validating them?

### Communication Quality

- [ ] **Anti-sycophancy.** Does it ban performative praise and enthusiasm?
- [ ] **Directness.** Does it instruct leading with the important thing, not burying it?
- [ ] **Efficiency.** Does it prevent restating the user's question or padding with filler?
- [ ] **Disagreement protocol.** Does it make clear that disagreement is expected and valued?
- [ ] **Confidence calibration.** Does it distinguish fact, inference, and uncertainty when material?
- [ ] **Brevity permission.** Does it allow short answers to be short?

### Writing Quality

- [ ] **AI-ism avoidance.** Does it discourage filler and canned phrasing without creating an awkward vocabulary blacklist?
- [ ] **Human voice.** Does it instruct writing like a competent human, not a language model?
- [ ] **Format appropriateness.** Does it prevent over-structuring (bullets when prose works)?

### User Development

- [ ] **Teaching when useful.** Does it explain the mental model for complex questions without turning direct answers into lectures?
- [ ] **Clarification discipline.** Does it ask questions only when missing context would materially change the answer?
- [ ] **Long-term optimization.** Does it prefer recommendations that compound over time?
- [ ] **Anti-learned-helplessness.** Does it avoid creating dependency on the model?

### Proactive Behavior

- [ ] **Unsolicited risk identification.** Does it instruct raising risks the user didn't ask about?
- [ ] **Alternative generation.** Does it propose a different path when one is meaningfully better or exposes a real tradeoff?
- [ ] **Assumption surfacing.** Does it require stating assumptions rather than burying them?

### Domain Specificity (for Project Prompts)

- [ ] **Named frameworks.** Does it reference specific methodologies relevant to the domain?
- [ ] **Expert reasoning patterns.** Does it describe how domain experts think, not just what they know?
- [ ] **Domain-specific failure modes.** Does it name the common mistakes in this field?
- [ ] **Evidence standards.** Does it set the right bar for the domain (e.g., RCTs for health claims, benchmarks for performance claims)?

## Iteration Process

1. **Draft** using the structure above and the concerns checklist.
2. **Test** with 5-10 representative questions across your use cases.
3. **Identify failures.** Where did the model ignore your directives? Where did it follow them but produce bad output anyway?
4. **Diagnose.** Was the directive too vague? Missing entirely? Contradicted by another directive? Drowned out by too much other text?
5. **Revise.** Tighten, cut, or restructure. Then test again.

Common iteration patterns:
- "The model keeps doing X" -> Name the desired behavior first; add a narrow ban only if the failure persists
- "The model is too cautious/hedgy" -> Add "if you have a view, state it with reasoning"
- "Answers are too long" -> Add brevity permission AND check that your prompt itself isn't encouraging length through excessive detail
- "The model agrees with everything" -> Strengthen the disagreement protocol with structure (not just "push back when you disagree" but HOW to structure disagreement)

## Reference Material

- `prompts/references/expert-panel.md`: Named experts with documented thinking frameworks, organized by domain. Use when drafting domain-specific project prompts that benefit from named reasoning styles.
- `prompts/system-prompt-advisor.md`: The canonical account-wide instructions for Gemini, Claude, and ChatGPT. Keep them compact and provider-neutral.
- `agents/shared/rules.md`: The deployed cross-vendor communication rules. Keep intentional overlap with the advisor prompt explicit rather than copying whole sections mechanically.
