"""
reyna/shapes.py — the three source formats the catalogue found missing, and
their lenses into the pivot.

`Document` already existed (extract.py) and covers six of the twenty-two cases
in okf/concepts/extraction-cases.md. These three cover the rest:

    Table      cases 9-14, 19, 20   budgets, salaries, filings, results, GTFS
    Geometry   cases 12, 15-19      zoning, parcels, districts, voxels, hexbins
    Timeline   cases 5, 7, 8, 22    minutes, transcripts, calendars, mail

EACH IS A FORMAT, NOT A PIVOT. Every one of them maps into `Trove`, and the
whole payoff of that arrangement is downstream: `emit` was written once, against
the pivot, and none of these three files had to teach it anything. That is the
pivot rule (foundations §1a) collecting on its promise rather than restating it.

THE PARSERS ARE SMALL ON PURPOSE. Each is enough to prove its format really
lands in the pivot — a real CSV, a real GeoJSON, a real WebVTT — and no more.
A catalogue whose claims are only asserted is worth much less than one where
three of them are executed by a test, and much less work than four production
importers nobody has a use for yet.

PURE. No I/O, no clock, no model.
"""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass, field
from typing import Optional

from .lens import Lens
from .pivot import Cite, Item, Key, Site, Span, Trove

# ── a dataset's name, as an ITEM ────────────────────────────────────────────
#
# `Trove` has no `title`, on purpose (see its docstring): a command transcript
# carries assertions, and there is no rune a trove-level label belongs to. So a
# format that has a name puts it on a `dataset` item — the same move the document
# leg already makes with the policy's title, and the reason all three of these
# formats survive the round trip through a transcript rather than quietly
# shedding their name on the way.

_DATASET = "dataset"


def _name_item(tr: Trove, name: str) -> None:
    if name:
        tr.add(Item(ident=_slug(name) or _DATASET, kind=_DATASET,
                    fields={"title": name}))


def _name_of(tr: Trove) -> str:
    items = tr.of_kind(_DATASET)
    return items[0].fields.get("title", "") if items else ""


# ── Table — observations in a cube ──────────────────────────────────────────


@dataclass
class Table:
    """Rows over named columns, split into **dimensions** and **measures**.

    That split is the entire content of the type and it is not bookkeeping: a
    budget row's `department` says *which cell*, and its `amount` says *what is
    in the cell*. Conflate them and "total the Fire department across funds"
    stops being expressible, which is the only question anyone asks of a budget.

    `units` maps a measure to its unit. Optional, and the first thing to regret
    omitting: a budget published in thousands and a budget published in dollars
    are the same table with a factor of a thousand between them, and nothing in
    the numbers says which you have.
    """

    name: str = ""
    dims: tuple[str, ...] = ()
    measures: tuple[str, ...] = ()
    rows: list[dict[str, str]] = field(default_factory=list)
    units: dict[str, str] = field(default_factory=dict)

    def key_of(self, row: dict[str, str]) -> Key:
        return Key(tuple((d, row.get(d, "")) for d in self.dims))


def read_csv(text: str, dims: tuple[str, ...], *, name: str = "",
             units: Optional[dict[str, str]] = None) -> Table:
    """A CSV into a Table. Whatever is not a dimension is a measure.

    The caller names the dimensions, and that is deliberate: which columns are
    coordinates is a **judgement about the source**, not something a parser can
    read off the bytes. Guessing it is how an importer silently turns a measure
    into a coordinate and produces a cube with one row per cell.
    """
    rd = csv.DictReader(io.StringIO(text))
    cols = tuple(rd.fieldnames or ())
    rows = [{k: (v or "").strip() for k, v in r.items() if k} for r in rd]
    return Table(name=name, dims=dims,
                 measures=tuple(c for c in cols if c not in dims),
                 rows=rows, units=dict(units or {}))


def table_trove(t: Table, origin: Cite, *, kind: str = "observation") -> Trove:
    tr = Trove(origin=origin)
    _name_item(tr, t.name)
    for n, row in enumerate(t.rows, 1):
        key = t.key_of(row)
        # The ident is built from the COORDINATE, not from the row number, so
        # re-harvesting a table whose rows were reordered updates the same items
        # instead of creating a parallel set. Row order is presentation; the cell
        # is identity.
        ident = _slug(f"{t.name}-" + "-".join(v for _k, v in key.dims)) or f"row-{n}"
        tr.add(Item(ident=ident, kind=kind, loci=(key,),
                    fields={m: row.get(m, "") for m in t.measures
                            if row.get(m, "")},
                    units=dict(t.units),
                    cites=(Cite(origin.source_url, origin.snapshot,
                                origin.method, locator=f"row {n}"),)))
    return tr


