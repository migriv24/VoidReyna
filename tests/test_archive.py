"""
Phase 1's exit test (okf/roadmap.md):

    Fetch the same document twice, a week apart. The archive holds two records;
    an unchanged document produces an identical snapshot id and a changed one
    does not. *Change detection works before anything depends on it.*

Run without waiting a week by serving the document from a local HTTP server we
control, and changing it between fetches. That is a *stronger* test than waiting
would be: waiting proves the page did not change, this proves we would notice if
it did.

No network, no dependencies:  python -m pytest tests/  — or just run this file.
"""

from __future__ import annotations

import http.server
import threading
import time
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reyna.archive import Archive, Record, content_id  # noqa: E402
from reyna.harvest import Harvester, Politeness        # noqa: E402

# ── a server whose body we can change between requests ─────────────────────
_BODY = {"data": b"version one", "etag": '"v1"'}


class _H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path == "/robots.txt":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            # NOTE: no blanket "Allow: /" here, and the omission is the point.
            # `urllib.robotparser` returns the FIRST matching rule in file
            # order, not RFC 9309's longest match — so a leading `Allow: /`
            # makes every Disallow below it dead, and the stdlib would happily
            # fetch /private. That divergence is real and documented in
            # harvest.allowed(); this file is written unambiguously so the test
            # measures the harvester rather than the stdlib's quirk.
            self.wfile.write(b"User-agent: *\nDisallow: /private\n")
            return
        if self.path == "/private/secret":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"should never be fetched")
            return
        if self.path == "/gone":
            self.send_error(404)
            return
        if self.client_address and self.headers.get("If-None-Match") == _BODY["etag"]:
            self.send_response(304)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("ETag", _BODY["etag"])
        self.end_headers()
        self.wfile.write(_BODY["data"])

    def log_message(self, *a):  # quiet
        pass


def _serve():
    srv = http.server.HTTPServer(("127.0.0.1", 0), _H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_port}"


FAILS = []


def check(cond, what):
    if not cond:
        FAILS.append(what)
        print(f"FAIL: {what}")


def test_everything(tmp_root: Path | None = None):
    root = tmp_root or Path(__file__).parent / "_tmp_archive"
    if root.exists():
        import shutil
        shutil.rmtree(root)
    srv, base = _serve()
    try:
        arc = Archive(root)
        # fast interval: politeness is tested separately, not by making the
        # suite slow
        h = Harvester(arc, Politeness(min_interval=0.0, retries=0))

        # ── 1. first capture ───────────────────────────────────────────────
        _BODY["data"], _BODY["etag"] = b"version one", '"v1"'
        f1 = h.fetch(f"{base}/doc", reason="first look")
        r1 = f1.record
        check(f1.ok, "first fetch ok")
        check(r1.content_id == content_id(b"version one"), "content id is sha256 of the bytes")
        # never seen before => None, NOT False. The distinction is load-bearing:
        # "we have never looked" is not "it has not changed".
        check(f1.changed is None, "first capture reports None, not False")
        check(arc.last_successful(f"{base}/nope") is None, "unseen URL has no last capture")

        # ── 2. unchanged: 304, no new bytes, same id ───────────────────────
        f2 = h.fetch(f"{base}/doc", reason="sweep")
        r2 = f2.record
        check(r2.status == 304, "conditional GET yields 304 when unchanged")
        check(r2.content_id == r1.content_id, "304 keeps the id we already hold")
        check(f2.changed is False, "unchanged detected")

        # ── 3. THE EXIT TEST: the document changes, and we notice ──────────
        _BODY["data"], _BODY["etag"] = b"version two, quietly edited", '"v2"'
        f3 = h.fetch(f"{base}/doc", reason="sweep")
        r3 = f3.record
        check(f3.ok and r3.status == 200, "changed document is re-fetched")
        check(r3.content_id != r1.content_id, "*** a changed document gets a different id ***")
        check(f3.changed is True, "*** THE EXIT TEST: the change is detected ***")

        # ...and the archive can say so as history. Two distinct versions of a
        # document that was supposed to be final IS the finding.
        ch = arc.changes(f"{base}/doc")
        check(len(ch) == 2, f"two distinct versions recorded (got {len(ch)})")

        # ── 4. the archive is append-only and content-addressed ────────────
        recs = list(arc.records())
        check(len(recs) == 3, f"three records for three fetches (got {len(recs)})")
        blobs = list((root / "blobs").rglob("*"))
        blobs = [b for b in blobs if b.is_file()]
        check(len(blobs) == 2, f"two blobs for two distinct contents (got {len(blobs)})")
        check(arc.open_bytes(r1.content_id) == b"version one", "the original bytes survive")
        check(arc.open_bytes(r3.content_id) == b"version two, quietly edited",
              "the new bytes are stored too")

        # ── 5. a failed fetch is evidence, not an exception ────────────────
        r4 = h.fetch(f"{base}/gone", reason="checking a dead link").record
        check(not r4.ok and r4.status == 404, "404 recorded, not raised")
        check(any(r.url.endswith("/gone") for r in arc.records()), "the failure is archived")

        # ── 6. robots.txt is obeyed ────────────────────────────────────────
        r5 = h.fetch(f"{base}/private/secret").record
        check(not r5.ok, "disallowed path is not fetched")
        check("robots" in r5.error, f"and says why (got '{r5.error}')")
        check(not (root / "blobs").joinpath(
            content_id(b"should never be fetched")[:2],
            content_id(b"should never be fetched")).exists(),
            "and no bytes were stored")

        # ── 7. records are immutable ───────────────────────────────────────
        try:
            object.__setattr__  # noqa: B018
            r1.url = "http://evil"  # type: ignore[misc]
            check(False, "a Record should be frozen")
        except Exception:
            check(True, "")

        # ── 8. purity: the id depends on content and nothing else ──────────
        check(content_id(b"abc") == content_id(b"abc"), "same bytes, same id")
        check(content_id(b"abc") != content_id(b"abd"), "different bytes, different id")
    finally:
        srv.shutdown()

    if FAILS:
        print(f"\n{len(FAILS)} check(s) failed")
        return 1
    print("OK - the evidence locker holds: 3 fetches, 2 versions, 1 change caught")
    return 0


if __name__ == "__main__":
    raise SystemExit(test_everything())
