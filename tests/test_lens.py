"""
The round-trip law, run against the REAL Springfield policy document.

`okf/concepts/foundations.md` claims a holiday is "an effect boundary plus a
pure Lens", and that lenses compose so a pivot format is provably as lossless as
its legs. This is where those stop being claims.

The one that matters: **`emit_policy` shipped a version that lost 150
provisions' worth of text**, and it took a C++ test in another repository to
notice. `lens.check()` notices here, in one line, before anything is emitted.

    python tests/test_lens.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reyna.archive import Archive, Record                      # noqa: E402
from reyna.emit import emit_policy, parse_transcript, policy_lens  # noqa: E402
from reyna.extract import Document, Provision, parse_numbered_document, pdf_text  # noqa: E402
from reyna.lens import Lens, pipeline                          # noqa: E402

FAILS: list[str] = []


def check(cond, what):
    if not cond:
        FAILS.append(what)
        print(f"FAIL: {what}")


REC = Record(url="https://example.gov/opp.pdf", fetched_at="2026-08-17T00:00:00Z",
             status=200, content_id="a" * 64, size=1)


def sample_doc() -> Document:
    """A small document exercising the shapes that break emitters: nesting,
    a section with no text of its own, punctuation the quoting has to survive,
    and a multi-line clause."""
    return Document(title="Test Policies", provisions=[
        Provision("1", "Authority", "Adopted under the Charter, Chapter IV."),
        Provision("2", "Officers", ""),                       # heading only
        Provision("2.1", "Election of President",
                  "The Council shall elect one of its members as President.",
                  parent="2"),
        Provision("2.2", "Other Seats",
                  "The City Manager, City Recorder, and City Attorney "
                  "are entitled to seats.", parent="2"),
        Provision("2.2.1", "Limits",
                  "They don't vote; the Mayor's ruling stands.", parent="2.2"),
        Provision("3", "Meetings", "Meetings are held\non Mondays."),
    ])


def main() -> int:
    # ── 1. THE LAW, on a document built to be awkward ───────────────────────
    lens = policy_lens(REC, policy_name="tp", effective="2025-10-06")
    rep = lens.check([sample_doc()])
    print(rep.render())
    check(rep.ok, "the sample document round-trips through the transcript")

    # ── 2. THE LAW WOULD HAVE CAUGHT YESTERDAY'S BUG ────────────────────────
    # A forward mapping that drops every provision's text — precisely the bug
    # that shipped — must be REPORTED, not tolerated. If this ever passes, the
    # law has stopped protecting anything.
    def lossy_forward(doc: Document) -> str:
        stripped = Document(title=doc.title, provisions=[
            Provision(p.number, p.heading, "", p.parent) for p in doc.provisions])
        return emit_policy(stripped, REC, policy_name="tp",
                           effective="2025-10-06").text()

    lossy = Lens(lossy_forward, parse_transcript,
                 normalize=lens.normalize, label="lossy")
    bad = lossy.check([sample_doc()])
    check(not bad.ok, "a text-dropping emitter FAILS the law (the shipped bug)")
    print(f"  (lossy lens correctly reported: {len(bad.mismatches)} mismatch)")

    # ── 3. COMPOSITION, and the claim that losslessness composes ────────────
    up = Lens(lambda d: Document(title=d.title.upper(), provisions=d.provisions),
              lambda d: Document(title=d.title.title(), provisions=d.provisions),
              label="title-case")
    both = up.compose(lens)
    check(both.check([sample_doc()]).ok, "lossless then lossless is lossless")
    check(Lens.identity().compose(lens).check([sample_doc()]).ok,
          "identity is the unit")
    check(pipeline().check([sample_doc()]).ok, "an empty pipeline is the identity")
    # …and a lossy leg poisons the composite, which is the property that makes
    # the pivot rule an argument rather than a preference.
    check(not up.compose(lossy).check([sample_doc()]).ok,
          "lossless then LOSSY is lossy - the composite inherits the weakest leg")

    # ── 4. inverse ─────────────────────────────────────────────────────────
    check(lens.inverse().forward is lens.backward, "inverse swaps the directions")

    # ── 5. THE REAL DOCUMENT, if the archive has it ─────────────────────────
    # This is the one that matters: 150 provisions of genuine Springfield text,
    # through the same law.
    arc_root = Path(__file__).resolve().parents[1] / "archive"
    real = None
    if arc_root.exists():
        arc = Archive(arc_root)
        for r in arc.records():
            if r.ok and "Operating Policies" in r.url:
                real = r
                break
    if real is None:
        print("\n(no archived Springfield policy — skipping the real-document law;"
              "\n run: reyna ingest <pdf> --origin '...' to enable it)")
    else:
        doc = parse_numbered_document(pdf_text(Archive(arc_root).open_bytes(real.content_id)))
        rl = policy_lens(real, policy_name="opp", effective="2025-10-06")
        rep = rl.check([doc])
        print(rep.render())
        check(rep.ok, f"the REAL document ({len(doc.provisions)} provisions) "
                      f"round-trips")
        # and the pivot claim, concretely: the same lens serves any adapter that
        # can produce a Document, which is the only thing a new source must do.
        check(len(doc.provisions) > 100, "the real document really is large")

    if FAILS:
        print(f"\n{len(FAILS)} check(s) failed")
        return 1
    print("\nOK - the round-trip law holds, and catches the bug that shipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