def trove_table(tr: Trove, *, kind: str = "observation") -> Table:
    items = tr.of_kind(kind)
    dims: tuple[str, ...] = ()
    for i in items:
        k = i.locus("key")
        if isinstance(k, Key) and k.dims:
            dims = tuple(d for d, _ in k.dims)
            break
    measures: list[str] = []
    for i in items:
        for f in i.fields:
            if f not in measures:
                measures.append(f)
    rows = []
    for i in items:
        k = i.locus("key")
        row = dict(k.dims) if isinstance(k, Key) else {}
        row.update(i.fields)
        rows.append(row)
    units = dict(items[0].units) if items else {}
    return Table(name=_name_of(tr), dims=dims, measures=tuple(measures),
                 rows=rows, units=units)


def table_lens(origin: Cite, *, kind: str = "observation") -> Lens:
    return Lens(lambda t: table_trove(t, origin, kind=kind),
                lambda tr: trove_table(tr, kind=kind),
                normalize=lambda t: (t.name, t.dims,
                                     tuple(sorted(t.units.items())),
                                     tuple(tuple(sorted(r.items()))
                                           for r in t.rows)),
                label="table<->trove")


# ── Geometry — features in space ────────────────────────────────────────────


@dataclass
class Feature:
    ident: str
    site: Site
    fields: dict[str, str] = field(default_factory=dict)


@dataclass
class Geometry:
    name: str = ""
    features: list[Feature] = field(default_factory=list)


def read_geojson(text: str, *, name: str = "", ident_field: str = "",
                 crs: str = "EPSG:4326") -> Geometry:
    """A GeoJSON FeatureCollection into Geometry.

    Handles Point / LineString / Polygon and the Multi- forms, which is what a
    city actually publishes. A geometry kind we do not understand becomes a Site
    with a **name and no shape** rather than an error or a guess — the
    unresolved state Site was built to hold, doing its job on its first day.
    """
    doc = json.loads(text)
    feats = doc.get("features", []) if isinstance(doc, dict) else []
    out = Geometry(name=name)
    for n, f in enumerate(feats, 1):
        props = {k: str(v) for k, v in (f.get("properties") or {}).items()
                 if v is not None}
        ident = _slug(props.get(ident_field, "")) or f"feature-{n}"
        g = f.get("geometry") or {}
        form, shape, dim = _geojson_shape(g)
        out.features.append(Feature(
            ident=ident,
            site=Site(name=props.get("name", ""), crs=crs if form else "",
                      form=form, shape=shape, dim=dim),
            fields=props))
    return out


def _geojson_shape(g: dict) -> tuple[str, tuple, int]:
    t = g.get("type", "")
    c = g.get("coordinates")
    if not c:
        return "", (), 2
    dim = 3 if _first_depth(c) >= 3 else 2

    def pts(seq) -> tuple:
        return tuple(tuple(float(x) for x in p) for p in seq)

    if t == "Point":
        return "point", (tuple(float(x) for x in c),), dim
    if t == "MultiPoint":
        return "point", pts(c), dim
    if t == "LineString":
        return "path", pts(c), dim
    if t == "Polygon":
        return "area", tuple(pts(ring) for ring in c), dim
    if t == "MultiPolygon":
        # Flattened to the rings of every part. Lossy about which ring belongs
        # to which part, and said so here rather than pretended otherwise: a
        # multipolygon is rare in the sources we target and correct handling
        # belongs with a real geometry library, not a stdlib reader.
        return "area", tuple(pts(ring) for poly in c for ring in poly), dim
    return "", (), dim


def _first_depth(c) -> int:
    while isinstance(c, list) and c and isinstance(c[0], list):
        c = c[0]
    return len(c) if isinstance(c, list) else 0


def geometry_trove(g: Geometry, origin: Cite, *, kind: str = "area") -> Trove:
    tr = Trove(origin=origin)
    _name_item(tr, g.name)
    for n, f in enumerate(g.features, 1):
        tr.add(Item(ident=f.ident, kind=kind, loci=(f.site,), fields=dict(f.fields),
                    cites=(Cite(origin.source_url, origin.snapshot, origin.method,
                                locator=f"feature {n}"),)))
    return tr


def trove_geometry(tr: Trove, *, kind: str = "area") -> Geometry:
    out = Geometry(name=_name_of(tr))
    for i in tr.of_kind(kind):
        s = i.locus("site")
        out.features.append(Feature(ident=i.ident,
                                    site=s if isinstance(s, Site) else Site(),
                                    fields=dict(i.fields)))
    return out


def geometry_lens(origin: Cite, *, kind: str = "area") -> Lens:
    return Lens(lambda g: geometry_trove(g, origin, kind=kind),
                lambda tr: trove_geometry(tr, kind=kind),
                normalize=lambda g: (g.name, tuple(
                    (f.ident, f.site, tuple(sorted(f.fields.items())))
                    for f in g.features)),
                label="geometry<->trove")


