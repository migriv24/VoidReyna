"""
reyna/extract.py — the PURE side. Bytes in, structure out.

Nothing here touches the network, the clock, or a model. Every function is a
pure function of its arguments, which is what makes the whole pipeline
re-runnable: when we get an extraction wrong — and we will — the fix is to
change this file and re-run it over the archive we already hold, without asking
a city's web server for anything a second time.

That property is the reason the archive comes first and the parser second.

PDF TEXT, WITH STDLIB. `zlib` + the content-stream text operators. It handles
the ordinary case (a text-bearing PDF produced by a word processor, which is
what a city publishes) and it does NOT handle scanned images, encrypted files,
or exotic encodings. Those return empty rather than guessing, because a parser
that invents text for a scan is worse than one that admits it cannot read it.

KNOWN LIMIT, MEASURED 2026-08-16: this is O(bytes) with a heavy constant and it
is too slow on a 41 MB agenda packet (156 MB of decompressed operators). Fine on
the ~200 KB policy documents that are the first target. Recorded rather than
hidden — see okf/developer_questions.md R5.
"""

from __future__ import annotations

import re
import zlib
from dataclasses import dataclass, field
from typing import Optional

# ── PDF text ────────────────────────────────────────────────────────────────

_STREAM = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.S)
_TEXTOP = re.compile(rb"\[(.*?)\]\s*TJ|\((?:\\.|[^\\()])*\)\s*Tj", re.S)
_LITERAL = re.compile(rb"\((?:\\.|[^\\()])*\)")


def _unescape(b: bytes) -> bytes:
    """PDF string escapes: \\n \\r \\t \\b \\f, octal, and \\<char>."""
    out = bytearray()
    i = 0
    esc = {0x6E: 10, 0x72: 13, 0x74: 9, 0x62: 8, 0x66: 12}
    while i < len(b):
        c = b[i]
        if c == 0x5C and i + 1 < len(b):
            n = b[i + 1]
            if n in esc:
                out.append(esc[n]); i += 2; continue
            if 0x30 <= n <= 0x37:  # octal
                j = i + 1
                digits = b""
                while j < len(b) and 0x30 <= b[j] <= 0x37 and len(digits) < 3:
                    digits += bytes([b[j]]); j += 1
                out.append(int(digits, 8) & 0xFF); i = j; continue
            out.append(n); i += 2; continue
        out.append(c); i += 1
    return bytes(out)


def pdf_pages(data: bytes, max_bytes: int = 8 * 1024 * 1024) -> list[str]:
    """Text per content stream, in file order. Roughly one entry per page.

    `max_bytes` caps a single decompressed stream, so one pathological object
    cannot hang a batch — the cap is a refusal, not a truncation: an oversized
    stream is skipped and its absence is visible as a short page list.
    """
    pages: list[str] = []
    for m in _STREAM.finditer(data):
        try:
            s = zlib.decompress(m.group(1))
        except Exception:
            continue
        if len(s) > max_bytes:
            continue
        if b"BT" not in s or (b"Tj" not in s and b"TJ" not in s):
            continue  # a font program or an image, not text
        parts = [
            b"".join(_unescape(p[1:-1]) for p in _LITERAL.findall(t.group(0)))
            .decode("latin-1")
            for t in _TEXTOP.finditer(s)
        ]
        if parts:
            pages.append(" ".join(parts))
    return pages


