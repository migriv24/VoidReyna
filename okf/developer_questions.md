---
type: Questions
title: Developer questions
description: Open decisions for the author, each with a lean. Answers fold into concepts and clear from here.
tags: [status:current, audience:dev, confidence:asserted]
timestamp: 2026-08-16T00:00:00Z
---

Open decisions, with leans so a non-answer has a sensible default.

# Open

- **R2 — `urllib.robotparser` is not RFC 9309.** (opened 2026-08-16.) The
  stdlib returns the **first** matching rule in file order; the standard says
  the **longest** match wins with `Allow` breaking ties. So

      Allow: /
      Disallow: /private

  reads as "everything allowed" to the stdlib and "everything but /private" to
  the standard — and the stdlib errs **permissive**, which is the wrong
  direction when "we obey robots.txt" is a claim we make in public.

  **Lean: leave it for now, fix it before unattended harvesting.** Phase 1
  fetches a handful of known government URLs whose robots.txt we have also read
  by hand, so the live risk is nil. It becomes real the moment a sweep runs
  without someone watching, and that is the moment to implement longest-match
  ourselves or vendor a compliant parser. Documented in `harvest.allowed()` so
  it cannot be a surprise.

- **R3 — how much of a 41 MB packet do we keep?** (opened 2026-08-16.) One
  agenda packet is 41.5 MB, and a decade of them is tens of gigabytes. The
  archive is content-addressed so unchanged documents cost nothing to re-check,
  but the first capture is the first capture. **Lean: keep everything, and
  revisit only when it hurts.** The whole premise is that the bytes are the
  evidence; a policy of keeping extracts instead would make us the only party
  who cannot prove what a document said. Blob storage is cheap relative to
  being unable to answer the question the project exists to answer.

- **R4 — when does the harvester become a Void Core holiday properly?**
  (opened 2026-08-16.) Today it is a plain Python module with a CLI, and the
  seam it should present is Void Core's effect-handler (`effect <op> …`), so a
  script could call it. **Lean: at phase 2**, when Hormiga first needs to
  *invoke* a harvest rather than consume its output. Building the seam before
  there is a caller would be guessing at the calling convention.

- **R5 — the PDF extractor does not scale.** (opened 2026-08-16.) It is pure
  stdlib and fine on the ~230 KB policy documents that are the first target, but
  a 41.5 MB agenda packet decompresses to ~156 MB of operators and did not
  finish in five minutes. **Lean: leave it until packets are the target.** The
  regex is doing the work a real parser would do with a tokenizer, so the fix is
  probably `pypdf` behind the `pdf` extra rather than a cleverer regex — and it
  costs nothing today because the archive already holds the bytes, so the parser
  can be replaced without re-fetching anything. That is the property the
  archive-first design was for.

- **R6 — extraction quality is a spectrum, and we should say where we are.**
  (opened 2026-08-16.) The structural parse of Springfield's Operating Policies
  finds all 150 provisions in document order with correct nesting, which is good.
  It also produces artefacts: a heading occasionally absorbs the first words of
  its body ("Authority T", "Election of President At the"). **Lean: ship it and
  make the artefacts visible rather than pretending they are not there** — a
  heading is a label, the *text* is the evidence, and the text is intact. The
  rule that matters is already enforced: **losing structure is recoverable,
  losing text is not**, so the parser drops a doubtful heading rather than
  cutting text out of the provision that contains it.

- **R7 — newlines in emitted values.** (opened 2026-08-17.) `quote()` collapses
  whitespace runs, newlines included, because a transcript is consumed **line by
  line** on both sides — `parse_transcript` here and `import_reyna_transcript` in
  Hormiga — so a value spanning two lines produces a command neither can read,
  and the Hormiga-side failure is *silent* (first line dispatches truncated,
  second is refused as an unknown verb). **Lean: leave it.** It costs nothing
  today since `pdf_text` already collapses whitespace. When an extractor that
  preserves paragraphs arrives the fix is `setjson` — JSON-encodes the newline,
  stays on one line, and is the mechanism Hormiga already uses for Allomone
  script bodies — plus JSON-decoding in `civic::field_of`.

- **R8 — discovery is missing, and it is structural.** (opened 2026-08-17.) Four
  catalogue cases fail at "which URLs exist", and each fails differently: a
  sitemap, an index page, a zip manifest, an API cursor. **Lean: a `Source`
  abstraction with `discover()` alongside `fetch()`**, written when the second
  source actually arrives rather than now — the shape of `discover` is exactly
  the thing one example cannot tell you, and guessing it is how the pivot got
  mis-named the first time.

- **R9 — one blob can hold many troves.** (opened 2026-08-17.) An agenda packet
  is a hundred documents concatenated; a GTFS feed is a zip of related tables.
  Extraction currently returns one structure per blob. **Lean: let an extractor
  return a list of troves, and leave containers alone until packets are the
  target** (which is also R5's condition). The design question that looked hard —
  how a contained item cites its position *inside* the container — is answered by
  `Cite.locator`, which already exists.

- **R10 — `Cite.method` is a string, and one day it must be an algebra.**
  (opened 2026-08-17.) Fine while every claim rests on one source. It stops being
  fine the moment a claim is *derived* from two, because "may this be published"
  is then a question about a combination, and hand-written propagation rules are
  where such things go wrong silently. **Lean: leave it until the first
  two-source claim exists** — foundations §3 flags the provenance-semiring
  correspondence as something to work out *before* claiming it, and that is still
  the honest status.

# Answered

- **R1 — Laserfiche says `Disallow: /`. What now? — ANSWERED 2026-08-17.**
  Harvest the permitted domain, and **ask** about the rest rather than routing
  around the file. The author's answer added the part that mattered: check the
  design against a spread of *other* hypothetical extractions before trusting it.
  That produced [extraction-cases](/concepts/extraction-cases.md) — 22 harvests,
  six of which broke something — and from it the [pivot](/concepts/pivot.md). The
  asking half is now a practice rather than a one-off decision: see
  [records-requests](/concepts/records-requests.md) for the ladder, the Oregon
  specifics, and the Springfield letter.
