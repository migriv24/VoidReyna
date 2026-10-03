"""
reyna/pivot.py — the pivot. One structure every source format maps into.

WHY THIS EXISTS, AND WHAT IT CORRECTS. `emit.policy_lens` named `Document` as
"the PIVOT". That was defensible with one format and is **wrong** with more than
one: a pivot is what all the legs meet at, and `Document` is a leg. The
correction came from writing out twenty-two hypothetical harvests
(okf/concepts/extraction-cases.md) and noticing that a set of minutes, a budget
table and a zoning map are not documents and never will be.

THE FINDING THE CATALOGUE PRODUCED. Sort those twenty-two by *what question you
ask about an item's position* and there are exactly four answers:

    Trail   what is this inside of?          a position in a containment order
    Span    when, and for how long?          an instant or interval in time
    Site    where, and what is near it?      a position or region in space
    Key     which cell of the cube?          a point in named dimensions

That is not an invented abstraction. **It is read off the consumer.** Hormiga's
Allomone ships 22 domain predicates and they partition exactly this way — `under`
is Trail, `before`/`after`/`overdue`/`upcoming`/`undated` are Span,
`near`/`near-rune`/`located` are Site, `field`/`field-has`/`role` are Key. The
app has been asking questions in four coordinate systems since before this file
existed; this names the one that was already load-bearing at the far end.

LOCI ARE A SET, NOT A CHOICE. A council district redrawn every ten years is a
region **and** an interval, and neither is optional — a 2011 district and a 2021
district can share a name and share nothing else. A calendar entry is a time and
a place. A hex-binned service map is a cell and a period. Six of the twenty-two
cases need more than one coordinate, so `Item.loci` is a tuple and any design
that made them exclusive would fail on redistricting, which is about as ordinary
as civic data gets.

WHAT IS DELIBERATELY *NOT* A COORDINATE. A **graph** is the destination, not a
source shape — items point at each other through `Item.refs`, which emit as
links, and the interesting graph structure is the consumer's model rather than
something extraction discovers. Case 21 (a citation network) was the check on
that, and it held.

PURE. No I/O, no clock, no model. Everything here is a plain value.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional

# ── citation ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Cite:
    """Where a claim came from, and how much weight it can bear.

    `snapshot` is an archive content id, so a reader can pull the exact bytes
    back and check the claim — and can tell whether the live document still says
    what we cited.

    `locator` is the part a *person* uses: "p. 14", "row 218", "00:12:31". A
    citation nobody can follow by hand is a citation in name only.

    `method` is the annotation
    okf/concepts/foundations.md §3 argues should eventually be a provenance
    semiring. It is a plain string until a claim is derived from two sources at
    once, at which point hand-written propagation rules start going wrong
    silently and the algebra earns its place. `verbatim` means the source says
    this in so many words, and it is the default because it is the only kind
    phase 1 produces.

    `withheld` records that the source **exists and was redacted** — a released
    records request with black bars is a different fact from a record we never
    saw, and an archive that cannot say so is lying by omission.
    """

    source_url: str = ""
    snapshot: str = ""
    method: str = "verbatim"
    locator: str = ""
    withheld: bool = False

    def json(self) -> dict:
        d = {"source_url": self.source_url, "snapshot": self.snapshot,
             "method": self.method}
        if self.locator:
            d["locator"] = self.locator
        if self.withheld:
            d["withheld"] = True
        return d

    @staticmethod
    def of(d: dict) -> "Cite":
        return Cite(source_url=d.get("source_url", ""),
                    snapshot=d.get("snapshot", ""),
                    method=d.get("method", "verbatim"),
                    locator=d.get("locator", ""),
                    withheld=bool(d.get("withheld", False)))


# ── the four coordinates ────────────────────────────────────────────────────


class Locus:
    """A position. One of exactly four kinds; see the module docstring."""

    kind = ""

    def json(self) -> dict:  # pragma: no cover - overridden
        raise NotImplementedError


@dataclass(frozen=True)
class Trail(Locus):
    """A position in a containment order — "3.3.1", or the 4th item of the 2nd.

    Named for the thing an ant lays down: an ordered sequence of steps that gets
    you to a place. Not called `Path` because that name is `pathlib`'s in every
    file that also touches disk, and a footgun in a foundation is expensive.

    `parts` is **as the document wrote it**, not normalized. A document that
    numbers its sections `IV` then `A` then `2` is telling us something about
    itself, and rewriting that into integers is the kind of tidy-up that loses a
    fact nobody asked us to lose.

    `ordinal` positions an item among its siblings when the source does not
    number them at all — the 3rd unnumbered paragraph under §4 — so that ordered
    prose is representable without inventing numbers for it.
    """

    kind = "trail"
    parts: tuple[str, ...] = ()
    ordinal: int = 0

    @property
    def number(self) -> str:
        return ".".join(self.parts)

    def parent(self) -> Optional["Trail"]:
        return Trail(self.parts[:-1]) if len(self.parts) > 1 else None

    def json(self) -> dict:
        d = {"kind": "trail", "parts": list(self.parts)}
        if self.ordinal:
            d["ordinal"] = self.ordinal
        return d


@dataclass(frozen=True)
class Span(Locus):
    """An instant or an interval. **Valid time** — when the world was like this.

    NOT transaction time. When we *learned* it lives on the archive `Record`'s
    `fetched_at`, and keeping the two axes in different objects is the whole of
    this project's answer to bitemporality: they are never in the same field, so
    they can never be confused for one another.

    THREE STATES PER BOUND, and collapsing any two of them is a lie:

        an ISO date   we know it
        OPEN ("")     unbounded on that side — "until further notice"
        UNKNOWN ("?") we do not know, and are not guessing

    The default is UNKNOWN, not OPEN, because an unstated bound is a thing we
    did not see rather than a thing that has no end. An emitter that means "in
    force indefinitely" has to say OPEN on purpose — which `emit` does for an
    adopted policy, since that genuinely is what adoption means, and it should
    be a visible decision rather than a default nobody chose.

    `frame` says what the bounds are measured against. `utc` means ISO dates or
    datetimes. `media` means seconds from the start of a recording, which is
    what a transcript segment actually knows — a timecode is *not* a date, and
    turning one into the other needs a fact (when the recording started) that
    the transcript does not contain. Carrying the frame keeps the two from being
    silently added together; a meeting transcript whose segments claim to be
    dated in the year 1970 is the failure this prevents.
    """

    kind = "span"
    OPEN = ""
    UNKNOWN = "?"
    start: str = UNKNOWN
    end: str = UNKNOWN
    frame: str = "utc"

    def json(self) -> dict:
        d = {"kind": "span", "start": self.start, "end": self.end}
        if self.frame != "utc":
            d["frame"] = self.frame
        return d


@dataclass(frozen=True)
class Site(Locus):
    """Where in the *world* — as opposed to Void Core's `place`.

    ⚠ **`place`/`placement` in Void Core is the VIEW SLICE** (SPEC §3.2, §6): a
    rune's x/y on a canvas, carved out of undo on purpose. It has nothing to do
    with geography and a Site must never emit it. Two different senses of "where"
    in one system is a real hazard, so this type is named to stay clear of it and
    its fields all carry a `site_` prefix on the wire.

    THREE RESOLUTIONS, and the ability to hold the *weakest* is the point:

      * **named only** — "225 5th St", "2 mi N of Eugene". This is how the most
        common spatial datum actually arrives (a permit, a museum record), and a
        design where a place must be a number pair cannot represent it at all.
        Geocoding is then a *holiday*: an effectful crossing that fills in
        `shape`, leaving `name` exactly as the source wrote it.
      * **a cell in a tiling** — an H3 index, a geohash, `precinct:lane-or-041`.
        Cheap to store as an id and ruinous to store as a re-derived polygon,
        because the polygon is the tiling's business and it changes.
      * **explicit geometry** — `shape` reads according to `form`:

            point    ((x, y[, z]),)
            path     ((x, y), …)                 an open linestring
            area     (outer_ring, hole, hole, …)  each a tuple of points
            volume   ((x, y, z), …)               cell centres at `resolution`

    `dim` is 2 or 3 and `form` includes `volume` because the author asked the
    right question — *what if the city publishes something voxel-based?* — and a
    pivot that hard-codes two dimensions answers it with a rewrite.
    """

    kind = "site"
    name: str = ""
    crs: str = ""            # "EPSG:4326"; "" when there is no geometry to place
    form: str = ""           # point | path | area | volume | ""
    shape: tuple = ()
    dim: int = 2
    resolution: float = 0.0  # voxel/cell edge length, in `crs` units
    tiling: str = ""         # "h3-r9", "geohash", "precinct:lane-or"
    cell: str = ""

    @property
    def resolved(self) -> bool:
        """False for a place we can name but not draw. Not an error — a state."""
        return bool(self.shape) or bool(self.cell)

    def json(self) -> dict:
        d: dict = {"kind": "site"}
        for k, v in (("name", self.name), ("crs", self.crs), ("form", self.form),
                     ("tiling", self.tiling), ("cell", self.cell)):
            if v:
                d[k] = v
        if self.shape:
            d["shape"] = _listify(self.shape)
            d["dim"] = self.dim
        if self.resolution:
            d["resolution"] = self.resolution
        return d


@dataclass(frozen=True)
class Key(Locus):
    """A point in a product of named dimensions — the cell of a cube.

    `(("department", "Fire"), ("fund", "General"), ("fy", "2026"))`, which is a
    budget line, an election result, a salary row and a permit count. The
    catalogue's largest family by far, and the one the design had nothing for.

    **The dimensions are the coordinate; the measure is the payload.** The
    amount lives in `Item.fields` with its unit in `Item.units`, not here —
    because "which cell" and "what is in it" are different questions, and a
    budget cube with two measures per cell is ordinary.

    Order is preserved: dimension order is how a source presents its cube, and
    it is free to keep.
    """

    kind = "key"
    dims: tuple[tuple[str, str], ...] = ()

    def get(self, name: str) -> str:
        return next((v for k, v in self.dims if k == name), "")

    def json(self) -> dict:
        return {"kind": "key", "dims": [list(d) for d in self.dims]}


def _listify(x):
    """Tuples to lists, recursively — JSON has no tuple, and round-tripping
    through it must not depend on which one we happened to build with."""
    if isinstance(x, (tuple, list)):
        return [_listify(i) for i in x]
    return x


def _tuplify(x):
    if isinstance(x, list):
        return tuple(_tuplify(i) for i in x)
    return x


def locus_of(d: dict) -> Locus:
    """Rebuild a locus from its JSON. The backward half of every locus's law."""
    k = d.get("kind", "")
    if k == "trail":
        return Trail(tuple(d.get("parts", [])), int(d.get("ordinal", 0)))
    if k == "span":
        return Span(d.get("start", Span.UNKNOWN), d.get("end", Span.UNKNOWN),
                    d.get("frame", "utc"))
    if k == "site":
        return Site(name=d.get("name", ""), crs=d.get("crs", ""),
                    form=d.get("form", ""), shape=_tuplify(d.get("shape", [])),
                    dim=int(d.get("dim", 2)),
                    resolution=float(d.get("resolution", 0.0)),
                    tiling=d.get("tiling", ""), cell=d.get("cell", ""))
    if k == "key":
        return Key(tuple((a, b) for a, b in d.get("dims", [])))
    raise ValueError(f"unknown locus kind: {k!r}")


