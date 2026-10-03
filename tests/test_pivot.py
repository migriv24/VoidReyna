"""
The pivot, and the claim that makes it worth having.

okf/concepts/extraction-cases.md walked twenty-two hypothetical harvests and
concluded that every one lands in one of four coordinate systems. This is where
that stops being a table in a document.

**The claim under test is not "the code works".** It is the pivot rule:

    Never write a direct A->B adapter when A->pivot->B exists.

which is only worth obeying if a NEW format costs one lens and inherits the rest.
So: three formats — a budget CSV, a zoning GeoJSON, a meeting WebVTT — that
`emit.py` has never heard of and was not modified for, each composed with the
one shared emitter, each checked against the round-trip law. If the pivot is
real they all pass; if it is decoration, the emitter would have needed teaching.

    python tests/test_pivot.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reyna.archive import Record                                  # noqa: E402
from reyna.emit import (document_lens, emit_trove, parse_trove,   # noqa: E402
                        policy_lens, trove_lens)
from reyna.extract import Document, Provision                     # noqa: E402
from reyna.lens import Lens                                       # noqa: E402
from reyna.pivot import (Cite, Item, Key, Site, Span, Trail,      # noqa: E402
                         Trove, loci_json, loci_of)
from reyna.shapes import (Feature, Geometry, Segment, Table,      # noqa: E402
                          Timeline, geometry_lens, read_csv,
                          read_geojson, read_vtt, table_lens, timeline_lens)

FAILS: list[str] = []


def check(cond, what: str) -> None:
    if not cond:
        FAILS.append(what)
        print(f"FAIL: {what}")


REC = Record(url="https://example.gov/src", fetched_at="2026-08-17T00:00:00Z",
             status=200, content_id="c" * 64, size=1)
ORIGIN = Cite(source_url=REC.url, snapshot=REC.content_id)


# ── 1. every locus survives JSON, including the awkward ones ────────────────

def test_loci() -> None:
    cases = [
        Trail(("3", "3", "1")),
        Trail((), ordinal=4),                       # unnumbered prose
        Span("2025-10-06", Span.OPEN),              # adopted, in force
        Span(Span.UNKNOWN, "2019-12-31"),           # we know the end and not the start
        Span("000000012.500", "000000019.250", frame="media"),   # a timecode
        Site(name="2 mi N of Eugene"),              # NAMED ONLY, ungeocoded
        Site(name="Ward 3", crs="EPSG:4326", form="area",
             shape=(((-123.0, 44.0), (-123.0, 44.1), (-122.9, 44.1),
                     (-123.0, 44.0)),)),
        Site(crs="EPSG:2992", form="volume", dim=3, resolution=5.0,
             shape=((10.0, 20.0, 5.0), (10.0, 20.0, 10.0))),      # voxels
        Site(tiling="h3-r9", cell="8928308280fffff"),             # a hexbin
        Key((("department", "Fire"), ("fund", "General"), ("fy", "2026"))),
    ]
    back = loci_of(loci_json(tuple(cases)))
    check(back == tuple(cases), "all four locus kinds round-trip through JSON")

    # The distinction the whole Span design exists for.
    check(Span("2025-10-06", Span.OPEN) != Span("2025-10-06", Span.UNKNOWN),
          "OPEN and UNKNOWN are different claims about an end date")
    check(Site(name="225 5th St").resolved is False,
          "a named-but-ungeocoded place is a valid, unresolved Site")
    check(Site(tiling="h3-r9", cell="89283").resolved is True,
          "a tiling cell counts as resolved")

    # Trails imply containment; they do not store it.
    tr = Trove(items=[Item("a", "p", loci=(Trail(("3",)),)),
                      Item("b", "p", loci=(Trail(("3", "3")),)),
                      Item("c", "p", loci=(Trail(("3", "3", "1")),))])
    check(tr.parent_of(tr.items[2]).ident == "b", "parent is the longest prefix")
    tr.items.pop(1)   # the document skips a level: 3 -> 3.3.1 with no 3.3
    check(tr.parent_of(tr.items[1]).ident == "a",
          "a skipped level nests to the nearest ancestor rather than orphaning")


# ── 2. the flat/JSON decision on the wire ───────────────────────────────────

def test_wire() -> None:
    """A legible transcript for the ordinary case, JSON only when needed."""
    plain = Trove(origin=ORIGIN, items=[
        Item("p-3-3-1", "provision", fields={"heading": "Notice"},
             loci=(Trail(("3", "3", "1")),))])
    text = emit_trove(plain).text()
    check("set p-3-3-1 number '3.3.1'" in text,
          "an ordinary trail emits the legible flat field, not JSON")
    check("setjson" not in text, "...and no JSON at all")

    rich = Trove(origin=ORIGIN, items=[
        Item("ward-3", "district", fields={"name": "Ward 3"},
             loci=(Site(tiling="h3-r9", cell="8928308280fffff"),
                   Span("2021-01-01", Span.OPEN)))])
    check("setjson ward-3 loci" in emit_trove(rich).text(),
          "a Site forces the whole locus set to JSON")

    # THE ONE THAT MATTERS. An absent `until` already means "indefinitely" to
    # Hormiga's civic model, so a flat form cannot also use it for "unknown".
    unknown = Trove(origin=ORIGIN, items=[
        Item("x", "revision", loci=(Span("2025-01-01", Span.UNKNOWN),))])
    check("setjson x loci" in emit_trove(unknown).text(),
          "an UNKNOWN end refuses the flat form rather than posing as OPEN")
    check(parse_trove(emit_trove(unknown).text()).items[0].loci
          == (Span("2025-01-01", Span.UNKNOWN),),
          "...and reads back as UNKNOWN, not as OPEN")

    # Two citations: the flat pair still carries the first, so an existing
    # consumer keeps working, and the full list rides alongside.
    two = Trove(origin=ORIGIN, items=[
        Item("claim", "statement", fields={"text": "hi"},
             cites=(Cite("https://a.gov", "a" * 64, "verbatim", locator="p. 4"),
                    Cite("https://b.gov", "b" * 64, "model:needle@1.2")))])
    t2 = emit_trove(two).text()
    check("set claim source_url 'https://a.gov'" in t2,
          "a multi-sourced claim still emits a flat first citation")
    check(parse_trove(t2).items[0].cites == two.items[0].cites,
          "...and both citations survive")

    check(trove_lens().check([plain, rich, unknown, two]).ok,
          "every wire form round-trips")


# ── 3. three formats the emitter has never heard of ─────────────────────────

BUDGET_CSV = """department,fund,fy,amount,fte
Fire,General,2026,"12450000",58.5
Police,General,2026,"18990000",96
Library,General,2026,"3120000",22.25
Fire,Capital,2026,"2000000",0
"""

ZONING_GEOJSON = """{"type":"FeatureCollection","features":[
 {"type":"Feature","properties":{"zone":"R-1","name":"Low Density"},
  "geometry":{"type":"Polygon","coordinates":[
    [[-123.02,44.04],[-123.02,44.06],[-122.98,44.06],[-123.02,44.04]],
    [[-123.01,44.05],[-123.005,44.05],[-123.01,44.052],[-123.01,44.05]]]}},
 {"type":"Feature","properties":{"zone":"C-2","name":"Main Street"},
  "geometry":{"type":"LineString","coordinates":[[-123.0,44.05],[-122.9,44.05]]}},
 {"type":"Feature","properties":{"zone":"PT","name":"City Hall"},
  "geometry":{"type":"Point","coordinates":[-123.0,44.05,142.3]}},
 {"type":"Feature","properties":{"zone":"??","name":"Unmapped Annex"},
  "geometry":{"type":"GeometryCollection","geometries":[]}}]}"""

MINUTES_VTT = """WEBVTT

