"""
reyna/archive.py — the evidence locker.

THE CLAIM THIS FILE EXISTS TO MAKE GOOD (okf/concepts/harvest.md):

    Fetching is easy. Being able to prove, in two years, what a page said on a
    given day is the hard part and the valuable one.

So: every fetch is written down *before anything is parsed*, and **the archive is
never edited**. A record is (what we asked for, what came back, the exact bytes,
and a content-derived id). Nothing in here is clever; the value is entirely in it
being boring and append-only.

TWO IDS, AND THE DIFFERENCE MATTERS.

  * ``content_id`` — sha256 of the raw bytes. This is what "did the page change"
    is asked against, and bytes are not JSON, so Void Core's ``provenance()``
    does not apply to them.
  * ``provenance(obj)`` — Void Core's stable, order-independent id for
    *JSON-serializable* values. It is the right tool for a structured extraction
    later in the pipeline, and the wrong tool for a PDF.

An earlier draft of the OKF said provenance() covered both. It does not, and
pretending otherwise would have produced a hash of a base64 string dressed up as
rigour. Both are pure and clock-free, which is the property that actually
matters.

PURE / IMPURE. Everything here except ``Archive.put`` and ``Archive.open_bytes``
is a pure function of its arguments. Writing is the only effect, and it is
append-only, so "impure" here means "adds a file", never "changes one".
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

# The layout on disk. Deliberately inspectable with `ls` and `cat`: an archive
# whose integrity depends on a tool being able to read it is worth less than one
# a person can check by hand.
#
#   <root>/blobs/<aa>/<content_id>          the exact bytes, once per distinct content
#   <root>/records/<utc>-<short>.json       one record per fetch, append-only
#
# Blobs are content-addressed, so re-fetching an unchanged page costs a record
# and no new blob — which is also what makes "unchanged" cheap to prove.

BLOBS = "blobs"
RECORDS = "records"


def content_id(data: bytes) -> str:
    """sha256 of the bytes, hex. Pure, no clock, no salt: the id is a property
    of the content and of nothing else, so two archives on two machines agree."""
    return hashlib.sha256(data).hexdigest()


def utc_now_iso() -> str:
    """The one clock call in the library, isolated here so it is easy to see and
    easy to inject around in tests. Everything downstream takes the timestamp as
    an argument rather than reading a clock itself."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class Record:
    """One fetch, as evidence.

    Frozen because an archive record is a claim about a moment. Correcting one
    means adding another, exactly as a council amends rather than rewrites.
    """

    url: str
    fetched_at: str          # UTC, ISO 8601
    status: int              # HTTP status, or 0 if the fetch never completed
    content_id: str          # sha256 of the bytes ("" when there are none)
    size: int
    content_type: str = ""
    etag: str = ""
    last_modified: str = ""
    error: str = ""          # non-empty when the fetch failed; kept, not dropped
    # Why we went and got it — free text, never interpreted. "weekly sweep",
    # "cited by ord-6472". The archive should be able to say why it holds a thing.
    reason: str = ""
    headers: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == 200 and not self.error and bool(self.content_id)

    def short(self) -> str:
        return self.content_id[:16] if self.content_id else "-" * 16