# ── Timeline — segments in time ─────────────────────────────────────────────


@dataclass
class Segment:
    """One interval with something said or done in it.

    `speaker` is a **label**, not an identity. A transcript's "SPEAKER_02" and
    a diarizer's cluster are both labels; attaching a person's name to one is a
    human's act, performed in the consumer as a logged command
    (okf/concepts/attribution.md). Reyna carries the label and stops.
    """

    start: float          # seconds from the start of the recording
    end: float
    text: str = ""
    speaker: str = ""


@dataclass
class Timeline:
    name: str = ""
    segments: list[Segment] = field(default_factory=list)
    frame: str = "media"      # or "utc", when the segments are really dated


_VTT_CUE = re.compile(
    r"(\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}|\d{1,2}:\d{2}[.,]\d{1,3})\s*-->\s*"
    r"(\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}|\d{1,2}:\d{2}[.,]\d{1,3})")
_VTT_VOICE = re.compile(r"<v\s+([^>]+)>(.*?)(?:</v>)?$", re.S)


def read_vtt(text: str, *, name: str = "") -> Timeline:
    """WebVTT or SRT into a Timeline. Both are cue-blocks with a timing line, so
    one reader covers both; the differences (a cue id, comma decimals) are
    tolerated rather than modelled."""
    tl = Timeline(name=name)
    cur: Optional[Segment] = None
    body: list[str] = []

    def flush() -> None:
        if cur is None:
            return
        raw = " ".join(x.strip() for x in body if x.strip())
        m = _VTT_VOICE.match(raw)
        if m:
            cur.speaker, raw = m.group(1).strip(), m.group(2)
        cur.text = re.sub(r"<[^>]+>", "", raw).strip()
        if cur.text:
            tl.segments.append(cur)

    for line in text.splitlines():
        m = _VTT_CUE.search(line)
        if m:
            flush()
            cur, body = Segment(_secs(m.group(1)), _secs(m.group(2))), []
            continue
        if line.strip() in ("", "WEBVTT") or line.strip().isdigit():
            if not line.strip():
                flush()
                cur, body = None, []
            continue
        if cur is not None:
            body.append(line)
    flush()
    return tl


def _secs(t: str) -> float:
    t = t.replace(",", ".")
    parts = [float(p) for p in t.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def _t(v: float) -> str:
    """Seconds as a fixed-width string. Fixed width so ordinary string
    comparison orders segments correctly — a Span's bounds are strings, and
    "100.0" < "9.0" is the bug that costs an afternoon."""
    return f"{v:012.3f}"


def timeline_trove(tl: Timeline, origin: Cite, *, kind: str = "utterance") -> Trove:
    tr = Trove(origin=origin)
    _name_item(tr, tl.name)
    for n, s in enumerate(tl.segments, 1):
        it = Item(ident=f"{_slug(tl.name) or 'seg'}-{n:05d}", kind=kind,
                  loci=(Span(_t(s.start), _t(s.end), frame=tl.frame),),
                  fields={"text": s.text},
                  cites=(Cite(origin.source_url, origin.snapshot, origin.method,
                              locator=_clock(s.start)),))
        if s.speaker:
            # A LABEL, in its own field, never in `role` or a link to a person.
            # The moment this becomes an edge to a contact it has asserted an
            # identity, and that assertion is a human's to make.
            it.fields["speaker_label"] = s.speaker
        tr.add(it)
    return tr


def trove_timeline(tr: Trove, *, kind: str = "utterance") -> Timeline:
    out = Timeline(name=_name_of(tr))
    frame = ""
    for i in tr.of_kind(kind):
        sp = i.locus("span")
        if not isinstance(sp, Span):
            continue
        frame = frame or sp.frame
        out.segments.append(Segment(float(sp.start or 0), float(sp.end or 0),
                                    i.fields.get("text", ""),
                                    i.fields.get("speaker_label", "")))
    out.frame = frame or "media"
    return out


def timeline_lens(origin: Cite, *, kind: str = "utterance") -> Lens:
    return Lens(lambda tl: timeline_trove(tl, origin, kind=kind),
                lambda tr: trove_timeline(tr, kind=kind),
                normalize=lambda tl: (tl.name, tl.frame, tuple(
                    (round(s.start, 3), round(s.end, 3),
                     " ".join(s.text.split()), s.speaker)
                    for s in tl.segments)),
                label="timeline<->trove")


def _clock(v: float) -> str:
    h, rem = divmod(int(v), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _slug(s: str, maxlen: int = 48) -> str:
    out: list[str] = []
    for ch in s.lower():
        if ch.isalnum() and ord(ch) < 128:
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")[:maxlen]
