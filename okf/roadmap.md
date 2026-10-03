---
type: Roadmap
title: Roadmap
description: Phases gated by exit tests, front-loaded with what can kill the project. Phases 0 and 1 exited 2026-08-16; phase 2 (votes from minutes) is current.
tags: [status:current, audience:dev, confidence:asserted]
timestamp: 2026-08-12T00:00:00Z
---

Phases are gated by **exit tests**, not by calendar, and ordered so that anything
that can kill the project fails early and cheaply.

Phase 0 exited 2026-08-16 in Hormiga, where its exit test lived. **Phase 1
exited the same day** — the evidence locker is built, tested, and has archived
real bytes. Phase 2 is current.

# 0 — Design — EXITED 2026-08-16

The concepts in this OKF. Exit test: **Hormiga hand-builds one meeting and the
data model survives contact with it.** Green — `VoidHormiga/src/civic.hpp` +
`tests/civic_smoke.cpp`, seven design claims passing.

What it changed for us: **edges carry only `(relation, directed)`** through a
projection, so anything richer is a rune or a field; and the consumer resolves
change as a **merge over dated assertions**, which means Reyna emits assertions
and **never has to decide which of two conflicting amendments wins.**

# 1 — The evidence locker — EXITED 2026-08-16

`reyna/archive.py`, `reyna/harvest.py`, `reyna/cli.py`, `tests/test_archive.py`.
Stdlib only, no dependencies.

**Exit test, passed — and taken more strictly than written.** The roadmap asked
for "fetch the same document twice, a week apart." Waiting would only prove the
page *did not* change; the test instead serves the document from a local server
and **changes it between fetches**, proving we would notice if it did. Three
fetches, two versions, one change caught, plus 404-as-evidence, robots
enforcement, append-only content-addressed blobs, and immutable records.

Verified against the real world too: `springfield-or.gov` captured, re-fetched,
and correctly reported **304 unchanged** by a live server.

**What it found:** a self-comparison bug in the store API (deleted, not
documented — see the log), `urllib.robotparser`'s divergence from RFC 9309 (R2),
and the one that reshapes the next phase — **Laserfiche disallows all crawlers**
(R1), while the packets are reachable on the permitted domain anyway.


# ⏸ PAUSED 2026-08-18 — read this first

**Reyna is deliberately parked at a clean boundary**, not abandoned. The author's
call: generating *new* data matters less right now than being able to put data
into an existing database, so Hormiga's headless adoption comes first.

**Everything below phase 2 is unstarted, and phase 2 is unblocked but unbegun.**

## What works today, end to end

    reyna fetch <url>        polite, conditional, archives bytes + a content id
    reyna ingest <file>      evidence that arrived by records request, not HTTP
    reyna extract <id>       PDF text, or --structure for numbered provisions
    reyna emit <id>          a Void Core command transcript, every rune cited
    reyna changes <url>      only the fetches where content DIFFERED

Proven on a real 150-provision Springfield policy: **1,952 commands, 282 of 282
runes citing the bytes they came from**, replayed into Hormiga by its own test.
`python tests/run_all.py` → 4/4, stdlib only, no network.

## What a future session should NOT have to rediscover

- **The pivot is `Trove`, not `Document`.** Four coordinates — Trail, Span, Site,
  Key — read off Hormiga's own Allomone predicates. See [pivot](/concepts/pivot.md).
- **A new source format costs ONE lens.** `Format ⇄ Trove`; the emitter is
  written and must not be touched. If a format seems to need emitter changes,
  the lens is wrong.
- **`reyna/lens.py` is a re-export now.** The implementation is vendored from
  Void Core in `vendor/voidcore/`; do not re-fork it.
- **Quoting is settled and pinned** (`tests/test_quoting.py`) against Void Core
  SPEC §6.1 — including the trailing-backslash trap that four independent
  implementations got wrong. Do not hand-roll it again.
- **The blocker for phase 2 is discovery (R8), not extraction.** We can parse a
  packet; we cannot yet enumerate which packets exist.

## The cheapest way back in

Phase 2 needs exactly one thing before any code: **a list of packet URLs.** Get
it from the meetings page, the request form, or a records request (the letter is
drafted in [records-requests](/concepts/records-requests.md)). With that list,
the existing `fetch` → `extract` → `emit` path already runs; what is new is a
minutes parser producing `Trove` items with `Span` loci and `refs` for
mover/seconder/vote, which is a day's work against the shape that already exists.

# 2 — Votes from minutes (NEXT, unblocked but unbegun)

The first real adapter and the first real dataset. Minutes → who moved, who
seconded, how each member voted, what was adopted. **No ML.**

**Not via Laserfiche** — it disallows crawling (R1). Packets are served from
`springfield-or.gov/wp-content/uploads/…`, which permits everything, and one
41.5 MB packet from 2023-04-03 is already archived. The remaining question is
discovery: the sitemap is pages-only, so finding *which* packets exist needs the
meetings page, the form, or a records request rather than a crawl.

**Exit test:** one Springfield meeting's votes emitted as a command transcript,
replayed into Hormiga, matching the PDF by hand-check — with every claim carrying
a citation back to an archived snapshot.

This phase produces a **publishable dataset on its own.** If the project stopped
here it would have been worth doing.

# 3 — The pivot formats — **EXITED EARLY, 2026-08-17**

Done ahead of schedule, and larger than planned: not "geometry through a pivot"
but **four coordinate systems** (Trail, Span, Site, Key) and four formats
(Document, Table, Geometry, Timeline), each reaching the transcript through its
own lens composed with one shared emitter.

**The exit test was met and then some.** It asked that a second geometry source
land with one new lens and no downstream changes. What actually happened:
*three* new formats — a budget CSV, a zoning GeoJSON, a meeting WebVTT — landed
with one lens each and **`emit.py` was not modified at all**, which
`tests/test_pivot.py` asserts. A voxel layer goes through the same untouched
path, which was the author's hypothetical and is now a passing test.

What is still deferred: an actual ArcGIS *fetch* of Springfield's ward
boundaries. The lens exists and is tested against real GeoJSON; nobody has
pointed it at the city's server yet, because that is phase 2's discovery problem
wearing a different hat.

# 4 — Statements, unattributed

YouTube captions → timed, segmented statement runes, with **no speaker claims at
all**. Searchable by topic, linked to the meeting and the video timestamp.

**Exit test:** a topic search returns statements with working timestamp links,
and **nothing on the website names a speaker.**

# 5 — Attribution, assistive

Diarization at the boundary; clusters proposed; Hormiga's review surface for
naming; method and confidence on every edge; the publishable line enforced at the
export seam.

**Exit test:** an unnamed cluster is invisible on the website; naming one in
Hormiga is a single logged command that attributes every segment in it; and
`web-hide` demonstrably keeps `diarized` and `inferred` claims out of the
published site.

# 6 — Topics, and the rest

Embedding-based clustering for topic tags. Still assistive: a proposed tag is a
proposal.

# Continuous

- **The archive is never edited.** Any change to that is a design change, not a
  bug fix.
- **Every phase ends in a command transcript** — replayable, undoable.
- **No generative model writes anything that gets published.**
