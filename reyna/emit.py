"""
reyna/emit.py — the seam. Structure in, a Void Core command transcript out.

This is the entire contract with any consumer, and it is deliberately the
smallest one available: **we emit verbs, not data structures.** Nothing is
linked, no header is shared, no schema is kept in sync across two languages and
two repos. A tool that emits a text transcript is a tool nobody is locked into —
Reyna could be rewritten in another language, or replaced by a person typing, and
Hormiga would not notice.

It also means conformance is automatic rather than aspirational: an import lands
as one replayable, undoable, attributed batch because that is what dispatcher
commands *are*.

CITATION IS NOT OPTIONAL. Every rune this file emits carries `source_url` and
`snapshot` — the archived bytes it came from. A civic dataset whose claims cannot
be traced back to a document is a rumour with better typography, and the archive
exists precisely so the trace is real. `cite()` is the only way to add fields
here, so forgetting is not available.

PURE. Nothing here fetches, writes or reads a clock. Commands in a list.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

import json
import re

from .archive import Record
from .extract import Document, Provision
from .lens import Lens
from .pivot import Cite, Item, Locus, Span, Trail, Trove, loci_json, loci_of


def quote(s: str) -> str:
    """One command argument, single-quoted.

    Void Core escapes only ``\\'`` inside single quotes and passes everything
    else through literally — including the double quotes policy text is full of,
    which a double-quoted argument could not carry.

    NEWLINES ARE COLLAPSED TO SPACES, and that is a decision rather than an
    oversight. Void Core *would* carry a real newline inside single quotes — but
    a transcript is consumed **line by line**, by `parse_transcript` here and by
    `import_reyna_transcript` in Hormiga, so a value spanning two lines produces
    a command neither side can read. The Hormiga-side failure is silent: the
    first line dispatches a truncated value and the second is refused as an
    unknown verb.

    It costs nothing today because `pdf_text` already collapses whitespace, so
    there is no paragraph structure to lose. When an extractor that *preserves*
    paragraphs arrives, the fix is `setjson` — JSON-encodes the newline and stays
    on one line, the mechanism Hormiga already uses for Allomone script bodies —
    plus JSON-decoding in `civic::field_of`. Recorded as R7 rather than left as a
    trap.
    """
    s = " ".join(s.split())
    return _one_arg(s)


def _one_arg(s: str) -> str:
    """The escaping half of both quoters, and the only place it is written.

    TRAILING BACKSLASHES ARE EMITTED OUTSIDE THE QUOTES. Void Core SPEC 6.1,
    documented 2026-08-17 after they found the third spelling of a bug we had
    already shipped twice. A value *ending* in a backslash puts it immediately
    before the closing quote, where the tokenizer reads the pair as an escaped
    apostrophe: the argument never closes, it swallows the rest of the line, and
    dispatch still reports ok. Pinned upstream in
    ``VoidCore/conformance/cases/12-arg-quoting.vs``, which asserts *positively*
    that the naive spelling turns the value ``C:\\`` into ``C:'``.

    Outside the quotes a backslash is literal and, being neither whitespace nor
    a quote, still belongs to the same token.

    Nothing else is escaped. Inside single quotes the only escape args.c honours
    is a backslash before an apostrophe, so escaping a backslash would itself be
    a bug -- a doubled one would arrive as two.
    """
    head = s.rstrip(chr(92))
    return "'" + head.replace("'", chr(92) + "'") + "'" + s[len(head):]


def json_arg(s: str) -> str:
    """A JSON value as ONE dispatcher argument.

    Separate from `quote()` and it has to be. `quote()` collapses whitespace
    runs, which is right for prose on a line-oriented wire and **wrong for
    JSON**, where the runs may be inside a string and collapsing them edits the
    value. `json.dumps` already emits no newline, so nothing here needs to.

    Mirrors Hormiga's own `json_arg` (src/app_shared.cpp). Both delegate the
    escaping to `_one_arg`, which is where the two traps are written down.
    """
    return _one_arg(s)


def slug(s: str, maxlen: int = 48) -> str:
    """A rune name: lowercase, ascii, hyphenated. Rune names are identifiers a
    person types and a citation points at, so they must be stable and dull."""
    out = []
    for ch in s.lower():
        if ch.isalnum() and ord(ch) < 128:
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")[:maxlen] or "unnamed"


@dataclass
class Transcript:
    """An accumulating list of commands, with the citation discipline built in."""

    lines: list[str] = field(default_factory=list)
    # Set once and applied by cite(); a transcript is always about one source.
    source_url: str = ""
    snapshot: str = ""

    def raw(self, cmd: str) -> "Transcript":
        self.lines.append(cmd)
        return self

    def mantle(self, name: str) -> "Transcript":
        return self.raw(f"mantle new {name}")

    def use(self, name: str) -> "Transcript":
        return self.raw(f"use {name}")

    def rune(self, glyph: str, name: str) -> "Transcript":
        return self.raw(f"rune new {glyph} {name}")

    def set(self, name: str, key: str, value: str) -> "Transcript":
        if value == "":
            return self
        return self.raw(f"set {name} {key} {quote(value)}")

    def setjson(self, name: str, key: str, value: str) -> "Transcript":
        if not value:
            return self
        return self.raw(f"setjson {name} {key} {json_arg(value)}")

    def link(self, a: str, b: str, relation: str) -> "Transcript":
        return self.raw(f"link {a} {b} --relation {relation}")

    def tag(self, name: str, *tags: str) -> "Transcript":
        return self.raw(f"tag {name} " + " ".join("+" + t for t in tags)) if tags else self

    def cite(self, name: str) -> "Transcript":
        """Stamp a rune with where it came from. Called for every rune emitted.

        `snapshot` is the archive's content id, so a reader can pull the exact
        bytes back out and check the claim — and can tell whether the live
        document still matches what we cited."""
        self.set(name, "source_url", self.source_url)
        self.set(name, "snapshot", self.snapshot)
        return self

    def text(self) -> str:
        return "\n".join(self.lines) + "\n"

    def __len__(self) -> int:
        return len(self.lines)


# ── THE ONE EMITTER: Trove -> transcript ────────────────────────────────────
#
# Written once, against the pivot (reyna/pivot.py). Every format — a numbered
# document, a budget table, a zoning layer, a meeting transcript — reaches this
# function through its own small lens and none of them had to teach it anything.
# That is the pivot rule collecting, and it is the reason this file did not grow
# a second `emit_*` when three new formats arrived.
#
# TWO PASSES, runes then links, because a Trove is a set and cannot promise that
# an item appears before something that points at it. `emit_policy` got away with
# interleaving only because document order happens to put a parent first.

# Field names the wire reserves. Anything else on an Item is the source's.
_RESERVED = {"source_url", "snapshot", "method", "locator", "withheld", "cites",
             "loci", "units", "number", "from", "until"}


def _flat_loci(loci: tuple[Locus, ...]) -> Optional[dict]:
    """The flat form — `number`, `from`, `until` — or None if it cannot carry
    this locus set faithfully.

    WHY BOTHER, when one `setjson loci` would always work. Because a transcript
    is read by people. `set opp-3-3-1 number '3.3.1'` is legible and is exactly
    what Hormiga's civic glyphs already store; a JSON blob in its place would be
    noise in the common case and would make every existing consumer poorer.

    So the flat form is used when it is EXACTLY equivalent, and the moment it is
    not — a Site, a Key, two loci of one kind, a media timecode, an UNKNOWN
    bound — the whole set goes as JSON. The test for "exactly equivalent" is
    below and it is deliberately strict; a flat form that is *nearly* right is a
    silent loss, which is the failure this project keeps finding.
    """
    out: dict[str, str] = {}
    seen: set[str] = set()
    for l in loci:
        if l.kind in seen:
            return None                      # two Spans is a claim flat cannot make
        seen.add(l.kind)
        if isinstance(l, Trail):
            # A part containing "." would rejoin ambiguously; an ordinal has
            # nowhere flat to live.
            if l.ordinal or any("." in p for p in l.parts) or not l.parts:
                return None
            out["number"] = l.number
        elif isinstance(l, Span):
            # UNKNOWN cannot be flattened: an absent `until` already means OPEN
            # ("indefinitely") to Hormiga's civic model, so "we don't know" and
            # "there is no end" would become the same wire bytes. They are not
            # the same claim and the archive does not get to blur them.
            if l.frame != "utc" or Span.UNKNOWN in (l.start, l.end):
                return None
            if not l.start and not l.end:
                return None                  # all-OPEN: nothing to write, unreadable back
            out["from"], out["until"] = l.start, l.end
        else:
            return None                      # Site and Key have no flat form
    return out


def emit_trove(tr: Trove, *, mantle: str = "civic") -> Transcript:
    """A Trove as Void Core commands. The only emitter in the project."""
    t = Transcript(source_url=tr.origin.source_url, snapshot=tr.origin.snapshot)
    t.mantle(mantle)

    for it in tr.items:
        t.rune(it.kind, it.ident)
        for k, v in it.fields.items():
            if k not in _RESERVED:
                t.set(it.ident, k, v)

        flat = _flat_loci(it.loci)
        if flat is None:
            t.setjson(it.ident, "loci", loci_json(it.loci))
        else:
            for k, v in flat.items():
                t.set(it.ident, k, v)

        if it.units:
            t.setjson(it.ident, "units", json.dumps(it.units, sort_keys=True,
                                                    separators=(",", ":")))

        cites = tr.cites_for(it)
        first = cites[0] if cites else Cite()
        t.set(it.ident, "source_url", first.source_url)
        t.set(it.ident, "snapshot", first.snapshot)
        if first.method and first.method != "verbatim":
            t.set(it.ident, "method", first.method)
        if first.locator:
            t.set(it.ident, "locator", first.locator)
        if first.withheld:
            t.set(it.ident, "withheld", "1")
        if len(cites) > 1:
            # A claim resting on two sources. The flat pair still carries the
            # first, so every existing consumer keeps working; the full list
            # rides alongside for the one that eventually asks the harder
            # question (foundations §3, provenance semirings).
            t.setjson(it.ident, "cites",
                      json.dumps([c.json() for c in cites], separators=(",", ":")))

    for it in tr.items:
        parent = tr.parent_of(it)
        if parent is not None:
            t.link(it.ident, parent.ident, "part-of")
        for rel, target in it.refs:
            t.link(it.ident, target, rel)
    return t


def emit_policy(doc: Document, record: Record, *, policy_name: str = "",
                mantle: str = "civic", effective: str = "",
                adopted: str = "") -> Transcript:
    """A parsed normative document as commands for Hormiga's civic model.

    Emits, per okf/concepts/civic-record.md:

      * one ``policy``    — the identity that persists
      * one ``provision`` per numbered item, joined by ``part-of`` LINKS
        (containment is a graph; the tree is a view the app derives)
      * one ``revision``  — a single DATED ASSERTION carrying the text, linked
        to each provision by ``amends``

    NOTE WHAT IS **NOT** EMITTED. No votes: this document does not record any,
    and inventing them would be exactly the failure this project exists to
    avoid. No interpretation of what a provision means. No guess at an
    ``until``. A harvester's job is to say what a document said, and to stop.
    """
    return emit_trove(document_trove(doc, record, policy_name=policy_name,
                                     effective=effective, adopted=adopted),
                      mantle=mantle)


def document_trove(doc: Document, record: Record, *, policy_name: str = "",
                   effective: str = "", adopted: str = "") -> Trove:
    """`Document -> Trove`. The document format's leg of the pivot.

    All the civic judgement lives here, and none of it lives in `emit_trove` —
    which is the division the pivot was for: what a policy *means* is
    format-specific, and how a claim becomes a command is not.

    ONE ASSERTION PER PROVISION, all sharing the adoption date. The first
    version emitted a single `revision` for the whole document, on the
    reasoning that the council adopted one document on one day. That is true
    about the *event* and wrong about the *assertion*: a revision carries one
    `text`, and one text field cannot hold 150 provisions' worth. The whole
    policy resolved to nothing, and a seam test in another repository caught it.

    The honest reading is that publishing a document makes 150 separate claims —
    "on 2025-10-06, provision 3.3.1 reads X" — which happen to share a date and
    a source. They compose correctly (each is about a different provision, so
    nothing conflicts), a later targeted amendment to one clause simply wins on
    date, and the shared `snapshot` is what groups them back into "these all
    came from that publication".

    It also keeps text OUT of the provision item: a provision is identity,
    number and heading; what it *says* belongs to a dated assertion, and storing
    it in both places would be the second source of truth the design refuses.

    NOTE WHAT IS **NOT** PRODUCED. No votes — this document records none, and
    inventing them would be exactly the failure the project exists to avoid. No
    interpretation of what a provision means. A harvester's job is to say what a
    document said, and then to stop.
    """
    origin = Cite(source_url=record.url, snapshot=record.content_id)
    tr = Trove(origin=origin)
    pid = policy_name or slug(doc.title or "policy")
    tr.add(Item(ident=pid, kind="policy", fields={"title": doc.title}))

    numbers = {p.number for p in doc.provisions}
    for p in doc.provisions:
        rid = f"{pid}-{p.number.replace('.', '-')}"
        it = Item(ident=rid, kind="provision",
                  fields={"heading": p.heading},
                  loci=(Trail(tuple(p.number.split("."))),))
        # A top-level provision hangs off the policy. `Trove.parent_of` derives
        # containment from trails and correctly finds nothing above "1", so this
        # one edge is stated rather than derived — the policy is not a provision
        # and has no trail to be the prefix of.
        if not p.parent or p.parent not in numbers:
            it.refs = (("part-of", pid),)
        if not effective:
            # No date given, so nothing can be asserted *as of* anything. Park
            # the text on the provision rather than inventing an effective date:
            # a made-up date in a civic archive is worse than a missing one.
            if p.text:
                it.fields["text"] = p.text
        tr.add(it)

    if effective:
        for p in doc.provisions:
            if not p.text:
                continue                      # a bare heading asserts nothing
            rid = f"{pid}-{p.number.replace('.', '-')}"
            tr.add(Item(ident=f"{rid}-rev-{effective}", kind="revision",
                        fields={"summary": f"{p.number} as published {effective}",
                                "text": p.text,
                                # DECISION time, kept apart from valid time even
                                # though they are equal here. A published policy
                                # takes effect on adoption, so the distinction
                                # costs one redundant-looking field today and
                                # saves migrating the whole corpus the first
                                # time a retroactive amendment arrives — which
                                # is ordinary, and which Hormiga's `resolve_at`
                                # now ranks by. See civic.hpp, Q31.
                                "adopted": adopted or effective},
                        # OPEN, not UNKNOWN, and on purpose: an adopted policy
                        # really does stay in force until something changes it.
                        # Saying so explicitly is the difference between a claim
                        # we make and a default nobody chose.
                        loci=(Span(effective, Span.OPEN),),
                        refs=(("amends", rid),)))
    return tr


def trove_document(tr: Trove) -> Document:
    """`Trove -> Document`. The other half of the document leg.

    Text comes from the assertion *about* a provision, never from the provision
    itself, which is the model's rule read backwards.
    """
    pol = next((i for i in tr.items if i.kind == "policy"), None)
    doc = Document(title=pol.fields.get("title", "") if pol else "")

    text_of: dict[str, str] = {}
    for rev in tr.of_kind("revision"):
        for rel, target in rev.refs:
            if rel == "amends" and rev.fields.get("text"):
                text_of[target] = rev.fields["text"]

    for it in tr.of_kind("provision"):
        t = it.trail
        parent = tr.parent_of(it)
        doc.provisions.append(Provision(
            number=t.number if t else "",
            heading=it.fields.get("heading", ""),
            text=text_of.get(it.ident, it.fields.get("text", "")),
            parent=parent.trail.number if parent and parent.trail else None))
    return doc


# ── the BACKWARD direction, which turns emit into a Lens ────────────────────
#
# A transcript is text, so "did the emitter drop anything" is answerable only if
# the text can be read back into the structure it came from. That is what makes
# `policy_lens` a real lens rather than a one-way pipe with a nice name — and it
# is not academic: `emit_policy` shipped a version that put a whole document's
# 150 provisions' text into ONE revision field, losing all of it, and it took a
# test in another repo to notice. `lens.check()` notices in one line.

_RE_RUNE = re.compile(r"^rune new (\S+) (\S+)$")
_RE_SET = re.compile(r"^set (\S+) (\S+) '(.*)'$", re.S)
_RE_SETJSON = re.compile(r"^setjson (\S+) (\S+) '(.*)'$", re.S)
_RE_LINK = re.compile(r"^link (\S+) (\S+) --relation (\S+)$")


def unquote(s: str) -> str:
    r"""Inverse of `quote`'s escaping: a real backslash before a quote.

    Note the `r` prefix and `chr(92)`. Written as `s.replace("\'", "'")` this is
    a **silent no-op** — Python reads `"\'"` as just `'`, so it replaces a quote
    with a quote — and it shipped that way for exactly as long as it took the
    round-trip law to run. Which is the argument for the law in one line.
    """
    return s.replace(chr(92) + "'", "'")


def parse_trove(text: str) -> Trove:
    """A transcript back into a Trove. The inverse of `emit_trove`.

    Deliberately strict about SHAPE and forgiving about ORDER and EXTRAS: it
    reads the verbs this module emits and ignores everything else, so a
    transcript carrying additional commands still round-trips the part we own.
    """
    order: list[str] = []
    glyphs: dict[str, str] = {}
    fields: dict[str, dict[str, str]] = {}
    jsons: dict[str, dict[str, str]] = {}
    links: list[tuple[str, str, str]] = []

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _RE_RUNE.match(line)
        if m:
            glyphs[m.group(2)] = m.group(1)
            fields.setdefault(m.group(2), {})
            jsons.setdefault(m.group(2), {})
            order.append(m.group(2))
            continue
        m = _RE_SETJSON.match(line)   # BEFORE `set` — `setjson` is not a `set`
        if m:
            jsons.setdefault(m.group(1), {})[m.group(2)] = unquote(m.group(3))
            continue
        m = _RE_SET.match(line)
        if m:
            fields.setdefault(m.group(1), {})[m.group(2)] = unquote(m.group(3))
            continue
        m = _RE_LINK.match(line)
        if m:
            links.append((m.group(1), m.group(2), m.group(3)))
            continue

    tr = Trove()
    for ident in order:
        f = fields.get(ident, {})
        j = jsons.get(ident, {})

        if "loci" in j:
            loci = loci_of(j["loci"])
        else:
            loci = _loci_from_flat(f)

        if "cites" in j:
            cites = tuple(Cite.of(d) for d in json.loads(j["cites"]))
        else:
            cites = (Cite(source_url=f.get("source_url", ""),
                          snapshot=f.get("snapshot", ""),
                          method=f.get("method", "verbatim"),
                          locator=f.get("locator", ""),
                          withheld=f.get("withheld", "") == "1"),)

        tr.add(Item(ident=ident, kind=glyphs.get(ident, ""),
                    fields={k: v for k, v in f.items() if k not in _RESERVED},
                    loci=loci, cites=cites,
                    units=json.loads(j["units"]) if "units" in j else {}))

    # Refs, in a second pass: telling a DERIVED `part-of` from a stated one
    # needs the whole trove, since "derived" means "the trail already implies
    # it". Emitting both and reading back only the stated one is what keeps
    # containment a single source of truth on the wire.
    by = tr.by_ident()
    for a, b, rel in links:
        it = by.get(a)
        if it is None:
            continue
        if rel == "part-of":
            p = tr.parent_of(it)
            if p is not None and p.ident == b:
                continue                      # derived from the trail; not a ref
        it.refs = it.refs + ((rel, b),)
    return tr


def parse_transcript(text: str) -> Document:
    """A transcript back into a Document — `parse_trove` then the document leg."""
    return trove_document(parse_trove(text))


# ── the lenses ──────────────────────────────────────────────────────────────


def trove_lens(*, mantle: str = "civic") -> Lens:
    """`Trove ⇄ transcript text` — the leg every format shares.

    Lossless, with no normalizer doing quiet work: everything a Trove holds is
    something a command can carry. That is not luck — `Trove.title` was removed
    for exactly this reason (see `pivot.Trove`), because the alternative was a
    normalizer that hid a real loss behind a comparison, which is the one thing
    a normalizer must never be used for.
    """
    def norm(tr: Trove) -> tuple:
        return tuple(
            (i.ident, i.kind, tuple(sorted(i.fields.items())), i.loci,
             tuple(sorted(i.units.items())), i.refs, tr.cites_for(i))
            for i in tr.items)

    return Lens(forward=lambda tr: emit_trove(tr, mantle=mantle).text(),
                backward=parse_trove, normalize=norm, label="trove<->transcript")


def document_lens(record: Record, *, policy_name: str = "",
                  effective: str = "", adopted: str = "") -> Lens:
    """`Document ⇄ Trove` — the document format's leg."""
    def norm(doc: Document) -> tuple:
        # Compare on what the pivot actually carries. Order is compared too: a
        # lens that silently reordered a policy's clauses would be lying about
        # the document.
        return tuple((p.number, p.heading.strip(), " ".join(p.text.split()),
                      p.parent) for p in doc.provisions)

    return Lens(forward=lambda d: document_trove(d, record,
                                                 policy_name=policy_name,
                                                 effective=effective,
                                                 adopted=adopted),
                backward=trove_document, normalize=norm,
                label="document<->trove")


