# Configure the Two Review Agents

Installing the skill does **not** register its bundled agent templates. Before using it, configure
both named agents in the chosen host and confirm that fresh named-agent dispatch is available.
This is setup guidance for the user or a separately authorized setup workflow, not an instruction
for the review skill to install anything.

## Contracts and Models

Bundled, self-contained templates:

- [rubber-duck-guide](../agents/rubber-duck-guide.md): constructive Duck role.
- [rubber-duck-adversary](../agents/rubber-duck-adversary.md): adversarial role.

Each body includes its full boundaries and output contract so an installed copy need not locate
the skill's other files. Preserve those bodies when translating metadata to another host.

Choose a model and supported reasoning effort for **each** role using the host's current model
catalog and available account access. Model names here are examples of intent, not pinned IDs:
an Opus producer can use Sol critics where the host supports that pairing. Both critics may use
the same complementary model; they need not differ from one another.

In a Claude-only environment, both may be independent instances of the same model as the producer.
This provides separate-context review, not cross-family diversity. If the producer's model later
changes, report the actual relationship rather than changing the configured critics automatically.

Confirm whether each model is pinned or deliberately inherited. The bundled `model: inherit` is a
Claude Code template default, not proof that a model choice or an installation has been confirmed.
Never infer an effective identity from an agent's self-description or a model merely being listed.

## Claude Code

The templates use Claude Code-style agent frontmatter. During explicitly authorized setup, place
the files in either the project's `.claude/agents/` or the user's `~/.claude/agents/`, choosing scope
deliberately. Do not overwrite existing agents with the same IDs without resolving the collision.

Retain `model: inherit` only if inheritance is the intended choice, or set a model supported by that
host. The templates allow only `Read`, `Grep`, `Glob`, and `WebFetch`: no edit, shell, or delegation
tools. Confirm which tools are actually available under the user's policies. Use the host's supported
agent discovery/reload mechanism before claiming installation succeeded.

## OpenCode, Copilot, and Other Hosts

Translate the complete agent definitions using that host's current documented configuration:

- Register callable named subagents with these IDs, or an explicitly configured one-to-one ID mapping
  that is passed to the caller. Do not guess names, silently resolve collisions, or use generic agents.
- Preserve the full role bodies and give each its selected model through agent configuration.
- Translate tool access to read-only exploration. Claude's `tools` list and `model: inherit` are not
  universal syntax; don't copy their meanings blindly. OpenCode configurations, for example, may need
  `mode: subagent` and a provider-qualified model plus host-specific permission fields.
- Deny writes, mutation-capable commands, and further delegation where enforceable. An allowed-tools
  list, a behavioral prohibition, and an enforced sandbox are different things; state the limits.
- Confirm both roles are discoverable and independently dispatchable, including the required nesting
  depth if a larger workflow calls this skill. Do not weaken policies or raise global depth silently.

Copilot's native Rubber Duck is useful prior art, but it is **not** a substitute for these two
configured roles. Do not claim the native feature ran when these custom agents did the review.

If the host cannot faithfully express both roles and their independent read-only dispatch, leave
the skill unready and explain the missing capability. Do not shell out to a second vendor's CLI.

## Invocation

Interactive example:

> Rubber-duck this migration plan. Keep the API contract unchanged. Propose improvements before
> editing the document.

Workflow packet:

> Invoke `rubber-duck` on revision R3 of this design. Goal: prevent duplicate fulfillment while
> retaining retries. Evidence: the supplied handler, schema, and tests. The producer may revise this
> design in scope, but may not edit source, add dependencies, or change requirements. Use at most
> two repair rounds. Return unresolved decisions to this caller, not to a human directly.

The caller retains artifact ownership, budget, and completion state. Neither example grants the
critics writing permission or turns this checkpoint into implementation delegation.