class Archive:
    """An append-only directory of evidence."""

    def __init__(self, root: str | os.PathLike):
        self.root = Path(root)
        (self.root / BLOBS).mkdir(parents=True, exist_ok=True)
        (self.root / RECORDS).mkdir(parents=True, exist_ok=True)

    # ── writing (the only effect) ──────────────────────────────────────────
    def put(self, rec: Record, data: Optional[bytes]) -> Path:
        """Append one record, storing the bytes if they are new.

        Never overwrites a blob: identical content is identical, so a second
        write would be a no-op that only risks a partial file. Never overwrites
        a record either — if two fetches somehow land in the same second, the
        content id disambiguates them.
        """
        if data:
            blob = self.blob_path(rec.content_id)
            blob.parent.mkdir(parents=True, exist_ok=True)
            if not blob.exists():
                tmp = blob.with_suffix(".part")
                tmp.write_bytes(data)
                tmp.replace(blob)  # atomic: a reader never sees a half blob
        stamp = rec.fetched_at.replace(":", "").replace("-", "")
        path = self.root / RECORDS / f"{stamp}-{rec.short()}.json"
        n = 1
        while path.exists():
            path = self.root / RECORDS / f"{stamp}-{rec.short()}-{n}.json"
            n += 1
        path.write_text(json.dumps(asdict(rec), indent=2, sort_keys=True),
                        encoding="utf-8")
        return path

    def ingest(self, path, origin: str, reason: str = "", when: str = "") -> Record:
        """Archive a file we did not fetch.

        **Not all evidence arrives over HTTP.** A public-records request comes
        back as an email attachment; a clerk hands over a USB stick; a portal
        that disallows crawling (see R1) may still answer a written request. An
        archive that can only hold things it downloaded would push exactly the
        most authoritative documents outside the evidence trail.

        `origin` replaces the URL and must say where it really came from —
        ``"records request 2026-08-14, City Recorder"`` — because a citation
        that reads `file:///C:/Users/...` is not a citation.
        """
        from pathlib import Path as _P
        data = _P(path).read_bytes()
        rec = Record(url=origin, fetched_at=when or utc_now_iso(), status=200,
                     content_id=content_id(data), size=len(data),
                     content_type="", reason=reason)
        self.put(rec, data)
        return rec

    # ── reading (pure) ─────────────────────────────────────────────────────
    def blob_path(self, cid: str) -> Path:
        return self.root / BLOBS / cid[:2] / cid

    def open_bytes(self, cid: str) -> bytes:
        return self.blob_path(cid).read_bytes()

    def records(self) -> Iterator[Record]:
        """Every record, oldest first. Filenames sort chronologically because
        the timestamp leads — which is a small thing that makes the archive
        browsable without this library."""
        for p in sorted((self.root / RECORDS).glob("*.json")):
            yield Record(**json.loads(p.read_text(encoding="utf-8")))

    def history(self, url: str) -> list[Record]:
        """Every fetch of one URL, oldest first — this archive's TimeMap, in the
        Memento sense (okf/concepts/foundations.md §5)."""
        return [r for r in self.records() if r.url == url]

    def latest(self, url: str) -> Optional[Record]:
        h = self.history(url)
        return h[-1] if h else None

    # ── the question the archive exists to answer ──────────────────────────
    def last_successful(self, url: str) -> Optional[Record]:
        """The most recent capture that actually got bytes, or ``None``.

        ``None`` means we have never successfully fetched it, which is honestly
        different from "unchanged" and must not be collapsed into it.

        NOTE ON A TRAP THIS REPLACED. There used to be a
        ``changed_since_last(url, new_id)`` here, and it was **wrong by
        construction**: ``Harvester.fetch`` archives the record before it
        returns, so by the time a caller could ask, the "last" record *was* the
        new one and it compared the id against itself — always "unchanged",
        including for a document that had visibly changed. It passed a casual
        read and failed the first test that changed a document.

        The lesson is not "be careful". It is that **a question whose answer
        depends on whether you asked before or after a write should not be
        asked of the store at all.** So comparison now happens where the
        before-state is unambiguously in hand: `Harvester.fetch` captures the
        previous record first and returns it alongside the new one, as a
        `Fetch`."""
        for r in reversed(self.history(url)):
            if r.ok:
                return r
        return None

    def changes(self, url: str) -> list[tuple[str, str]]:
        """(fetched_at, content_id) for each fetch where the content DIFFERED
        from the previous one. On a document that is supposed to be final — an
        approved set of minutes — a second entry here **is itself a finding**,
        and arguably the most interesting thing this project can surface."""
        out: list[tuple[str, str]] = []
        prev = None
        for r in self.history(url):
            if not r.ok:
                continue
            if prev is None or r.content_id != prev:
                out.append((r.fetched_at, r.content_id))
                prev = r.content_id
        return out