def policy_lens(record: Record, *, policy_name: str = "", mantle: str = "civic",
                effective: str = "", adopted: str = "") -> Lens:
    """`Document ⇄ transcript text`, **as a composition** rather than a mapping.

    This is the pivot rule stated as code instead of as a slogan:

        Document ⇄ Trove ⇄ transcript

    Neither leg knows about the other. A new source — HTML minutes, a Legistar
    API, a GeoJSON zoning layer — writes only its own `⇄ Trove` leg and inherits
    the second half for free, and the round-trip law it inherits is *earned*
    rather than assumed, because **losslessness composes** (foundations §1a).

    Which also means `Lens.compose` is now load-bearing here rather than a
    convenience, and the request for it upstream
    (MESSAGE_FOR_VOIDCORE_hormiga-lens-composition-2026-08-12.md) has a working
    reference implementation behind it.
    """
    return document_lens(record, policy_name=policy_name, effective=effective,
                         adopted=adopted).compose(trove_lens(mantle=mantle))


def _loci_from_flat(f: dict[str, str]) -> tuple[Locus, ...]:
    """Rebuild loci from `number` / `from` / `until` when no `loci` json rode
    along. See `_flat_loci` for why the flat form exists at all."""
    out: list[Locus] = []
    if f.get("number"):
        out.append(Trail(tuple(f["number"].split("."))))
    if f.get("from") or f.get("until"):
        out.append(Span(f.get("from", Span.OPEN), f.get("until", Span.OPEN)))
    return tuple(out)
