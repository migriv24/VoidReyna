"""
reyna/harvest.py — the boundary. The only impure arrow in the system.

Void Core's banked invariant (design/transform-layers.md): *effects live at the
holiday boundary; none of reduce/temper/scry ever fires one.* This module is
that boundary for the network, and it is deliberately **thin**: fetch, record,
stop. Every judgement — what a document means, how it is structured, who said
what — belongs on the pure side, where it is testable with no network and
re-runnable when we get it wrong. We will get it wrong; that is what the archive
is for.

MANNERS, WHICH ARE THE WHOLE ETHICS OF CRAWLING (okf/concepts/harvest.md). What
makes the Internet Archive acceptable is not scale or permission — it is:

  * identify yourself, with a contact a webmaster can actually reach
  * rate-limit per host and back off; a records project needs one request every
    few seconds, not a search engine's firehose
  * respect robots.txt
  * fetch conditionally (If-None-Match / If-Modified-Since) — polite, and it
    makes change detection nearly free
  * never re-download what the archive already holds

All of it is enforced here rather than left to a caller's good intentions,
because a politeness rule a caller can forget is not a rule.

NO DEPENDENCIES. urllib and robotparser are stdlib, which keeps phase 1 honest:
the evidence locker must not need a wheel to work.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
import urllib.robotparser
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from .archive import Archive, Record, content_id, utc_now_iso

# Identify honestly. A public-records harvester that hides what it is has
# already given up the argument for why it is allowed to run.
USER_AGENT = (
    "VoidReyna/0.1 (public-records harvester; "
    "+https://github.com/voidreyna; contact: see repository)"
)


@dataclass(frozen=True)
class Fetch:
    """What one look produced: the new record, and the last successful capture
    that preceded it.

    `changed` is computed HERE rather than asked of the archive, because the
    archive cannot answer it safely — `fetch` has already written the new record
    by the time anyone could ask, so a store-side comparison compares the new
    record against itself (see Archive.last_successful). Holding the before-state
    explicitly removes the ordering hazard instead of documenting it.
    """

    record: "Record"
    previous: Optional["Record"] = None

    @property
    def ok(self) -> bool:
        return self.record.ok

    @property
    def changed(self) -> Optional[bool]:
        """True / False / None, and **None is not False**: "we have never seen
        this before" is a different claim from "it is the same as last time",
        and collapsing them is how an archive starts lying quietly."""
        if self.previous is None:
            return None
        if self.record.status == 304:
            return False
        if not self.record.content_id:
            return None                      # a failed fetch tells us nothing
        return self.record.content_id != self.previous.content_id


@dataclass
class Politeness:
    """The knobs, with defaults chosen for a *records* project.

    `min_interval` is per host. Weekly sweeps of a city portal do not need to be
    fast, and being slow is most of what makes this defensible.
    """

    min_interval: float = 3.0   # seconds between requests to one host
    timeout: float = 30.0
    max_bytes: int = 64 * 1024 * 1024   # a PDF, not a video
    obey_robots: bool = True
    retries: int = 2
    backoff: float = 5.0


class Harvester:
    """Fetches politely into an Archive. One per run; keeps per-host timing."""

    def __init__(self, archive: Archive, politeness: Optional[Politeness] = None):
        self.archive = archive
        self.p = politeness or Politeness()
        self._last: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    # ── politeness ─────────────────────────────────────────────────────────
    def _wait(self, host: str) -> None:
        last = self._last.get(host)
        if last is not None:
            gap = self.p.min_interval - (time.monotonic() - last)
            if gap > 0:
                time.sleep(gap)
        self._last[host] = time.monotonic()

    def allowed(self, url: str) -> bool:
        """robots.txt, cached per host.

        A robots.txt we cannot fetch is treated as PERMISSIVE, which is the
        conventional reading and the one the standard describes — but it is a
        judgement call, so it is written down here rather than buried.

        ⚠ **`urllib.robotparser` is not RFC 9309.** The stdlib returns the
        FIRST matching rule in file order; the standard says the LONGEST match
        wins, with `Allow` beating `Disallow` on a tie. So a file reading

            Allow: /
            Disallow: /private

        is "everything allowed" to the stdlib and "everything but /private" to
        the standard — and the stdlib's reading is the *permissive* one, which
        is the wrong direction to be wrong in when the claim we make publicly is
        that we obey robots.txt.

        Found 2026-08-16 by a test that was itself written ambiguously, which is
        how it surfaced at all. **Not yet fixed**, because phase 1 fetches a
        handful of known government URLs and a wrong-but-permissive reading of a
        file we have also read by hand is not the live risk. It becomes one the
        moment harvesting is unattended, and that is the moment to implement
        longest-match ourselves (or vendor a compliant parser). Recorded in
        okf/developer_questions.md rather than left as a surprise.
        """
        if not self.p.obey_robots:
            return True
        parts = urlparse(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(origin + "/robots.txt")
            try:
                self._wait(parts.netloc)
                rp.read()
            except Exception:
                rp = None  # unreachable robots.txt: permissive
            self._robots[origin] = rp
        rp = self._robots[origin]
        return True if rp is None else rp.can_fetch(USER_AGENT, url)

    # ── the fetch ──────────────────────────────────────────────────────────
    def fetch(self, url: str, reason: str = "") -> Fetch:
        """Fetch one URL and append a record. Always returns a Record.

        A FAILED FETCH IS ALSO EVIDENCE and is archived as one. "The portal was
        down on the 3rd" and "we never looked on the 3rd" are different claims,
        and an archive that only keeps successes cannot tell them apart.

        Conditional: if we already hold this URL with an ETag or Last-Modified,
        we send it, and a 304 costs no bytes and still produces a record — which
        is the cheapest possible proof that nothing changed.
        """
        parts = urlparse(url)
        prev = self.archive.last_successful(url)  # BEFORE we write anything
        if parts.scheme not in ("http", "https"):
            return self._record(url, 0, b"", {}, reason, prev,
                                error=f"unsupported scheme: {parts.scheme}")
        if not self.allowed(url):
            return self._record(url, 0, b"", {}, reason, prev,
                                error="disallowed by robots.txt")
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        if prev and prev.ok:
            if prev.etag:
                req.add_header("If-None-Match", prev.etag)
            if prev.last_modified:
                req.add_header("If-Modified-Since", prev.last_modified)

        last_err = ""
        for attempt in range(self.p.retries + 1):
            self._wait(parts.netloc)
            try:
                with urllib.request.urlopen(req, timeout=self.p.timeout) as resp:
                    data = resp.read(self.p.max_bytes + 1)
                    if len(data) > self.p.max_bytes:
                        return self._record(url, resp.status, b"", dict(resp.headers),
                                            reason, prev, error="exceeds max_bytes")
                    return self._record(url, resp.status, data, dict(resp.headers), reason, prev)
            except urllib.error.HTTPError as e:
                hdrs = dict(e.headers or {})
                if e.code == 304:
                    # Unchanged, and the server said so without sending bytes.
                    # Record it with the id we already hold: the point of a
                    # record is "we looked, on this date, and this is what was
                    # there" — and it was the same thing.
                    return self._record(url, 304, b"", hdrs, reason, prev,
                                        keep_id=prev.content_id if prev else "")
                if e.code in (429, 503) and attempt < self.p.retries:
                    time.sleep(self.p.backoff * (attempt + 1))
                    last_err = f"HTTP {e.code}"
                    continue
                return self._record(url, e.code, b"", hdrs, reason, prev, error=f"HTTP {e.code}")
            except Exception as e:  # noqa: BLE001 — a failed fetch is evidence
                last_err = f"{type(e).__name__}: {e}"
                if attempt < self.p.retries:
                    time.sleep(self.p.backoff * (attempt + 1))
                    continue
        return self._record(url, 0, b"", {}, reason, prev, error=last_err or "failed")

    def _record(self, url: str, status: int, data: bytes, headers: dict,
                reason: str, prev: Optional[Record], error: str = "",
                keep_id: str = "") -> Fetch:
        rec = Record(
            url=url,
            fetched_at=utc_now_iso(),
            status=status,
            content_id=keep_id or (content_id(data) if data else ""),
            size=len(data),
            content_type=headers.get("Content-Type", ""),
            etag=headers.get("ETag", ""),
            last_modified=headers.get("Last-Modified", ""),
            error=error,
            reason=reason,
            headers={k: v for k, v in headers.items()},
        )
        self.archive.put(rec, data if data else None)
        return Fetch(record=rec, previous=prev)