# ── items and troves ────────────────────────────────────────────────────────


@dataclass
class Item:
    """One thing found in a source: an identity, where it sits, what it says.

    `kind` is the **glyph** it will become. Extraction chooses it, because the
    source is what knows whether this is a provision or a vote; nothing
    downstream can recover that.

    `refs` are named relations to other items by ident — `("moved-by", "…")`,
    `("amends", "…")`. They emit as links, and they are how the catalogue's
    genuinely relational cases (a ledger's payer and payee, a motion's mover)
    are carried without pretending a relation is a coordinate.

    `units` maps a field name to its unit. Small, and it earns its keep the
    first time a budget publishes in thousands: "was that dollars or thousands
    of dollars" is a real and expensive class of error in exactly the family of
    sources with the most rows.
    """

    ident: str
    kind: str
    fields: dict[str, str] = field(default_factory=dict)
    loci: tuple[Locus, ...] = ()
    cites: tuple[Cite, ...] = ()
    refs: tuple[tuple[str, str], ...] = ()
    units: dict[str, str] = field(default_factory=dict)

    def locus(self, kind: str) -> Optional[Locus]:
        """The first locus of a kind, or None. Items usually have zero or one of
        each; a source with two Spans on one item is describing two things."""
        return next((l for l in self.loci if l.kind == kind), None)

    @property
    def trail(self) -> Optional[Trail]:
        l = self.locus("trail")
        return l if isinstance(l, Trail) else None


