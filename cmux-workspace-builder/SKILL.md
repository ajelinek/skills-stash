---
name: cmux-workspace-builder
description: >
  Guides users through building a cmux.json workspace configuration file via a
  structured interview. Use this skill whenever a user wants to set up cmux,
  design a terminal workspace layout, configure split panes, automate their dev
  environment, or create custom commands. Trigger on phrases like "set up cmux",
  "create a cmux config", "build my workspace", "cmux layout", "terminal splits",
  "workspace definition", or whenever the user describes a multi-pane terminal
  setup they want to automate — even if they don't mention cmux by name.
---

# cmux Workspace Builder

Your job is to **interview the user** and gather everything needed to build a
great `cmux.json`. Don't generate config until you've asked the right questions
and confirmed the plan. A user who says "set up cmux for me" hasn't given you
enough yet — ask first.

## Step 0: Fetch the latest schema

Before doing anything else, fetch the current docs so you're working with the
right field names and behaviors:

```
https://cmux.com/docs/custom-commands
```

## Step 1: Run the interview

Work through these questions conversationally — don't dump them all at once.
Group related questions together and adapt based on what the user has already
told you. The goal is a dialogue, not a form.

### Panes & layout

Start here — this is the core of the workspace:

1. **How many panes** do you want visible at once?
   (e.g. 2 side by side, 3, a 2×2 grid of 4)

2. **What goes in each pane?** For each one, find out:
   - What is it for? (e.g. frontend server, API, logs, idle shell, browser preview)
   - What **command** should run when it opens — or should it be an empty shell?
   - What **directory** should it start in?
   - Any **environment variables** it needs?

3. **How should the panes be arranged?**
   Ask the user to describe it in plain words. You can offer examples:
   - Left/right split?
   - One big pane on the left, two stacked on the right?
   - 2×2 grid?
   - Something else — describe it and I'll figure out the splits

4. **Browser panes?** Do you want any pane to show a web preview (e.g. localhost:3000
   inline next to your terminal)?

5. **Which pane gets focus** when the workspace opens? (Usually the one you'll
   type in first.)

### Utility commands

These are quick actions that appear in the command palette but don't open a workspace:

6. **Any one-shot commands** you run regularly?
   (e.g. run tests, run migrations, deploy, install deps, reset the database)

7. For each one: should it **ask for confirmation** before running?
   Good idea for anything slow, destructive, or hard to undo.

### Workspace settings

8. What should the **workspace tab be called**?

9. Any **color** for the tab? (hex value, or describe it — e.g. "something green")

10. If you trigger this command when the workspace is **already open**, what should happen?
    - **Switch to it** and leave it running (best for long-lived dev environments)
    - **Ask before recreating** (good when the workspace has state worth keeping)
    - **Always recreate** (good for stateless or reproducible setups)

11. **Per-project or global?**
    - Per-project: saves as `./cmux.json` in your project directory
    - Global: saves to `~/.config/cmux/cmux.json`, available everywhere

## Step 2: Confirm the plan

Before writing any JSON, summarize the layout in plain language and confirm.
For example:

> Here's what I'm planning:
>
> **Workspace: "Dev"** (React blue tab)
> - Left half: frontend terminal → `npm run dev` (focused on open)
> - Right top: browser preview → localhost:3000
> - Right bottom: idle shell for git/scratch work
>
> **Utility commands:**
> - "Run Tests" → `npm test -- --watch` (no confirmation)
> - "Install" → `npm install` (with confirmation)
>
> Does this look right? Anything to change before I generate the config?

## Step 3: Generate the cmux.json

Once the user confirms, produce a complete, valid `cmux.json`. Key rules:

### Layout rules

- Layouts are **binary trees**: every split node has **exactly two children**
  (another split or a pane). Never more, never fewer.
- `direction: "horizontal"` = left/right; `direction: "vertical"` = top/bottom
- `split` is 0.1–0.9 (0.5 = equal halves)
- For 3+ panes, **nest splits** — e.g. a right column split vertically inside a
  horizontal split creates 3 panes total
- Each `pane` has a `surfaces` array — one item per tab within the pane

### Surface rules

- `type: "terminal"` for shell panes; `type: "browser"` for web panes (needs `url`)
- `command` auto-runs when the surface opens — omit it for idle shells
- `cwd` is relative to workspace `cwd` unless it starts with `~` or `/`
- `env` is a `{ "KEY": "value" }` object
- `focus: true` on the surface the user types in first

### Command rules

- `workspace` commands define layouts; `command` commands are one-shot shell runners
- `confirm: true` for anything slow, destructive, or irreversible
- `restart`: `"ignore"` (switch to existing), `"confirm"` (ask), `"recreate"` (rebuild)
- Every command gets a `keywords` array with synonyms and abbreviations

## Step 4: Deliver and explain

After generating, summarize what was built:
- What each command does
- How the layout is arranged
- Any assumptions you made, so the user knows what to adjust

---

## Layout patterns reference

**Two panes side by side:**
```
horizontal → [pane A] [pane B]
```

**Main pane + two stacked on the right:**
```
horizontal → [pane A] [vertical → [pane B] [pane C]]
```

**2×2 grid:**
```
horizontal → [vertical → [pane A] [pane B]] [vertical → [pane C] [pane D]]
```

**Top bar + two columns below:**
```
vertical → [pane A] [horizontal → [pane B] [pane C]]
```
