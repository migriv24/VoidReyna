---
type: Log
title: Log
description: The running history — every session that changed the design or the code.
tags: [status:current, audience:dev, confidence:asserted]
timestamp: 2026-08-12T00:00:00Z
---

## 2026-08-18 — cleaned up, upstream adopted, and deliberately parked

The author's pivot: Reyna stays valuable but Hormiga's headless adoption comes
first, so this session brought Reyna to a clean stopping point rather than a
half-finished one. The roadmap now opens with a **PAUSED** section saying what
works, what a future session should not have to rediscover, and the cheapest way
back in.

**The quoting bug had a third instance, and it was ours.** Void Core found that
the "correct" helper corrupts any value *ending* in a backslash — it lands before
the closing quote, the tokenizer reads the pair as an escaped apostrophe, the
argument never closes, and dispatch returns `ok`. Both our quoters had it. Fixed,
sharing one `_one_arg`, and **pinned** in `tests/test_quoting.py` against their
conformance case rather than trusted. Four wrong implementations in three
codebases is what it took to stop hand-writing this.

**Our `Lens` is deleted.** Void Core confirmed `scry/lens.py` imports without the
compiled engine and added `pure_import_test.py` — which poisons `ctypes.CDLL` so
any load-on-import raises — specifically so we could rely on it in 2031. That
test existing is what justified the deletion; "it happens to work today" would
not have. Vendored into `vendor/voidcore/` with their LICENSE rather than
imported, per rule 2: an archival tool should not need a sibling repo on disk.

Their `RoundTripReport` is better than the one we deleted — a structured
`(index, key, expected, got)` diff, where ours printed two 300-character strings
that looked identical on a large document.

They also shipped our correction (`self.normalize or other.normalize`) and added
the caveat we would not have written: *lossless ∘ lossless is lossless* holds
exactly for exactly-lossless legs, and up-to-normalizer legs carry a hypothesis —
so **every composite must be checked rather than assumed**, which is now how the
four format lenses are tested rather than something we believed about them.

4/4 green, stdlib only, no network.

## 2026-08-17 (later still) — our upstream asks now travel in Hormiga's messages

The author asked for one consolidated message per upstream recipient rather than
an accumulating pile. Reyna's asks are **carried in Hormiga's**, not drafted
separately:

- `../VoidHormiga/MESSAGE_FOR_VOIDCORE_hormiga+reyna-standing-asks-2026-08-17.md`
- `../VoidHormiga/MESSAGE_FOR_VOIDMAIZ_hormiga+reyna-standing-asks-2026-08-17.md`

**Do not draft a `MESSAGE_FOR_*_reyna-…` while those exist** — add to them
instead. One open message per recipient is the rule now; two repos each sending
their own would recreate exactly the pile the author asked us to clear.

What of ours went upstream:

**To Void Core.** The `Lens.compose` ask, restated from having *built* it and
including a correction to what Hormiga proposed in August — a composite's
normalizer must be `self.normalize or other.normalize`, because `None` means *no
opinion* rather than *no normalization*, and the naive version failed on the
first real composition. The argument-quoting gap, now with our `unquote` no-op as
a second independent data point in a second language. A question about whether
`scry.lens` can be imported without the compiled engine, since we duplicated it
to keep `dependencies = []`. And the three-time-axes finding, because `scry.md`
reads as though the context `date` is *the* time axis when it is the query side
of one of three.

**To Void Maiz.** Mostly that **we evaluated them and dissolved the need**, and
the honest reason: not "no Python", but that the human confirmation step must be
a dispatcher command, so it belongs in the consumer. Reyna proposes; Hormiga
confirms — their own propose-never-write pattern, applied a level up. Plus the
four coordinate systems as a report about *their* host-predicate seam rather than
about our pivot: Hormiga's 22 predicates partition into containment / time /
space / dimensions with nobody having designed them to, which only became visible
when this project named the same structure from the other end.

## 2026-08-17 (later) - the pivot: four coordinates, and the answers to R1/Q31/Q32