1
00:00:12.500 --> 00:00:19.250
<v Mayor>The meeting will come to order.
Roll call, please.

2
00:00:19.250 --> 00:00:24.000
<v Recorder>Councilor Ruiz? Present.

3
00:01:41.000 --> 00:01:52.750
Motion carries, four to one; it don't need a second reading.
"""


def test_formats() -> None:
    # ── Table (catalogue cases 9-14) ────────────────────────────────────────
    tbl = read_csv(BUDGET_CSV, dims=("department", "fund", "fy"),
                   name="Adopted Budget FY2026",
                   units={"amount": "USD", "fte": "FTE"})
    check(tbl.measures == ("amount", "fte"),
          "whatever is not a dimension is a measure")
    check(len(tbl.rows) == 4, "four budget rows")
    tl_ = table_lens(ORIGIN)
    check(tl_.check([tbl]).ok, "Table <-> Trove is lossless")
    check(tl_.compose(trove_lens()).check([tbl]).ok,
          "Table -> Trove -> transcript round-trips (the emitter was not touched)")
    tv = tl_.forward(tbl)
    obs = tv.of_kind("observation")
    check(obs[0].units.get("amount") == "USD",
          "units ride with the observation - a budget in thousands is a real hazard")
    check(obs[0].ident != obs[3].ident and "fire" in obs[0].ident,
          "the ident is built from the CELL, so a reordered re-harvest updates in place")

    # ── Geometry (cases 15-19, and Q32 verbatim) ────────────────────────────
    geo = read_geojson(ZONING_GEOJSON, name="Zoning 2026", ident_field="zone")
    forms = [f.site.form for f in geo.features]
    check(forms == ["area", "path", "point", ""],
          f"polygon/line/point read, unknown geometry left unresolved (got {forms})")
    check(geo.features[2].site.dim == 3, "a 3-D point is recognised as 3-D")
    check(geo.features[3].site.resolved is False
          and geo.features[3].site.name == "Unmapped Annex",
          "an unreadable geometry becomes a NAMED site, not an error and not a guess")
    check(len(geo.features[0].site.shape) == 2,
          "a polygon keeps its hole")
    gl = geometry_lens(ORIGIN)
    check(gl.check([geo]).ok, "Geometry <-> Trove is lossless")
    check(gl.compose(trove_lens()).check([geo]).ok,
          "Geometry -> Trove -> transcript round-trips")

    # The voxel case the author asked about, which is why `form` is not an enum
    # of two: it costs nothing to carry and a rewrite to add later.
    vox = Geometry(name="Envelope", features=[Feature(
        "block-a", Site(crs="EPSG:2992", form="volume", dim=3, resolution=5.0,
                        shape=((10.0, 20.0, 5.0), (10.0, 20.0, 10.0))))])
    check(gl.compose(trove_lens()).check([vox]).ok,
          "a VOXEL layer reaches a transcript through the same unmodified pivot")

    # ── Timeline (cases 5, 7, 8, 22) ────────────────────────────────────────
    tml = read_vtt(MINUTES_VTT, name="Council 2026-08-04")
    check(len(tml.segments) == 3, f"three cues (got {len(tml.segments)})")
    check(tml.segments[0].speaker == "Mayor" and tml.segments[1].speaker == "Recorder",
          "the voice tag is captured as a LABEL")
    check(abs(tml.segments[2].end - 112.75) < 1e-6, "timecodes parse to seconds")
    ml = timeline_lens(ORIGIN)
    check(ml.check([tml]).ok, "Timeline <-> Trove is lossless")
    check(ml.compose(trove_lens()).check([tml]).ok,
          "Timeline -> Trove -> transcript round-trips (apostrophes and all)")

    seg_items = ml.forward(tml).of_kind("utterance")
    check("speaker_label" in seg_items[0].fields,
          "a speaker is a label in its own field...")
    check(not any(r for _i in seg_items for r in _i.refs),
          "...and never an edge to a person: identifying a voice is a human's act")
    sp = seg_items[0].locus("span")
    check(sp.frame == "media",
          "a transcript's span is in MEDIA time, not pretending to be a date")
    check(sp.start < sp.end and seg_items[0].fields["text"].startswith("The meeting"),
          "fixed-width timecodes still compare in the right order as strings")


# ── 4. composition, on the real document ────────────────────────────────────

def sample_doc() -> Document:
    return Document(title="Test Policies", provisions=[
        Provision("1", "Authority", "Adopted under the Charter, Chapter IV."),
        Provision("2", "Officers", ""),
        Provision("2.1", "Election of President",
                  "The Council shall elect one of its members as President.",
                  parent="2"),
        Provision("2.2.1", "Limits",
                  "They don't vote; the Mayor's ruling stands.", parent="2"),
    ])


def test_composition() -> None:
    doc_l = document_lens(REC, policy_name="tp", effective="2025-10-06")
    check(doc_l.check([sample_doc()]).ok, "Document <-> Trove is lossless")

    whole = policy_lens(REC, policy_name="tp", effective="2025-10-06")
    check(whole.check([sample_doc()]).ok,
          "and so is the composition, which is what the pivot rule promises")
    # Both legs are named in the composite's label - Void Core's `compose`
    # joins them with an arrow, which reads as the pipeline it is.
    check("document<->trove" in whole.label and "trove<->transcript" in whole.label,
          f"policy_lens really is a composition (label: {whole.label})")

    # Losslessness composes — but only because both legs are lossless. A lossy
    # leg must poison the composite, or the rule is not an argument.
    lossy = Lens(lambda d: Document(title=d.title, provisions=[
        Provision(p.number, p.heading, "", p.parent) for p in d.provisions]),
        lambda d: d, normalize=doc_l.normalize, label="drops-text")
    check(not lossy.compose(whole).check([sample_doc()]).ok,
          "a lossy leg poisons the composite")

    # Hormiga still gets the transcript it already reads.
    text = whole.forward(sample_doc())
    check(text.count("rune new provision ") == 4, "four provisions")
    check(text.count("rune new revision ") == 3,
          "three revisions - a bare heading asserts nothing")
    runes = [l.split()[3] for l in text.splitlines() if l.startswith("rune new ")]
    cited = {l.split()[1] for l in text.splitlines()
             if l.startswith("set ") and l.split()[2] == "source_url"}
    check(set(runes) == cited, "EVERY rune carries its citation")
    check("link tp-2-2-1 tp-2 --relation part-of" in text,
          "a skipped level still links to its nearest real ancestor")


def main() -> int:
    for t in (test_loci, test_wire, test_formats, test_composition):
        t()
    if FAILS:
        print(f"\n{len(FAILS)} check(s) failed")
        return 1
    print("OK - four coordinate systems, four formats, one unmodified emitter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
