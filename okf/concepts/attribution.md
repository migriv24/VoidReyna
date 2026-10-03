---
type: Concept
title: Attribution — models distinguish, humans identify
description: "The part with a real victim: why a wrong speaker attribution is a false statement about a person rather than a data-quality issue, the clustering/naming split that makes the work tractable without making it reckless, why confirmation belongs in the consuming application, and the publishable line enforced at the export seam."
tags: [status:draft, audience:all, confidence:proposed]
timestamp: 2026-08-12T00:00:00Z
---

# The stake

Everything else in this project is engineering. This is the part where being
wrong hurts someone.

The output is a **public website that says a named, real person said a specific
thing**. If a transcript does not label speakers — and Springfield's do not
exist at all, leaving YouTube auto-captions, which are timed and unlabeled —
then attribution is *inferred*. A wrong inference on a contested rezoning is not
a data-quality issue. It is a false statement about a person, published, with
our name on it.

So the discipline is not "try to be accurate." It is structural:

> **A model may propose a grouping. Only a human may attach a name.**

# Why the split works

The split is not a compromise between speed and safety — it is a recognition of
what the model is actually good at.

A diarization model is very good at *"these forty segments are the same voice"*
and has **no idea whose voice it is**. That is the whole shape of the problem:

- **Clustering is low-stakes and verifiable.** A wrong cluster is visible and
  fixable, and nobody is defamed by "these two segments sound alike."
- **Naming is a claim about a real person.** It is the part that gets published,
  the part that could be wrong in a way that matters, and the part a human can
  do quickly and correctly.

And the labour arithmetic is the reason this is tractable at all: **name a
cluster once, and one click attributes hundreds of segments.** An afternoon
instead of a month, with the accountability intact. Refusing model assistance
entirely would not be safer — it would mean the work never happens, and the
record stays inaccessible, which helps nobody.

# Where the confirmation happens — and it is not here

**In the consuming application, not in Reyna.** The reason is not UI convenience:

> A confirmation must be a **dispatcher command**, so that naming a cluster is
> logged, attributed, replayable and undoable like every other gesture.

If confirmation happened in Reyna it would happen outside the consumer's command
log, and the single most sensitive decision in the pipeline would be the one
thing with no audit trail. So Reyna **proposes** — emitting clusters, segments
and candidate attributions with their method and confidence — and Hormiga's
review surface is where a person says "cluster 7 is Councilor Stevens," as a
command.

This is the same **propose-never-write** shape Allomone's Weaver already uses,
and it is why Reyna is headless by design rather than by omission
([index](/index.md) §why not Void Maiz).

# Method and confidence on every claim

Every `said-by` edge carries **how it was arrived at**:

| method | meaning | publishable? |
|---|---|---|
| `labeled` | the source document said so | **yes** |
| `human` | a person confirmed it | **yes** |
| `diarized` | grouped by voice, cluster named by a person… but this segment's *membership* was inferred | no — surfaced in-app |
| `inferred` | guessed from text cues (`"Councilor Smith:"`, turn-taking) | no — surfaced in-app |

**Only `labeled` and `human` may reach the website.** That line is enforced at
the export seam Hormiga already has — `web-hide`, built and tested — rather than
by template convention, which is the same reason the internal-notes rule is
enforced at the read.

**Every statement links to its source at a timestamp.** The claim is checkable
by the reader, and that is the only real defence against being wrong: not
confidence, but citability.

# Where the models run

At the **holiday boundary**, and the answer is forced rather than chosen. Void
Core's transform-layer invariant 4: *"any nondeterminism is injected by the
action, never generated inside."* A diarization model is nondeterministic and
impure, so it cannot live in the pure interior. The resolution is not to abandon
reproducibility:

> **Run the model at the boundary, record its output as data, and make
> everything downstream a pure function of that record.**

The model's output becomes an **input**. What that buys:

- **A run is re-runnable without the model** — the segments are archived.
- **The model version is part of the record**, so "re-transcribed in 2028 with a
  better model" is a **new dated assertion**, not a silent overwrite. That is the
  same mechanism a council amending a policy uses — one shape, two uses.
- **A model can be swapped** without invalidating anything downstream.
- **Everything after the boundary tests with no GPU and no network.**

# The good news that makes all of this safe to defer

**Minutes record who moved, who seconded, and how each member voted — by name,
as a matter of law.**

So the highest-value, legally-meaningful half of the dataset — the votes —
**needs no machine learning at all.** It needs a PDF parser and a careful eye.

The two halves split cleanly, and they should never share a pipeline or a trust
rule:

| | source | attribution | ML needed |
|---|---|---|---|
| **votes, attendance, adoptions** | minutes | `labeled`, authoritative | none |
| **statements** | auto-captions | inferred | diarization |

Doing votes first yields a real, publishable, fully-attributed civic dataset with
**zero** attribution risk — and puts everything in this document behind a product
that already works without it.