The author answered four open questions in one message. Three of them turned out
to be the same question.

**R1 asked for a list of hypothetical extractions to check the design against**,
and that list is now [extraction-cases](/concepts/extraction-cases.md):
twenty-two harvests, deliberately including several with nothing to do with a
city council — a transit feed, a museum catalogue, a terms-of-service corpus. It
is a stress test, not a roadmap. A case that breaks something was worth more than
a case that fits, and six of them broke something.

**The finding, which was not the one I expected.** Sort the twenty-two by *what
question you ask about an item's position* and there are exactly four answers:
**Trail** (what is this inside of), **Span** (when, and for how long), **Site**
(where), **Key** (which cell of the cube). And it is not an invented
abstraction — **it is read off the consumer.** Hormiga's Allomone already ships
22 domain predicates and they partition exactly that way. The application has
been asking questions in four coordinate systems since before the pivot existed.

**So `Document` was never the pivot.** Calling it one was defensible with a
single leg and wrong with four; a pivot is what the legs *meet at*. The pivot is
now [`Trove`](/concepts/pivot.md) — items, each carrying a set of loci, refs,
units and citations — and `Document` is a format like any other. Recorded as a
correction rather than quietly fixed, because the mistake is instructive: **you
cannot tell a pivot from a leg until there are two legs.**

Built: `reyna/pivot.py` (Trail/Span/Site/Key, Item, Trove, Cite) and
`reyna/shapes.py` (Table, Geometry, Timeline, with small real parsers for CSV,
GeoJSON and WebVTT), and one emitter — `emit_trove` — written once against the
pivot. `policy_lens` is now literally
`document_lens(...).compose(trove_lens(...))`, which makes `Lens.compose`
load-bearing rather than a convenience.

**The test is the claim.** `tests/test_pivot.py` runs a budget CSV, a zoning
GeoJSON and a meeting VTT through the round-trip law composed with that emitter,
which was **not modified** for any of them; a voxel layer goes through the same
unmodified path. If the pivot were decoration, the emitter would have needed
teaching. The real 150-provision Springfield document still round-trips, and
still imports into Hormiga with 282/282 runes cited.

**Three states that must not collapse**, each a place where a convenient default
would have lied. A `Span` bound is a date, OPEN ("until further notice") or
UNKNOWN ("we did not see one"), defaulting to UNKNOWN. A `Site` is named, celled
or drawn — an address is how the most common spatial datum actually arrives, so
ungeocoded is a *state*, not an error, and geocoding is a holiday. A `Cite` is
verbatim, derived or **withheld** — a redacted release is a different fact from a
record never seen.

**Q31 (bitemporality) came apart into three axes, not two.** Transaction time is
the archive record and the command log, and belongs on neither rune nor pivot.
Valid time is `from`/`until`. **Decision time is `adopted`** — and `from` had been
doing both jobs. That is invisible while adoption is prospective and immediate,
which is every assertion in the current corpus, and it breaks on a *retroactive*
amendment: two assertions then carry equal strength and merge to ⊤, reporting a
conflict the record does not have as though the law were unclear. Hormiga's
`resolve_at` now ranks by decision time and filters by valid time, with a
fallback that leaves every already-stored assertion meaning exactly what it
meant. Emitted here, tested there.

**R1's other half — the closed door — is now a practice rather than a decision.**
[records-requests](/concepts/records-requests.md) has the four-rung ladder (read
the file properly; look for another host; write to the records officer; file a
formal request), the Oregon statutory specifics, what we will not do, and the
Springfield letter as a worked example. The rung that matters structurally is the
fourth: `ingest` already makes evidence arriving on a CD a first-class citizen,
so a records request is *part of the system* rather than the place the software
gives up.

**Bugs the day surfaced.** `tests/run_all.py` held a hand-written list of
filenames, so `test_pivot.py` was written, passing, and **not being run** — a
suite you have to remember to update is a suite that is wrong by default; it
globs now. And `quote()` collapses whitespace runs, which is right for prose on a
line-oriented wire and would silently edit a string *inside* JSON, so `json_arg`
is now its own function mirroring Hormiga's.

