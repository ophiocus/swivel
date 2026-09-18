---
name: swivel
description: Stash and restore working focus like git stash, and keep the session's CORE theme recallable when other threads intrude. Use when the user says "swivel", "stash this", "park this and switch", "what was I doing", "what are we actually doing", "pop the stash", or when a request arrives that opens a new frame unrelated to the thread in progress. Keeps a core lane plus numbered injected lanes on disk so a context switch costs nothing and the main theme never gets lost.
---

# swivel — git stash, for attention

A long session accumulates in-flight state that lives nowhere but the transcript:
which PR is awaiting whose review, which form is half-packaged, which contact is
parked and why. Switching focus loses it. `swivel` writes that state to disk as a
numbered stack so the switch is free and the return is exact.

## Core vs injected — the part that matters most

A long session does not lose its theme in one step. It loses it by servicing a
reasonable request, then another off the back of that, until the transcript's apparent
subject is three frames away from the thing that was actually being built — and nobody
can say when it changed. **Swivel's first job is not stashing. It is keeping the core
theme recallable at every point in the thread.**

### The two kinds of thread

**CORE** — the theme that owns the session's accumulated state. It has produced
artifacts, it has a counterparty who is responding, and it set a clock. It survives
silence: leave it for a day and it is still the thing you were doing.

**INJECTED** — a thread that entered from an *ambient surface* — an inbox, a tracker, a
notification, a workspace's own gravity — rather than from the core's next step. It can
be urgent, legitimate, and worth doing in full. It is still not the theme.

### The three-question test

Ask at the moment a new frame opens:

1. **Provenance** — did this arise from the core thread's own next action, or from a
   surface I happened to look at?
2. **Counterparty and clock** — does it have its own, distinct from the core's?
3. **Advancement** — if completed perfectly, does the core move?

*Surface + own counterparty + core does not move* = **injected**. Log it as such.

### Workspace gravity is not theme

The most common source of injection is the container. A repository, a folder, a tracker,
a memory file full of one kind of rule — these constantly re-suggest their own subject.
A core theme living inside a differently-shaped workspace has to be **actively held**, or
the workspace wins by default. Suspect an injection whenever the new frame matches the
*workspace's* usual business rather than the *session's* current work.

### Injections nest, and depth is the danger signal

An injection spawns injections. Depth 1 is normal. **Depth ≥ 2 is where scope violations
happen** — by then the frame has drifted far enough that the original constraints are no
longer in view. On reaching depth 2, stop and re-state the core before continuing.

### The rules

- **Never refuse an injection for being one.** Service it fully and well. Classification
  is bookkeeping, not gatekeeping.
- **Name it once, at entry.** One clause: *"parking core X for this."* Not a lecture.
- **Keep the pointer home alive.** When an injected stretch runs long, the reply that
  closes it says what the core is and what its next action was.
- **Never let an injection silently become the lane.** If it earns lane status, that is a
  deliberate promotion, said out loud, written to the index.
- **Recallability is the acceptance test.** At any point in the thread, *"what were we
  actually doing?"* must be answerable in one line without scrolling. If it is not, swivel
  was not doing its job.

## Storage

Lanes live in `<project>/.swivel/`.

- `lane-<name>.md` — **exactly one is marked CORE**: the session's theme. Every other
  lane is injected, and carries what it was injected off and when.
- `INDEX.md` — which lane is core, which is active, and the injection ancestry.
- `CASE-*.md` — worked examples kept as precedent.

The core lane is never deleted and **never demoted by drift** — only by the user saying
outright that the theme has changed.

Numbering is monotonic: the newest stash has the highest number. `swivel@{0}` always
means "the most recent stash", exactly like git.

## Commands

| Say | Meaning |
|---|---|
| **swivel** / **swivel push** | Snapshot the current focus, write it, confirm, then ask what we're switching to |
| **swivel pop** | Restore the newest stash into working context, then mark it popped |
| **swivel apply** | Same as pop, but leave the stash in place |
| **swivel list** | Show the stack from `INDEX.md` |
| **swivel show N** | Print stash N in full |
| **swivel drop N** | Mark stash N dropped (never delete the file — history is the point) |

Bare "swivel" with a destination ("swivel to the Drupal work") means push-then-switch
in one move.

## What a stash MUST capture

A stash is only worth writing if it survives a cold read a week later. Every one carries:

1. **Headline** — one line naming the focus being parked.
2. **Live state, with evidence** — refs, SHAs, URLs, message ids, row numbers. Never
   "the PR is waiting on review"; write "#195 head `027720d`, MERGEABLE, reviewer
   requested changes 10:29Z". A stash that repeats a claim without its evidence is a
   trap, not a record.
3. **Whose ball** — for each open thread, ours or theirs, and what unblocks it.
4. **Next physical action** — the specific thing that happens on resume, precise enough
   to act on with no thinking.
5. **Landmines** — the gotchas discovered this session that would be re-learned
   expensively (silently-failing tools, stale rows, quoting traps).
6. **Timestamp** — computed with `date`, never inferred.

## Rules

- **Verify before stashing, not after.** A stash is a claim about the world; check the
  live source in the same turn you write it. A stale stash is worse than none.
- **Pop means re-verify.** On restore, re-check anything time-sensitive before acting on
  it — the world moved while the stash sat. State plainly what changed since.
- **Never delete.** `drop` marks; it does not remove. The stack doubles as a session log.
- **One stash per focus, not per interruption.** A two-minute detour does not earn one.
- **The canonical tracker still wins.** If the project keeps live status somewhere
  canonical (a sheet, an issue board), it belongs there; a stash points at it, never
  replaces it.

## Stash file format

```markdown
# swivel@{N} — <headline>

**Stashed:** <YYYY-MM-DD HH:MM TZ, computed>
**Status:** active | popped <date> | dropped <date>

## Live state
<claims, each with its evidence>

## Whose ball
<thread → ours/theirs → what unblocks>

## Next physical action
<the precise thing to do on resume>

## Landmines
<gotchas that would otherwise be re-learned>
```
