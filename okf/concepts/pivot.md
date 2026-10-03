---
type: Concept
title: The pivot — four coordinates, one Trove
description: "What every source format maps into, and why it is four coordinate systems and not one: Trail, Span, Site and Key, carried as a SET on each item. Includes the correction it makes to the earlier design, the flat/JSON wire decision, and what a new format actually costs."
tags: [status:current, audience:dev, confidence:asserted]
timestamp: 2026-08-17T00:00:00Z
---

**Answers [Q32](../../VoidHormiga/okf/developer_questions.md)**, which asked for
a `geometry` payload before any polygon importer, on the grounds that *without a
pivot, "use a holiday" is a direct adapter in a costume.* The answer turned out
to be larger than geometry, and better for it.

# The correction this makes

`emit.policy_lens` named `Document` as "the PIVOT". That was defensible with one
format and is **wrong** with more than one: a pivot is what all the legs meet at,
and `Document` is a leg. The mistake was invisible while there was only one.

It became visible by writing out [twenty-two hypothetical
harvests](extraction-cases.md) — budgets, zoning layers, meeting minutes, a
transit feed, a museum catalogue — and noticing that a set of minutes, a budget
table and a zoning map are not documents and never will be.

# The finding

Sort those twenty-two by **what question you ask about an item's position** and
there are exactly four answers:

| coordinate | asks | carries |
|---|---|---|
| **Trail** | what is this inside of? | `("3","3","1")`, or an ordinal among siblings |
| **Span** | when, and for how long? | two bounds, each a date / OPEN / UNKNOWN, plus a frame |
| **Site** | where, and what is near it? | a name, a tiling cell, or geometry (point/path/area/**volume**) |
| **Key** | which cell of the cube? | named dimensions in order |

**This is not invented — it is read off the consumer.** Hormiga's Allomone ships
22 domain predicates and they partition exactly this way: `under` is Trail;
`before`/`after`/`overdue`/`upcoming`/`undated` are Span; `near`/`near-rune`/
`located` are Site; `field`/`field-has`/`role` are Key. The application has been
asking questions in four coordinate systems since before this page existed.
Building the pivot from the same four is not a new abstraction; it is finally
naming one that was already load-bearing at the far end.

## Loci are a SET, not a choice

Six of the twenty-two cases need more than one coordinate at once. A council
district redrawn every ten years is a region **and** an interval, and neither is
optional — a 2011 district and a 2021 district can share a name and share nothing
else. A calendar entry is a time and a place. A hex-binned service map is a cell
and a period.

So `Item.loci` is a tuple. A design that made the four exclusive would fail on a
redistricting map, which is about as ordinary as civic data gets.

## What is deliberately *not* a coordinate

- **A graph.** It is the destination, not a source shape. Items point at each
  other through `Item.refs`, which emit as links; the interesting graph structure
  is the consumer's model rather than something extraction discovers. Case 21 (a
  citation network) was the check on that, and it held.
- **Decision time.** An assertion's *position* in time is its validity; when a
  body decided is a fact the source states *about* the assertion, so it is a
  field. See [Q31](../../VoidHormiga/okf/developer_questions.md).

# The three states that must not collapse

Each is a place where a convenient default would have been a lie.

**`Span`: a date, OPEN, or UNKNOWN.** OPEN is "until further notice"; UNKNOWN is
"we did not see one". The default is UNKNOWN, so an emitter that means
*indefinitely* has to say so on purpose — which `emit` does for an adopted
policy, because that genuinely is what adoption means.

**`Site`: named, celled, or drawn.** An address or "2 mi N of Eugene" is how the
most common spatial datum actually arrives, and a design where a place must be a
number pair cannot represent it at all. Geocoding is then a *holiday* that fills
in the geometry and leaves the name exactly as the source wrote it.

**`Cite`: verbatim, derived, or withheld.** A released records request with black
bars is a different fact from a record we never saw.

# The wire, and why it is not all JSON

Loci travel as one `setjson loci` field — except when the flat form
(`number`, `from`, `until`) is *exactly* equivalent, which is the ordinary case.
A transcript is read by people, and `set opp-3-3-1 number '3.3.1'` is legible and
is precisely what Hormiga's civic glyphs already store.

The test for "exactly equivalent" is deliberately strict, and the sharpest case
is why: an absent `until` already means *indefinitely* to the civic model, so the
flat form has no way to say *unknown*. An UNKNOWN bound therefore refuses the
flat form and goes as JSON. A flat form that is *nearly* right is a silent loss,
which is the failure this project keeps finding in its own code.

# What a new format costs

One lens, `Format ⇄ Trove`. Everything downstream is inherited, and the
round-trip law it inherits is **earned rather than assumed**, because
losslessness composes ([foundations §1a](foundations.md)):

    Document ⇄ Trove ⇄ transcript
    Table    ⇄ Trove ⇄ transcript      ← one new lens
    Geometry ⇄ Trove ⇄ transcript      ← one new lens
    Timeline ⇄ Trove ⇄ transcript      ← one new lens

`policy_lens` is now literally `document_lens(...).compose(trove_lens(...))`,
which makes `Lens.compose` load-bearing rather than a convenience — and gives the
[request for it upstream](../../VoidHormiga/MESSAGE_FOR_VOIDCORE_hormiga-lens-composition-2026-08-12.md)
a working reference implementation behind it.

**The claim was tested rather than asserted.** `tests/test_pivot.py` runs a
budget CSV, a zoning GeoJSON (polygon with a hole, linestring, 3-D point,
unreadable geometry) and a WebVTT meeting transcript through the round-trip law,
composed with the one shared emitter — which `emit.py` was **not modified** for.
A voxel layer goes through the same unmodified path. If the pivot were
decoration, the emitter would have needed teaching.

# What it does not fix

- **Discovery.** Four of the catalogue's cases fail at "which URLs exist", each
  differently: a sitemap, an index page, a zip manifest, an API cursor. That is a
  `Source` abstraction with `discover()`, and it is the honest reading of the
  phase-2 blocker in the [roadmap](/roadmap.md).
- **Containers.** One blob can hold many troves of different kinds (an agenda
  packet, a GTFS zip). Extraction still returns one structure per blob.
- **Provenance algebra.** `Cite.method` is a string. It becomes a
  [semiring](foundations.md#3-provenance-semirings--one-algebra-for-where-from-how-and-may-we-publish)
  when a claim first rests on two sources at once, and not before.