@dataclass
class Trove:
    """Everything one extraction found, plus where it all came from.

    Named for what it is: a collection of things found somewhere. Not `Corpus`,
    which would bias the whole design back toward text, which is the mistake
    this file exists to undo.

    `origin` is the trove-wide citation. An item with no `cites` of its own
    inherits it, so **forgetting to cite is not reachable** — the same discipline
    `Transcript.cite` enforced for one format, generalised.

    THERE IS DELIBERATELY NO `title`. It was here for one draft and removed,
    because a command transcript is a list of assertions and there is no rune a
    trove-level label belongs to — so it could not survive `emit`, and keeping it
    would have meant a field that silently does not round-trip. Every name is an
    **item** instead: a policy's title rides on the policy, a dataset's on a
    `dataset` item. A field the wire cannot carry does not belong in the pivot,
    and normalizing the loss away would have been the polite version of hiding
    it.
    """

    items: list[Item] = field(default_factory=list)
    origin: Cite = field(default_factory=Cite)

    def add(self, item: Item) -> Item:
        self.items.append(item)
        return item

    def by_ident(self) -> dict[str, Item]:
        return {i.ident: i for i in self.items}

    def of_kind(self, kind: str) -> list[Item]:
        return [i for i in self.items if i.kind == kind]

    def cites_for(self, item: Item) -> tuple[Cite, ...]:
        return item.cites or (self.origin,)

    # ── the containment relation, DERIVED from trails ───────────────────────
    def parent_of(self, item: Item) -> Optional[Item]:
        """The item whose trail is the longest proper prefix of this one's.

        Structural, so a document that skips a level (3 → 3.3.1 with no 3.3)
        nests sensibly instead of orphaning the child — the same rule the
        document parser used, lifted here because it is a fact about trails and
        not about PDFs.

        This is *derived*. The trail is what the source stated and is stored;
        the parent link is a view of it. That ordering was the author's
        correction on the civic model — containment is a link, the tree is a
        projection — and it is the same correction one level down.
        """
        t = item.trail
        if t is None or len(t.parts) < 2:
            return None
        have = {i.trail.number: i for i in self.items
                if i.trail is not None and i is not item}
        for cut in range(len(t.parts) - 1, 0, -1):
            cand = ".".join(t.parts[:cut])
            if cand in have:
                return have[cand]
        return None


# ── the wire form of a locus set ────────────────────────────────────────────
#
# Loci travel as ONE json field rather than as scattered flat fields. The
# alternative — `from`/`until`/`site_name`/… as separate `set` commands — was
# tried on paper and loses the thing that matters: an item with two Spans, or a
# Site *and* a Span, flattens into a shape you cannot read back. Six of the
# twenty-two catalogue cases need exactly that.
#
# The flat fields are emitted TOO, by `emit`, for the ones a consumer queries
# directly (`from`, `until`, `number`). Duplication on the wire is cheap; an
# unrecoverable coordinate is not.

def loci_json(loci: tuple[Locus, ...]) -> str:
    return json.dumps([l.json() for l in loci], separators=(",", ":"))


def loci_of(s: str) -> tuple[Locus, ...]:
    return tuple(locus_of(d) for d in json.loads(s)) if s else ()