def pdf_text(data: bytes) -> str:
    """One flattened string. Runs of whitespace collapse, and the dot-leaders a
    table of contents is made of collapse too, because they are layout and not
    content."""
    t = " ".join(pdf_pages(data))
    t = re.sub(r"\.{4,}", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# ── numbered normative documents ────────────────────────────────────────────
#
# A city's operating policies, an ordinance, a set of bylaws, a platform's terms
# of service: all of them are "a title, then numbered provisions, nested". This
# parser finds that structure and nothing else. It does not try to understand
# what a provision MEANS — that is a person's job, and the model deliberately
# stores the text rather than an interpretation of it.

@dataclass
class Provision:
    number: str                 # "3", "3.3", "3.3.1" — as the document wrote it
    heading: str
    text: str = ""
    parent: Optional[str] = None  # the containing NUMBER, resolved structurally


@dataclass
class Document:
    title: str = ""
    provisions: list[Provision] = field(default_factory=list)
    # Text before the first numbered provision — a preamble, an adoption line.
    preamble: str = ""


# "SECTION 4 ORDER OF BUSINESS" — capitalised word, number, then a SHOUTED title
_SECTION = re.compile(r"\bSECTION\s+(\d+)\s+([A-Z][A-Z \-'&/]{2,80})")
# "3.3.1 Notification" — a dotted number, then a heading, then the body.
#
# The heading is taken as Title-Case words and stops at the first word that is
# NOT Title-Case, which is where prose begins. An earlier version stopped at the
# first following capital and truncated almost every heading ("Mayor and",
# "Open to the"); this keeps them whole.
_NUMBERED = re.compile(
    r"(?<![\d.])(\d+(?:\.\d+)+)\s+"
    r"((?:[A-Z][A-Za-z'&/\-]*(?:\s+(?:and|or|of|to|for|the|a|an|on|in|by)\b)?\s*){1,10})"
)
# A page number swept into a heading — "Condolences 17", "Amendments 21 1".
_TRAILING_PAGENO = re.compile(r"(?:\s+\d{1,3})+\s*$")


def _number_key(num: str) -> tuple[int, ...]:
    return tuple(int(x) for x in num.split(".") if x.isdigit())


def _despace_caps(s: str) -> str:
    """PDF text extraction frequently splits a word after its first letter —
    "A UTHORITY", "T he City Manager". Rejoin a single leading capital that is
    followed by a space and a lowercase run, which is the shape that artefact
    always takes and which no real title has."""
    s = re.sub(r"\b([A-Z]) ([A-Z]{2,})\b", r"\1\2", s)      # A UTHORITY
    return re.sub(r"\b([A-Z]) ([a-z]{2,})\b", r"\1\2", s)    # T he


def parse_numbered_document(text: str, title: str = "") -> Document:
    """Split a flattened normative document into provisions.

    Deliberately conservative: it recognises SECTION headings and dotted
    numbers, and everything it cannot place stays in the preceding provision's
    text rather than being dropped. **Losing text is worse than mis-nesting
    it** — a wrong parent is visible and fixable in the app, whereas a silently
    dropped clause is an altered public record.
    """
    text = _despace_caps(text)
    doc = Document(title=title)

    # SKIP THE TABLE OF CONTENTS. A TOC repeats every number the body will use,
    # so parsing the whole file produces each provision twice and interleaves
    # them unusably. An earlier version tried "keep the last occurrence of each
    # number", which fails on the common case of a body that cross-references an
    # earlier clause — the reference wins over the real heading.
    #
    # The body starts at the LAST occurrence of the first section marker: a TOC
    # lists "SECTION 1" once, and the body repeats it. Documents with no TOC are
    # unaffected because there is only one occurrence to find.
    body_start = 0
    first = _SECTION.search(text)
    if first:
        hits = [m.start() for m in _SECTION.finditer(text)
                if m.group(1) == first.group(1)]
        if len(hits) > 1:
            body_start = hits[-1]

    marks: list[tuple[int, int, str, str]] = []   # (start, end, number, heading)
    def clean(h: str) -> str:
        h = _TRAILING_PAGENO.sub("", h.strip())
        return re.sub(r"\s+", " ", h).strip(" .,;:")

    for m in _SECTION.finditer(text):
        marks.append((m.start(), m.end(), m.group(1), clean(m.group(2)).title()))
    for m in _NUMBERED.finditer(text):
        head = clean(m.group(2))
        if not head:
            continue
        # end the mark where the HEADING ends, so the body text starts after it
        marks.append((m.start(), m.start() + len(m.group(0).rstrip()), m.group(1), head))
    marks.sort(key=lambda x: x[0])

    body = [mk for mk in marks if mk[0] >= body_start]

    # MONOTONICITY. In a body, provision numbers only go forward. A number that
    # goes *backwards* against its neighbours is not a provision — it is a list
    # item ("2.4 Scheduled vacations") or a cross-reference inside someone
    # else's text, and treating it as a provision both invents a clause and
    # steals the text of the real one it interrupted.
    #
    # This is a heuristic and it is the honest kind: it can only ever DROP a
    # spurious heading, never invent one, and dropped text stays with the
    # provision that contains it. Losing structure is recoverable; losing text
    # is not.
    kept: list[tuple[int, int, str, str]] = []
    for mk in body:
        if kept and _number_key(mk[2]) <= _number_key(kept[-1][2]):
            continue
        kept.append(mk)
    body = kept

    if body:
        doc.preamble = text[body_start : body[0][0]].strip()
    for i, (_s, e, num, head) in enumerate(body):
        end = body[i + 1][0] if i + 1 < len(body) else len(text)
        doc.provisions.append(Provision(number=num, heading=head,
                                        text=text[e:end].strip()))

    # Parent = the longest existing number that is a dotted prefix. Structural,
    # so a document that skips a level (3 → 3.3.1 with no 3.3) still nests
    # sensibly instead of orphaning the child.
    have = {p.number for p in doc.provisions}
    for p in doc.provisions:
        parts = p.number.split(".")
        for cut in range(len(parts) - 1, 0, -1):
            cand = ".".join(parts[:cut])
            if cand in have:
                p.parent = cand
                break
    return doc