## 2026-08-17 — the Lens, and the law that catches what tests in another repo caught late

**The foundational gap this closes.** `okf/concepts/foundations.md` opens by
stating the definition the whole project runs on — *a holiday is an effectful
boundary crossing plus a pure Lens* — and until today **nothing in `reyna/` was
a Lens.** The claim was in the OKF and not in the code, which is how a design
document quietly becomes fiction.

`reyna/lens.py`: `forward`, `backward`, `normalize`, `check`, `check_inverse`,
`inverse`, **`compose`**, `identity`, and a `pipeline` helper. Deliberately
API-compatible with Void Core's `scry/lens.py` but defined here, so the
round-trip law is available under `dependencies = []` — fifty duplicated lines is
a better trade than an install requirement on the one structure that guarantees
we are not losing public records.

**`compose` is the operation the pivot rule runs on**, and Void Core does not
have it (asked for in Hormiga's message of 2026-08-12; this is the reference
implementation for that ask). The law it carries is the whole argument for a
pivot format: **lossless ∘ lossless is lossless**, so `A→pivot→B` is *provably*
as good as its legs rather than merely tidier.

**`Document` is now named as the pivot.** A source adapter's entire job is
`bytes → Document`; everything downstream is shared. HTML minutes or a Legistar
API write one adapter and inherit `policy_lens` for free.

**The backward direction is real.** `parse_transcript` reads an emitted
transcript back into a `Document`, which is what makes `policy_lens` a lens
rather than a one-way pipe with a nice name — and it is checked against the
genuine 150-provision Springfield document, not only a fixture.

### What the law caught, immediately

1. **`unquote` was a silent no-op.** `s.replace("'", "'")` written in a
   context that ate a backslash becomes `s.replace("'", "'")` — Python reads
   `"'"` as just `'`. Every apostrophe in the corpus was surviving as `'`.
   It shipped for exactly as long as it took the law to run once.
2. **A newline in a value breaks BOTH consumers.** A transcript is read line by
   line here and in `import_reyna_transcript`, so a multi-line value produces a
   command neither side can parse — and the Hormiga failure is silent. `quote()`
   now collapses whitespace, with the `setjson` fix recorded as R7.
3. **`compose` silently weakened its arguments.** It kept `self.normalize`, so
   composing a trivial lens (no normalizer) with the policy lens produced a
   composite that compared whitespace the policy lens knew to collapse. Now:
   `self.normalize or other.normalize` — **`None` means *no opinion*, not *no
   normalization***, and a composition operator that quietly weakens its
   arguments' guarantees is worse than not having one.
4. **Non-ASCII in a printable label crashes a Windows console.** A `⇄` in a lens
   label raised `UnicodeEncodeError` in cp1252 — from the very test run that
   would have reported something useful. Labels are machine-facing; typography
   belongs in the docs.

And the point of the exercise, stated plainly: **the test asserts that a
text-dropping emitter FAILS the law** — the exact bug shipped on 2026-08-16,
which took a C++ test in another repository to notice. It is caught here now, in
one line, before anything is emitted.

`tests/run_all.py` runs everything without pytest, because a suite that needs an
install to run does not run on a fresh checkout, which is when it matters most.

## 2026-08-16c — end to end: real PDF → transcript → Hormiga

The author asked for the two things that were actually missing: **something
working in Reyna with a test, and a way to get its data into Hormiga.** Both
exist now, and the loop runs on real Springfield material rather than a mock.

**Reyna's pure side.** `reyna/extract.py` (PDF text via stdlib zlib, plus a
parser for numbered normative documents) and `reyna/emit.py` (a `Transcript`
builder whose `cite()` is the only way to add fields, so a rune without its
source is not expressible). Plus `archive.ingest` — **not all evidence arrives
over HTTP**: a records request comes back as an attachment, and an archive that
could only hold downloads would push the most authoritative documents outside the
evidence trail.

