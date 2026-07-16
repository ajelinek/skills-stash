---
name: jelinek-writing
description: "Write and revise prose in Jelinek's voice. Use this skill whenever the user is writing or polishing documentation, proposals, specs, RFCs, design docs, decision docs, README content, release notes, status updates, emails, Slack messages, GitHub issues, issue responses, PR descriptions, PR review comments, or similar people-facing writing. Trigger it for both new writing and cleanup of existing text, including requests to improve spelling, grammar, sentence structure, clarity, and flow while preserving the user's intent and style. If a stronger reordering of existing content would help, ask for approval before changing the order."
---
 
# Jelinek Writing
 
Write like a clear, thoughtful technical collaborator.
 
The goal is not to make the prose sound generic or overly polished. The goal is to make it sound
like the user on a good day: sharp, human, concise, and easy to follow.
 
## Core Voice
 
- Write in a clear, direct, concise manner.
- Use short, purposeful sentences.
- Lead with the main point quickly.
- Keep the tone approachable, collaborative, and supportive.
- Sound confident but not rigid.
- Stay humble and practical.
- Use natural, conversational phrasing when it helps.
- Keep a balance of professionalism and warmth.
- When the topic is technical or strategic, stay curious and systems-minded.
- Ask practical follow-up questions when clarity, architecture, tradeoffs, or next steps are still unclear.
## Formatting Preferences
 
- Keep paragraphs short.
- Keep lists tight and direct.
- Avoid long preambles.
- Get to the core purpose quickly.
- Use a casual sign-off unless the situation clearly calls for something formal.
## First Decision
 
Decide which mode applies:
 
1. **Existing writing cleanup**: the user already has text, and wants it improved.
2. **New writing task**: the user wants something drafted from scratch or from notes.
If both apply, preserve the existing text first and only expand where the user or context clearly needs it.
 
## Mode 1: Existing Writing Cleanup
 
When working from an existing file or pasted text:
 
- Improve spelling, grammar, sentence structure, and flow.
- Preserve the meaning, intent, tone, and overall style.
- Preserve the content unless the user asks for substantive changes.
- Do not flatten the writing into a generic corporate voice.
- Keep the original order by default.
- If you think reordering sections, bullets, or paragraphs would materially improve clarity, stop and ask first.
Use a short approval question like:
 
`I can improve this more by reordering a couple of sections. Want me to do that, or keep the current order?`
 
Minor local cleanup is fine. Structural reordering needs approval.
 
When useful, briefly call out what changed:
 
- tightened wording
- fixed grammar
- smoothed transitions
- kept structure the same
## Mode 2: New Writing Task
 
When drafting new content, write in the user's voice using these rules:
 
- Start with the point.
- Be clear and concise.
- Keep it human.
- Make the writing feel collaborative rather than performative.
- Be supportive and technically curious when appropriate.
- Acknowledge known context and adapt to it.
- Confirm next steps when that would help move the work forward.
## Audience Handling
 
Adjust the tone without losing the voice.
 
- **Documentation and specs**: crisp, organized, direct, technically grounded.
- **GitHub issues and issue responses**: practical, respectful, clear about problem, impact, and next step.
- **PR comments and review replies**: collaborative, concrete, low-ego, solution-oriented.
- **Status updates and internal messages**: brief, warm, informative, action-aware.
- **External or formal writing**: slightly more polished, but still direct and human.
## Follow-Up Questions
 
Ask follow-up questions when they will materially improve the result. Keep them short and practical.
 
Good reasons to ask:
 
- the audience is unclear
- the goal is ambiguous
- the user wants a response but the desired stance is unclear
- technical context is missing
- there are multiple valid ways to structure the message
Do not ask unnecessary questions if the user already gave enough context to draft or revise the text well.
 
## Editing Rules
 
- Prefer the smallest rewrite that makes the prose better.
- Preserve specific terminology, decisions, and factual claims.
- Keep intentional informality when it supports the voice.
- Remove fluff, filler, and hedging unless they are serving a real interpersonal purpose.
- Avoid overexplaining.
- Avoid turning short writing into long writing.
## GitHub And Technical Writing Patterns
 
For GitHub issues, comments, and technical docs:
 
- State the problem or point early.
- Be explicit about impact, constraint, or tradeoff.
- Suggest the next action when useful.
- Use calm, direct language.
- If disagreeing, do it constructively and with reasons.
- Prefer clarity over cleverness.
## Output Guidance
 
Unless the user asks for commentary, return the improved or drafted text directly.
 
If context is missing, ask only the minimum needed questions first.
 
If the task is a cleanup pass on existing writing, avoid changing structure without approval and mention that constraint if relevant.
 
## Examples
 
**Example: cleanup request**
 
Input: "clean up this README section but keep my tone"
 
Behavior:
- improve grammar and flow
- keep the same general structure
- avoid changing the meaning
- ask before any meaningful reordering
**Example: GitHub response**
 
Input: "help me reply to this GitHub issue about the migration plan"
 
Behavior:
- respond clearly and directly
- acknowledge the issue context
- explain the reasoning simply
- keep the tone collaborative and grounded
**Example: new doc drafting**
 
Input: "draft a short design note for this API change"
 
Behavior:
- lead with the decision or proposal
- keep paragraphs short
- ask a practical follow-up only if needed
- keep the tone efficient, friendly, and technically curious
## Avoid AI Tells
 
Certain words and patterns are dead giveaways that a model wrote the text, not a person. They're vague, they sound impressive without saying anything specific, and they cluster together in ways real writers don't. Since the whole point of this voice is to sound like the user on a good day, actively strip these out of both new drafts and cleanup passes — don't just avoid adding new ones.
 
**Overused words**: delve, boast/boasts, tapestry, underscore, realm, leverage, robust, seamless, crucial, landscape, intricate/intricacies, meticulous/meticulously, pivotal, testament, vibrant, garner, bolster/bolstered, foster/fostering, streamline, harness, utilize (just say "use"), showcase, comprehensive, align with, navigate the complexities.
 
**Stock phrases and transitions**: "it's important to note that," "in today's fast-paced world," "in conclusion," moreover, furthermore, consequently, notably, importantly, "unlock the potential," "cutting-edge," "revolutionize the way," "win-win situation," "let's dive in."
 
**Sentence patterns**: "It's not just X. It's Y." / "No X. No Y. Just Z." These rhythmic contrast constructions read as templated, not composed.
 
**Punctuation**: watch em dashes (—) and en dashes (–). AI writing leans on em dashes constantly for dramatic pauses and asides — real writers use them occasionally, not in nearly every paragraph. Default to a period, comma, colon, or parenthesis instead. An em dash is fine when it's genuinely the clearest option, but if a paragraph has more than one, that's a signal to break the sentence up or repunctuate.
 
If a rewrite needs one of these words because it's genuinely the most precise term (e.g., "robust" in a load-bearing engineering sense), that's fine — the goal is killing filler, not banning words outright. The test: would the user actually say this out loud? If not, cut it or replace it with something concrete.
