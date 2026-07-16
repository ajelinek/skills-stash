---
name: grilling
description: >
  Grill the user relentlessly about a plan, decision, or idea. Use when the
  user wants to stress-test their thinking, or uses any 'grill' trigger
  phrases.
---

# Grilling

Interview the user relentlessly about every aspect of the plan, decision, or
idea until you reach a shared understanding. Walk down each branch of the
decision tree, resolving dependencies between decisions one by one. For each
question, provide your recommended answer.

## Rules

1. **One question at a time.** Ask a single question, then wait for the
   user's answer before asking the next. Asking multiple questions at once is
   bewildering.
2. **Recommend, don't just ask.** For each question, state your recommended
   answer — and why — then let the user confirm or override it.
3. **Look things up, don't ask.** If a fact can be found by exploring the
   environment (filesystem, tools, code, docs, etc.), look it up yourself
   rather than asking the user. Reserve questions for things that are
   genuinely the user's decision to make.
4. **Follow the dependency chain.** Walk down each branch of the decision
   tree in order — resolve a decision before moving to the ones that depend
   on it. If an answer changes what's downstream, re-derive the affected
   branch before continuing rather than asking questions that are now moot.
5. **Don't act until confirmed.** Do not implement, write, or execute
   anything based on this interview until the user explicitly confirms that
   shared understanding has been reached.

## Ending the interview

Once every branch has been resolved, summarize the shared understanding in
plain language — the plan or decision as agreed, including every point where
the user overrode your recommendation — and ask for final confirmation
before doing anything else.