**The real run.** Springfield's genuine *Operating Policies and Procedures* →
**150 provisions, in document order, correctly nested** (Authority; Officers;
3.3.1 Notification under 3.3 under 3) → **1822 commands** → replayed into Hormiga
→ 1 policy, 150 provisions, 131 dated assertions, **282/282 runes citing the
archived bytes they came from**.

**Hormiga's side** is `import_reyna_transcript`: one file, one `compile_commit`
batch, one undo. And it **filters rather than trusts** — only model-building
verbs pass, so `use`, `config`, `deploy` and `effect` are refused. A transcript
is executable input from outside the application; an import that could switch
mantles or fire a holiday is not an import, it is a script, and nothing about a
harvested PDF should be able to become one. `tests/reyna_import_smoke.cpp`
enforces the identical filter, so the app cannot widen it by accident.

### Three bugs, all found by the seam test, none findable from one side

1. **A missing glyph field is silent — exactly as annotate.hpp warns.** The
   `policy` glyph declared no `source_url`/`snapshot`, so `set` succeeded, `get`
   returned the value, and **only `project_scene` dropped it**. The transcript
   plainly cited the policy; the app showed it uncited. Caught only because the
   test asserts *every* rune carries a citation — 151/152 is the kind of number
   nothing else notices.

2. **A revision carries one `text`; a published document sets 150.** Emit
   produced a single `revision` for the whole document, reasoning that the
   council adopted one document on one day. True about the *event*, wrong about
   the *assertion*: the whole policy resolved to nothing. The honest reading is
   that publishing makes 150 claims — "on 2025-10-06, 3.3.1 reads X" — sharing a
   date and a source. They compose without conflicting, a later targeted
   amendment still wins on date, and the shared snapshot regroups them. It also
   keeps text **off** the provision rune, where it would have been the second
   source of truth the design refuses.

3. **`urllib.robotparser` is not RFC 9309** (R2, earlier today) — first match in
   file order, not longest match, erring permissive.

### And the parser is honest about what it is

150/150 provisions with correct nesting, and artefacts: a heading sometimes
absorbs its first words of body ("Authority T"). Recorded as R6 rather than
polished away, under the rule the parser already follows: **losing structure is
recoverable, losing text is not** — so a doubtful heading is dropped rather than
text being cut out of the provision containing it.

The 41 MB agenda packet still does not parse in reasonable time (R5). It does not
block anything, and the archive already holds the bytes, so the parser can be
replaced without asking Springfield for a single byte again. That is the property
the archive-first ordering was for.

## 2026-08-16b — phase 1 BUILT and green; the first real bytes; and Laserfiche says no

The author caught a bad plan before it cost anything: Hormiga's roadmap had
"generate the website" as the next step, and the honest answer to *"did we scrape
anything? is Reyna built? why is the next step a website"* was **no, no, and it
should not have been.** The website argument was a *software* de-risk — and
every risk this project actually has is in the **data**. It is also true that
Hormiga's Builder already generates sites, so that step would mostly re-prove
something proven, on a synthetic council. Reordered in both repos.

**So: phase 1 is built.** `reyna/archive.py` (the evidence locker),
`reyna/harvest.py` (the polite boundary), `reyna/cli.py`, `tests/test_archive.py`.
Stdlib only — no dependencies, as promised.

**The exit test is green, and it is stronger than the one the roadmap asked
for.** The roadmap said "fetch the same document twice, a week apart." Instead
the test serves the document from a local server we control and **changes it
between fetches**: waiting a week would only prove the page did not change; this
proves we would notice if it did. Three fetches, two versions, one change caught,
plus 404-as-evidence, robots enforcement, append-only blobs and immutable records.

### Two bugs, and the better one is not the code

**`changed_since_last` was wrong by construction.** `Harvester.fetch` archives
the record before it returns, so by the time anyone could ask the store "did this
change", the "last" record *was* the new one — it compared the id against itself
and always answered "unchanged", including for a document that had visibly
changed. It read fine and died on the first test that changed a document.

