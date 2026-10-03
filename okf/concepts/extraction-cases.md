---
type: Reference
title: Extraction cases — twenty-two sources Reyna must survive
description: "A deliberately broad catalogue of hypothetical harvests, civic and not, used as a stress test on the architecture rather than as a roadmap. Each case names what arrives, what shape it is, and what breaks today. The finding: every case lands in one of four coordinate systems, which is what the pivot must be built from."
tags: [status:current, audience:dev, confidence:asserted]
timestamp: 2026-08-17T00:00:00Z
---

**This is not a roadmap.** Nothing here is promised, and most of it will never
be built. It is a **stress test**: a design that only fits the one document we
have already parsed has not been shown to fit anything, and the cheapest moment
to discover that is before the second source arrives, not during it.

The method is the one the author asked for: enumerate a wide spread of
*hypothetical* extractions — deliberately including several that have nothing to
do with a city council — and check the architecture against each. A case that
breaks something is worth more than a case that fits.

**The finding is at the bottom** and it is the reason this page exists: all
twenty-two land in **one of four coordinate systems**, and the current pivot
(`Document`) is only one of them. That is a real gap in the foundations, found
here rather than in six months.

# How to read a row

| column | meaning |
|---|---|
| **arrives as** | the bytes at the boundary — what `harvest`/`ingest` will hold |
| **shape** | the structure inside, once extracted |
| **breaks** | what in `reyna/` today does not cope |

---

# A. Normative text — the case we have already done

### 1. A city's operating policies (PDF)
*Built.* Springfield's, 150 provisions, nested, dated. **Shape:** nested ordered
text. **Breaks:** nothing — this is the case the code was written from, which is
exactly why it proves nothing on its own.

### 2. A municipal code / ordinance corpus (HTML, thousands of pages)
Arrives as many pages, one per chapter, cross-referencing each other and the
state statutes. **Shape:** the same nested ordered text — *but spread across
documents*, with the containment relation crossing file boundaries.
**Breaks:** (a) there is no **discovery** step, so "which pages exist" is
unanswerable; (b) `Document.provisions` assumes one document holds its own
tree, and here a provision's parent lives in another fetch.

### 3. State statutes referenced by a local ordinance (PDF/HTML, another body)
**Shape:** nested ordered text again. **Breaks:** nothing structurally — and
that is the point. A *reference* from a local provision to `ORS 192.610` is a
link between two items in two troves, which is a fact about identity, not about
extraction. It belongs to the consumer.

