# Executing the plan via a browser tool

This only applies once the user has approved Path B in the main skill file.
It is deliberately light on exact click-paths — the Claude.ai UI changes, and
hard-coded selectors go stale. Drive it by reading the live page, not by
recalling a fixed layout from training data.

## Before starting

- Confirm the user is actually logged into Claude in the browser the tool
  controls. If a login/auth screen shows up instead of the app, stop and tell
  the user rather than trying to work around it.
- Re-state the approved plan in short form (which Projects, which chats move
  where) before taking the first action, so there's a last checkpoint before
  anything changes.

## General approach

Work **one Project at a time**, not as one uninterrupted batch:

1. Create (or open, if it already exists) the Project.
2. Set its name and description as approved.
3. Move/assign the approved chats into it.
4. Set up the approved file/folder structure (project knowledge files).
5. Report what happened for that Project — created, renamed, N chats moved,
   files added — before moving to the next one.

If a step fails (an element isn't where expected, a chat can't be found,
an action is refused), stop and surface the failure — don't guess at an
alternate path silently. The Claude.ai UI's exact controls for creating
projects, adding files, and moving conversations change over time; read
what's actually on screen (visible labels, accessibility tree) rather than
assuming a specific menu structure.

## Guardrails

- Never take an action outside the approved plan (e.g. don't rename a
  Project the user didn't ask you to touch, don't archive/delete anything —
  Path B only creates/moves/labels, per the main skill file's non-goals).
- If mid-execution the user wants to change the plan, stop, confirm the
  change verbally/in-chat first, then resume — don't silently adapt.
- At the end, give a final summary of everything actually done, and call out
  anything from the plan that was skipped or failed, so the user's mental
  model matches reality.