The fix is not "be careful". **A question whose answer depends on whether you
asked before or after a write should not be asked of the store at all.** So
`fetch` now returns a `Fetch` holding the new record *and the last successful one
that preceded it*, and `changed` is computed where the before-state is
unambiguously in hand. `Archive.changed_since_last` is deleted; the trap is gone
rather than documented.

`changed` is also deliberately three-valued: **`None` is not `False`.** "We have
never looked at this" is a different claim from "it is the same as last time",
and collapsing them is how an archive starts lying quietly.

**`urllib.robotparser` is not RFC 9309** (R2). It returns the *first* matching
rule in file order; the standard says the *longest* match wins. So `Allow: /`
above `Disallow: /private` means "everything allowed" to the stdlib — it errs
**permissive**, which is the wrong direction when obeying robots.txt is a claim
we make in public. Surfaced by a test whose own robots.txt was written
ambiguously, which is the only reason it showed up at all. Not fixed yet, and
documented rather than left as a surprise.

### The first real harvest, and the finding that reshapes phase 2

Five records. `springfield-or.gov/city/city-council-meetings/` captured, then
re-fetched immediately and correctly reported **304 unchanged** against a real
server — the conditional path works outside a test.

Then: **`laserfiche.springfield-or.gov` returns `Disallow: /`.** The portal
holding every agenda packet and set of minutes before November 2024 disallows all
crawlers, blanket. Our harvester obeyed and refused, which is right, and which is
a wall across phase 2 exactly as it was planned.

**And the same hour, the way around it that is not a way around it:** agenda
packets are *also* served from `springfield-or.gov/wp-content/uploads/…`, whose
robots.txt permits everything. **A real 41.5 MB agenda packet from 2023-04-03 is
now archived.** Phase 2 is viable without touching Laserfiche.

Filed as R1, with the general lesson: a blanket `Disallow: /` on a records portal
is almost always the **vendor's shipped default**, not a policy the city chose —
so the other legitimate avenue is to *ask* (a note to the City Recorder, an
Oregon public-records request), and the thing we must not do is ignore the file.

**This is the whole argument for the reordering, demonstrated within an hour of
taking it.** A website built on the synthetic council would have told us nothing
about any of this.

## 2026-08-16 — phase 0's exit test is GREEN; phase 1 is unblocked

The gate was *"Hormiga hand-builds one Springfield meeting and the data model
survives contact with it."* Done, in Hormiga, as `src/civic.hpp` +
`tests/civic_smoke.cpp` — synthetic council, structure modelled on the real
Springfield *Operating Policies and Procedures*. Seven design claims went in and
came out as passing assertions. **Phase 1 (the evidence locker) is unblocked.**

Three findings that change what Reyna emits:

**Edges carry only `(relation, directed)` through a projection.** Void Core's
`link` accepts `--weight`, and `maiz::SceneWire` has no weight field, so it dies
at the projection. Consequence for us: **anything richer than a relation must be
a rune or a field.** Terms are runes; speaker method and confidence live on the
statement, not the edge.

**A command in our own concept page was not a real command.** The Hormiga-side
page had `link … --relation said-by --confidence 0.61 --method diarized`.
Corrected. Worth recording as a discipline note rather than an embarrassment:
**a transcript we have never replayed is a guess**, and the emitter should be
built against a live dispatcher from its first line — which is cheap, since Void
Core is `pip install`-able.

**The consumer already resolves change as a merge.** Hormiga sets an assertion's
strength to its adoption date in days and hands the set to `maiz::merge`, so
*later governs, same-day disagreement is ⊤*. Reyna therefore does **not** need to
decide which of two conflicting amendments wins, or to order anything: it emits
dated assertions and the consumer composes them. That removes a whole class of
judgement from the harvester, which is the right place for it not to be.

## 2026-08-12 — founded

Named by the author — **Reyna**, the queen, who does not forage or build but
*founds the colony* — and split out of Void Hormiga's design work on
[the civic record](../../VoidHormiga/okf/concepts/civic-record.md), which is the
first client and the reason this exists.