### 4. A platform's terms of service, versioned over years
Deliberately non-civic. **Shape:** nested ordered text with a strong temporal
axis — the interesting object is the *diff*, and the archive already holds every
capture. **Breaks:** nothing today; it is the case that most wants
[delta lenses](foundations.md#2-delta-lenses--the-upgrade-re-harvesting-will-demand),
and a good argument that the upgrade is not civic-specific.

---

# B. Proceedings — what a body did, in order

### 5. Meeting minutes (PDF)
The phase-2 target. **Shape:** *not* a document, though it looks like one. It is
a **chronology**: call to order, roll, then a sequence of motions each with a
mover, a seconder, and a tally by name. The nesting is incidental; the ordering
and the *timing* are the content. **Breaks:** `parse_numbered_document` would
find agenda numbers and produce provisions, which would be a category error
recorded as data. There is no shape for "an ordered sequence of events, each
with participants".

### 6. An agenda packet (PDF, 41 MB, a hundred attachments concatenated)
**Shape:** a *container* — many documents in one file, each a different shape.
**Breaks:** R5 (too slow), and more fundamentally: extraction currently returns
**one** structure per blob. A container returns *many*, of *different kinds*.

### 7. A meeting video's transcript (VTT/SRT, or produced by a local model)
**Shape:** timed segments — `(start, end, text, maybe a speaker)`. **Breaks:**
no shape for intervals. Also the first case where a **method** annotation is
load-bearing: `human-transcribed` and `model-transcribed v3.1` are not the same
claim, and [attribution](attribution.md) says so, but `Record` has nowhere to put
it.

### 8. A council calendar feed (iCal)
**Shape:** intervals with a place attached. **Breaks:** intervals again; and it
is the first case where an item has **two** coordinates at once (when *and*
where), which single-shape thinking cannot express.

---

# C. Tabular — the largest family, and absent from the design

### 9. An adopted budget (PDF with tables, or XLSX)
**Shape:** observations — `(department, fund, fiscal-year) → amount, currency`.
**Breaks:** everything. There is no table shape, no notion of a measure, no
units. Extracting a table out of a *PDF* is separately hard (R5/R6 territory).

### 10. Public employee salary disclosures (CSV)
**Shape:** the same observations, keyed by person instead of department.
**Breaks:** same. Also the first case that is **person-level public data**, where
the publishable line has to be drawn deliberately rather than assumed.

### 11. Campaign finance filings (ORESTAR bulk CSV)
**Shape:** a ledger — `(date, payer, payee, amount, purpose)`. A ledger is a
table whose rows are events, so this needs no new shape beyond tables — but its
rows are simultaneously **temporal** and **relational**, which is the multiple-
coordinate problem again.

### 12. Election results by precinct (CSV)
**Shape:** `(contest, candidate, precinct) → votes`. **Breaks:** tables, plus:
`precinct` is a *geographic* key that only becomes geography when joined to a
boundary file. The join is the interesting operation and there is nowhere to
express it.

### 13. Building permits / code-enforcement cases (CSV or an ArcGIS endpoint)
**Shape:** events keyed to an **address**. **Breaks:** an address is a place
that has not been resolved to a coordinate yet. Any design where "a place" must
be a number pair cannot hold the most common form a place actually arrives in.

### 14. A transit schedule (GTFS — a zip of CSVs)
Deliberately non-civic-government. **Shape:** tables *and* geometry *and*
recurring intervals, in one archive, referencing each other by id. **Breaks:**
all three, at once. Genuinely the hardest case in the catalogue, which is why it
is a good one to design against.

---

# D. Spatial — the case Q32 was opened for

### 15. Zoning districts (GeoJSON / shapefile)
**Shape:** polygons with attributes. **Breaks:** no geometry shape at all. This
is the open question verbatim.

### 16. Parcel boundaries with owner attributes
**Shape:** the same polygons, and the first where a spatial join is the point —
"which zoning district contains this parcel".

### 17. A council-district map, redrawn every ten years
**Shape:** polygons **with a validity interval**. Space and time, together,
non-optionally: a 2011 district and a 2021 district can share a name and share
nothing else. Any spatial design without time in it is wrong for this case, and
this case is not exotic.

### 18. A city's 3-D zoning envelope, or a lidar-derived model
The author's hypothetical, and the reason the pivot rule was invoked: *what if
the city publishes something voxel-based?* **Shape:** volumes. **Breaks:** any
design that hard-codes two dimensions.

### 19. A hex-binned heat map of service requests
**Shape:** cells in a tiling (H3, geohash, quarter-section). Not a polygon — an
*index* into a known partition. Cheap to store as a cell id, ruinous to store as
a re-derived polygon.

---

# E. Beyond the city — generality checks

### 20. A herbarium or museum catalogue (JSON API, paginated)
**Shape:** records with a collection date, a collector, and a *place* that is
often a text description ("2 mi N of Eugene"). Same unresolved-place problem as
case 13, arrived at from a completely different domain — which is decent
evidence the problem is real rather than an artefact of one city's data.

### 21. A scientific corpus with citations (PDF + a metadata API)
**Shape:** documents plus a citation graph. **Breaks:** nothing new — the graph
is the *consumer's* model, and this confirms that "graph" is a destination and
not a source shape, which is a distinction worth having made explicitly.

### 22. Emails released under a public-records request (mbox on a CD)
**Shape:** timestamped items with participants and threading — a chronology
again. **Breaks:** nothing at the boundary (`ingest` already handles evidence
that arrives by post rather than HTTP, which was built for exactly this). It is
the strongest case for **method and clearance annotations**: a records release
is usually partly redacted, and "this was withheld" is a fact worth recording.

---

# The finding

Twenty-two cases. Sort them by *what question you ask of an item's position*,
and there are **four** answers and no more:

| coordinate | the question it answers | cases |
|---|---|---|
| **Path** — a position in a containment order | *what is this inside of?* | 1–4, 6, 21 |
| **Span** — an instant or interval in time | *when, and for how long?* | 4, 5, 7, 8, 11, 17, 20, 22 |
| **Place** — a position or region in space | *where, and what is near it?* | 8, 12–20 |
| **Key** — a point in a product of named dimensions | *which cell of the cube?* | 9–14, 19, 20 |

Two things make this more than a tidy table.

**First, it is not invented — it is read off the consumer.** Hormiga's Allomone
already ships 22 domain predicates, and they partition exactly this way:
`under` is Path; `before`/`after`/`overdue`/`upcoming`/`undated` are Span;
`near`/`near-rune`/`located` are Place; `field`/`field-has`/`role` are Key. The
app has been asking questions in four coordinate systems since before this page
existed. Building the pivot from the same four is not a new abstraction, it is
finally naming one that was already load-bearing at the other end.

**Second, several cases need more than one at a time** — 8, 11, 14, 17, 19, 20.
So the shapes cannot be alternatives. An item carries *a set of loci*, not one,
and a design that makes them exclusive fails on a redistricting map, which is
about as ordinary as civic data gets.

## What this changes

1. **`Document` is not the pivot; it is a *format*.** Naming it the pivot was
   defensible when there was one leg and is wrong now. The pivot is the thing all
   four formats map into — see [pivot](pivot.md).
2. **Place must admit the unresolved.** Cases 13 and 20 arrive with an address or
   a phrase, not a coordinate. Geocoding is a *holiday*, so an ungeocoded place
   is a valid Place with a name and no geometry — otherwise the most common form
   of the most common spatial datum cannot be represented at all.
3. **Span must admit the open-ended and the unknown.** "From 2025-10-06 until
   further notice" is the normal state of an adopted policy.
4. **Extraction must dispatch on content type and may return many troves.**
   Case 6 (a container) and case 14 (a zip of related tables) both break the
   current one-blob-one-structure assumption.
5. **Discovery is missing and is structural, not a phase-2 chore.** Cases 2, 6,
   14 and 20 all fail at "which URLs exist", and each fails differently: a
   sitemap, an index page, a zip manifest, an API cursor. That is a `Source`
   abstraction with `discover()`, and it is the honest reading of the phase-2
   blocker already in the roadmap.
6. **Citations need `method`, and sometimes more than one.** Cases 7, 20 and 22
   all produce claims whose trustworthiness depends on *how* they were derived.
   This is where [provenance semirings](foundations.md#3-provenance-semirings--one-algebra-for-where-from-how-and-may-we-publish)
   stop being a research note.

## What it does not change

The boundary is fine. `harvest` + `archive` + `ingest` took cases 20 and 22
without modification, and the archive-first rule paid for itself again: every
one of these cases will be extracted wrongly at first, and every one of them can
be re-extracted from bytes we already hold.
