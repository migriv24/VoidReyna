"""
reyna/cli.py — phase 1's whole user interface.

    reyna fetch <url> [--reason r]   fetch politely and archive the result
    reyna history <url>              every time we looked, and what we found
    reyna changes <url>              only the fetches where the content DIFFERED
    reyna ls                         the whole archive, newest last
    reyna cat <content-id>           the exact bytes we hold, to stdout

`changes` is the one that matters. On a document that is supposed to be final —
an approved set of minutes — a second line of output **is itself a finding**.
"""

from __future__ import annotations

import argparse
import os
import sys

from .archive import Archive
from .harvest import Harvester, Politeness

DEFAULT_ROOT = os.environ.get("REYNA_ARCHIVE", "archive")


def _fmt(r) -> str:
    state = "ok" if r.ok else (f"HTTP {r.status}" if r.status else "FAILED")
    if r.status == 304:
        state = "unchanged (304)"
    return f"{r.fetched_at}  {state:<16} {r.short()}  {r.size:>9}  {r.url}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="reyna", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--archive", default=DEFAULT_ROOT, help="archive root (or $REYNA_ARCHIVE)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="fetch a URL and archive it")
    f.add_argument("url")
    f.add_argument("--reason", default="", help="why — free text, kept with the record")
    f.add_argument("--interval", type=float, default=3.0, help="seconds between requests per host")
    f.add_argument("--ignore-robots", action="store_true",
                   help="do not consult robots.txt (say why in --reason)")

    for name, helptext in (("history", "every fetch of a URL"),
                           ("changes", "only the fetches where content differed")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("url")

    g = sub.add_parser("ingest", help="archive a file we did not fetch (a records request)")
    g.add_argument("path")
    g.add_argument("--origin", required=True,
                   help="where it REALLY came from, e.g. 'records request 2026-08-14, City Recorder'")
    g.add_argument("--reason", default="")

    e = sub.add_parser("extract", help="pull text/structure out of an archived document")
    e.add_argument("content_id")
    e.add_argument("--structure", action="store_true", help="numbered provisions, not raw text")

    m = sub.add_parser("emit", help="a command transcript for an archived policy document")
    m.add_argument("content_id")
    m.add_argument("--title", default="", help="the policy's title")
    m.add_argument("--adopted", default="",
                   help="the date the body DECIDED (ISO); defaults to --effective. "
                        "Kept apart from --effective so a RETROACTIVE adoption "
                        "ranks by when it was decided, not when it took effect")
    m.add_argument("--name", default="", help="rune name (default: slug of the title)")
    m.add_argument("--effective", default="", help="ISO date this version took effect")
    m.add_argument("--mantle", default="civic")
    m.add_argument("-o", "--out", default="", help="write here instead of stdout")

    sub.add_parser("ls", help="every record in the archive")
    c = sub.add_parser("cat", help="write archived bytes to stdout")
    c.add_argument("content_id")

    a = ap.parse_args(argv)
    arc = Archive(a.archive)

    if a.cmd == "fetch":
        h = Harvester(arc, Politeness(min_interval=a.interval,
                                      obey_robots=not a.ignore_robots))
        f = h.fetch(a.url, reason=a.reason)
        print(_fmt(f.record))
        if f.record.error:
            print(f"  error: {f.record.error}", file=sys.stderr)
            return 1
        # Say plainly what this fetch meant, because "did it change" is the
        # entire question and should not need a second command. `changed` comes
        # from the Fetch, which held the before-state; asking the archive after
        # the write would compare the record against itself.
        if f.changed is None:
            print("  first capture")
        elif f.changed:
            print("  *** CONTENT CHANGED since the last capture ***")
        else:
            print("  unchanged since last capture")
        return 0

    if a.cmd == "ingest":
        rec = arc.ingest(a.path, origin=a.origin, reason=a.reason)
        print(_fmt(rec))
        print("  ingested (not fetched) - origin recorded as stated")
        return 0

    if a.cmd in ("extract", "emit"):
        from .extract import pdf_text, parse_numbered_document
        try:
            data = arc.open_bytes(a.content_id)
        except FileNotFoundError:
            print(f"no blob {a.content_id}", file=sys.stderr)
            return 1
        rec = next((r for r in arc.records() if r.content_id == a.content_id), None)
        text = pdf_text(data) if data[:5] == b"%PDF-" else data.decode("utf-8", "replace")
        if a.cmd == "extract":
            if not a.structure:
                print(text)
                return 0
            doc = parse_numbered_document(text)
            for p in doc.provisions:
                print(f"{p.number:<10} {'  ' * p.number.count('.')}{p.heading}"
                      f"   ({len(p.text)} chars)"
                      + (f"  [in {p.parent}]" if p.parent else ""))
            print("", file=sys.stderr)
            print(f"{len(doc.provisions)} provisions", file=sys.stderr)
            return 0

        from .emit import emit_policy
        if rec is None:
            print("no record for that blob - cannot cite it", file=sys.stderr)
            return 1
        doc = parse_numbered_document(text, title=a.title)
        t = emit_policy(doc, rec, policy_name=a.name, mantle=a.mantle,
                        effective=a.effective, adopted=a.adopted)
        out = t.text()
        if a.out:
            import pathlib
            pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            with open(a.out, "w", encoding="utf-8") as fh:
                fh.write(out)
            print(f"{len(t)} commands -> {a.out}", file=sys.stderr)
        else:
            sys.stdout.write(out)
        return 0

    if a.cmd == "history":
        rs = arc.history(a.url)
        for r in rs:
            print(_fmt(r))
        if not rs:
            print("no captures of that URL", file=sys.stderr)
            return 1
        return 0

    if a.cmd == "changes":
        ch = arc.changes(a.url)
        for when, cid in ch:
            print(f"{when}  {cid[:16]}")
        if len(ch) > 1:
            print(f"\n{len(ch)} distinct versions. If this document was supposed "
                  f"to be final, that is a finding.", file=sys.stderr)
        return 0

    if a.cmd == "ls":
        n = 0
        for r in arc.records():
            print(_fmt(r))
            n += 1
        print(f"\n{n} record(s) in {arc.root}", file=sys.stderr)
        return 0

    if a.cmd == "cat":
        try:
            sys.stdout.buffer.write(arc.open_bytes(a.content_id))
        except FileNotFoundError:
            print(f"no blob {a.content_id}", file=sys.stderr)
            return 1
        return 0

    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
