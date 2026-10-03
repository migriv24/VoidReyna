---
okf_version: "0.1"
type: Index
title: Void Reyna
description: The front door — what Void Reyna is, the founding commitments, and where every other document lives.
tags: [status:draft, audience:all, confidence:proposed]
timestamp: 2026-08-12T00:00:00Z
---

# Void Reyna

**The dataset generator.** A Python application, founded 2026-08-12, built on
Void Core (`../VoidCore` — the engine, which ships a real Python package). Its
first client is Void Hormiga (`../VoidHormiga`).

One sentence: **Void Reyna harvests the unstructured public world, archives what
it fetched as evidence, transforms it through pure mappings with laws attached,
and emits the result as a Void Core command transcript.**

> **Name.** *Reyna* — queen. A queen ant does not forage or build; she **founds
> the colony**. Reyna founds a dataset: Hormiga then keeps it, maps it, dates it
> and publishes it. The distinction is the architecture — Reyna *produces* a
> model, Hormiga *views* one.

# The founding commitments

1. **The archive is the product.** Fetching is easy. Proving in two years what a
   page said on a given day is the hard and valuable part. Nothing is parsed
   before it is archived; the archive is never edited; every claim points at the
   bytes it came from. See [harvest](/concepts/harvest.md).
2. **Impurity at the boundary, nowhere else.** Void Core's banked invariant —
   *effects live at the holiday boundary* — is the spine. Network, disk and
   **models** are boundary work; everything downstream is a pure function of
   what the boundary recorded. That is what makes a run re-runnable without a
   GPU and testable without a network.
3. **Every transformation is a holiday with a law.** A holiday is *an effectful
   crossing plus a pure mapping*, and the mapping carries a round-trip law so a
   lossy adapter is caught structurally rather than discovered later. Adapters
   route through a **pivot**, never directly, so N formats cost N adapters
   instead of N×M. See [foundations](/concepts/foundations.md).
4. **We emit verbs.** The contract with any consumer is a command transcript.
   Nothing is linked, no header is shared, no schema is kept in sync across two
   languages. Every import is therefore already replayable, undoable and
   attributable, because that is what commands are.
5. **Models distinguish; humans identify.** A model may propose a grouping;
   only a person may attach a name, and that confirmation happens in the
   consuming application as a logged command. Reyna proposes and never asserts
   identity. See [attribution](/concepts/attribution.md).

# Map

- [Foundations](/concepts/foundations.md) — the mathematics, each idea paired
  with what it buys and honest about what was evaluated and declined: lenses and
  the round-trip law (built upstream), **delta lenses** as the change-propagation
  upgrade, **provenance semirings** as the algebra of trust and method,
  functorial data migration as vocabulary-for-thinking, and Memento as the
  protocol shape the whole design already has.
- [The pivot](/concepts/pivot.md) — what every source format maps into: four
  coordinate systems (Trail, Span, Site, Key), read off the consumer's own
  predicate vocabulary and carried as a *set* per item, because six of the
  twenty-two cases need more than one at a time.
- [Extraction cases](/concepts/extraction-cases.md) — twenty-two hypothetical
  harvests, civic and not, used as a stress test rather than a roadmap. The page
  that found the pivot, by breaking the old one.
- [Records requests](/concepts/records-requests.md) — the four-rung ladder for
  material a harvester cannot reach, and why a closed door is a reason to ask.
- [Harvest](/concepts/harvest.md) — the boundary layer: politeness, per-platform
  adapters over generic crawling, the evidence record, change detection, and why
  a moved snapshot id is itself a finding.
- [Attribution](/concepts/attribution.md) — the part with a real victim.
  Method and confidence on every claim, the publishable/unpublishable line, and
  why confirmation belongs in the consumer rather than here.
- [Roadmap](/roadmap.md) — phases, gated by exit tests.
- [Developer questions](/developer_questions.md) — open decisions with leans.
- [Log](/log.md) — the running history.

# Why not Void Maiz

Void Maiz is the **view** library (canvas, gestures, faces, Allomone) and it is
C++ with no Python. Reyna is batch and headless, so it would use almost none of
it — and the one place a UI seems necessary turns out to belong elsewhere:

> **The human confirmation step must be a dispatcher command**, so that naming a
> voice cluster is logged, attributed, replayable and undoable. If it happens in
> Reyna it happens outside the consumer's log. So it happens in **Hormiga**.

Reyna proposes; Hormiga confirms. That is the same propose-never-write shape
Allomone's Weaver already uses, and it means Reyna stays headless by design
rather than by omission. Whatever operator UI it needs — watching a harvest,
inspecting a failed parse — is a CLI, not a canvas.

*(A Python Void Maiz may be worth building one day. It should be justified by
its own clients, not by this one, because this one dissolved.)*

# Status

**Phase 1 is built and green: the evidence locker.** `reyna/` is stdlib-only,
has archived real bytes from Springfield, and correctly reports a changed
document. Since 2026-08-17 it also has the **pivot**: four formats (Document,
Table, Geometry, Timeline) mapping into one `Trove` through lenses that carry the
round-trip law, and one emitter written once against it. Phase 2 — votes from
minutes, no ML — is current, and its blocker is discovery (R8).

The concepts here were written 2026-08-12 alongside Hormiga's
[civic record](../../VoidHormiga/okf/concepts/civic-record.md), which is the
first client and the reason this project exists.

**One finding worth the front page:** Springfield's Laserfiche portal, which
holds every pre-Nov-2024 agenda packet, returns `Disallow: /`. We obey it. The
packets turned out to be reachable on the main domain, which permits everything —
but the general lesson is in [R1](/developer_questions.md), and it is that the
answer to a closed door is to *ask*, not to route around it.