**The line that justifies a separate project**, from Hormiga's own analysis: *a
view over the model stays in Hormiga; a producer of the model from outside stays
out.* Reyna is the only piece on the author's list that is a producer. The
decisive argument is Hormiga's ground rule 5 — *vendor, don't depend* — which
cannot survive a speech-recognition stack. Moving the ML out is that rule working
as intended, not a compromise of it.

**Built on Void Core, not Void Maiz.** Void Core ships a real Python package
(`voidcore` 0.2.6, the C core as a DLL, and **no required deps — "holidays pull
their own deps when used"**), which is precisely Reyna's dependency model. Void
Maiz is the C++ *view* library; Reyna is batch and headless.

And the one place a UI seemed unavoidable turned out to belong elsewhere: **the
human confirmation step must be a dispatcher command**, so that naming a voice
cluster is logged, attributed and replayable. If it happened here it would happen
outside the consumer's log — the single most sensitive decision in the pipeline
would be the one thing with no audit trail. So Reyna proposes and Hormiga
confirms, the same propose-never-write shape as Allomone's Weaver. **Reyna is
headless by design, not by omission.**

## The research, held to Void Maiz's bar

*No mathematics unless it pays for itself* — the rule that got a sheaf framing
rejected for Allomone. Written up in [foundations](/concepts/foundations.md).

- **Lenses + the round-trip law** — already built in Void Core, and its docstring
  already names *a holiday's record⇄rune mapping* as the motivating case. Gives
  the definition this project runs on: **holiday = an effectful crossing + a pure
  lens.** It pays from experience rather than theory: Portfolio Manager wrote one
  such mapping three times and shipped a lossy-tag bug between the copies.
- **Lens composition** — the operation the pivot rule actually runs on, and
  **missing upstream**. Losslessness composes, which is the one-line proof that a
  pivot format is worth the extra hop. Asked for via Hormiga's message to Void
  Core.
- **Delta lenses** (Diskin; *coalgebras for a comonad*, arXiv:2108.00390) — both
  sides modelled as *categories of states and transitions*, so a change
  propagates **as a change**. Named as the upgrade re-harvesting will demand,
  since a re-harvest is a diff and not a world. Also, pleasingly, the formal
  object behind the author's own framing that *a policy is defined by its delta*.
- **Provenance semirings** (Green / Karvounarakis / Tannen, PODS 2007) — **the
  strongest find.** Annotate facts with semiring values and propagate them
  through queries; provenance polynomials record *how* inputs were combined. The
  framework explicitly covers **trust levels and clearance levels**, which is not
  an analogy to our method/confidence/publishability problem — it *is* it.
  Field-checking works for a claim from one source and **silently fails for a
  claim derived from two**, which is exactly what attribution is. Caveat flagged
  rather than papered over: Allomone composes with a join semilattice and this is
  a semiring; the exact correspondence should be worked out before it is claimed.
- **Functorial data migration** (Spivak / Wisnesky; Δ, Σ, Π adjoint) — admitted
  as **vocabulary for thinking, explicitly not as an implementation**, on the same
  terms Void Maiz admitted the sheaf framing's *behaviour* while rejecting its
  *vocabulary*. It buys a real checklist — "is this adapter a pullback, a left
  pushforward, or a right pushforward?" — and underwrites the pivot rule at the
  **schema** level where lenses do it at the **instance** level. We are not
  building CQL.
- **Memento, RFC 7089** — datetime negotiation and TimeMaps, supported by every
  major web archive. Two payments: uniform temporal access across archives, and
  the observation that it is *the same shape* as Void Core's `scry(state,
  context)` with `date` in the context. Two independent designs converging on
  "resource + preferred datetime ⇒ representation" is decent evidence the shape
  is right — and it means Reyna could plausibly **serve** Memento over its own
  archive, making the evidence locker readable by tools that already exist.

## The roadmap is front-loaded on risk

The evidence locker first — **change detection must work before anything depends
on it** — then **votes from minutes, which need no ML at all**, because minutes
record movers, seconders and votes by name as a matter of law. That phase
produces a publishable dataset on its own and puts every attribution risk behind
a product that already works without it.
