---
type: Reference
title: Foundations — the mathematics, and what each piece buys
description: "Every mathematical idea Void Reyna rests on, paired with what it makes simpler: state-based lenses and the round-trip law (built upstream), delta lenses as the change-propagation upgrade, provenance semirings as the algebra of method and trust, functorial data migration as vocabulary-for-thinking, and Memento as the protocol the design already resembles. Includes what was evaluated and declined."
tags: [status:draft, audience:dev, confidence:proposed, research]
timestamp: 2026-08-12T00:00:00Z
---

**The rule this page enforces**, inherited from Void Maiz's
[allomone/foundations §7](../../../VoidMaiz/okf/concepts/allomone/foundations.md):

> No piece of mathematics appears here unless it **pays for itself** by making
> the implementation simpler or by guaranteeing a property we would otherwise
> have to test for. Vocabulary that only makes the design sound impressive is a
> liability — it invites contributors to reason in a frame the code does not
> implement.

That page rejected a sheaf-theoretic framing on exactly this ground, twice over.
The bar is real. Each section below states what it buys, and one section states
that it buys thinking rather than code.

# The table

| Concept | Mathematics | Where it lives | What it buys |
|---|---|---|---|
| An adapter that loses nothing | state-based **lens** + round-trip law | `VoidCore/scry/lens.py` — **built** | one mapping instead of three; lossy adapters caught structurally |
| Chaining adapters | **lens composition** | **missing upstream** — asked for | the pivot rule becomes a theorem: lossless ∘ lossless = lossless |
| Re-harvesting | **delta lens** | designed, not built | propagate what changed instead of recomputing the world |
| Method, confidence, publishability | **provenance semiring** | designed, not built | one algebra carries "where from / how / may it be published" through every transformation |
| Schema-level migration | functorial data migration (Δ, Σ, Π) | **thinking only** | a checklist of the three canonical ways to move data along a mapping |
| Time-indexed archives | **Memento** (RFC 7089) | a protocol to speak | uniform "what did this look like on date D" across every major archive |

# 1. Lenses, and the law that catches a lossy adapter

A **lens** is a pair of mappings with a law: `forward : A → B`, `backward :
B → A`, and `backward(forward(x)) == x`. Void Core ships it, and its docstring
names *a holiday's record⇄rune mapping* as the motivating case:

> Pure (no I/O) — **the holiday still does the file/network; the Lens is just the
> mapping + law.** — `VoidCore/scry/lens.py`

So the account of a holiday, which is the load-bearing definition of this whole
project:

> **holiday = an effectful boundary crossing + a pure lens.**

**What it buys, concretely and from experience rather than theory:** Portfolio
Manager wrote one record⇄rune mapping three times — persistence, form read-side,
form write-side — and shipped a lossy-tag bug between the copies. One lens owns
the mapping once and `lens.check(samples)` is the regression guard. For an
archive the stakes are higher than a UI bug: **a lossy import is an altered
public record.**

## 1a. Composition, and the pivot rule

Lenses compose, and composition is the operation the design actually runs on:

    (A ⇄ B) ∘ (B ⇄ C)  =  A ⇄ C
    forward  = g.forward  ∘ f.forward
    backward = f.backward ∘ g.backward

**And losslessness composes.** If both legs satisfy the round-trip law, so does
the composite — a one-line proof, and the entire justification for routing
through a pivot format instead of writing direct adapters:

    polygon ⇄ geometry ⇄ map
    voxel   ⇄ geometry ⇄ map        ← one new lens
    voxel   ⇄ geometry ⇄ heatmap    ← free; nothing written

Direct adapters cost one per **pair**; a pivot costs one per **format**. Hence
the standing rule:

> **Never write a direct A→B holiday when A→pivot→B exists. If no pivot exists,
> naming one is the first job.**

**Void Core's `Lens` has `check`, `check_inverse` and `inverse()` but no
`compose`.** Asked for in
`../VoidHormiga/MESSAGE_FOR_VOIDCORE_hormiga-lens-composition-2026-08-12.md`.
Not blocking — chaining by hand is easy — but a rule whose supporting law each
host must re-prove is a rule that will quietly stop being followed.

# 2. Delta lenses — the upgrade re-harvesting will demand

A state-based lens maps **states**. A **delta lens** maps *changes*: both sides
are modelled as **categories of states and transitions**, and the
consistency-restoration operation knows *which transition occurred* rather than
merely the state it produced ([nLab](https://ncatlab.org/nlab/show/delta+lens);
Diskin et al.; [delta lenses as coalgebras for a
comonad](https://arxiv.org/abs/2108.00390), which characterises them as an
algebraic generalisation of split opfibrations).

**Why this is not decoration here.** Re-harvesting a portal produces a *diff*,
not a world: one new PDF among four hundred unchanged ones. A state-based lens
has no way to say so — you re-run everything and hope the outputs match. A delta
lens is the object that propagates "this one provision changed" through the
pipeline as a change.

It is also, precisely, the mathematics of the author's own framing of a policy:
*defined by its delta.* The consuming model treats a policy's history as a set of
dated assertions ([civic
record](../../../VoidHormiga/okf/concepts/civic-record.md)), and a delta lens is
the transformation that carries an assertion across a mapping without
reconstituting the document.

**Status: designed, not built, and deliberately not first.** State-based lenses
plus full re-derivation are correct and slow; correctness first. This is the
named upgrade path so nobody has to rediscover it.

# 3. Provenance semirings — one algebra for "where from, how, and may we publish"

**The strongest find of the research session.** Annotate each atomic fact with a
value in a commutative semiring and propagate the annotations through queries,
tracking whether information was used *alternatively* (`+`, disjunction) or
*jointly* (`×`, conjunction). **Provenance polynomials** — the most general model
in the framework — record *how* inputs were combined to produce a result
([Green, Karvounarakis & Tannen, PODS
2007](https://web.cs.ucdavis.edu/~green/papers/pods07.pdf); the [semiring
framework](https://www.cis.upenn.edu/~val/15MayPODS.pdf), and recent extensions
to first-order logic with negation,
[arXiv:2412.07986](https://arxiv.org/pdf/2412.07986)).

The line that makes it ours: **the same framework covers multiplicities, trust
levels, costs and *clearance levels*.** That is not an analogy to our problem, it
*is* our problem:

| our annotation | the semiring reading |
|---|---|
| which harvest a claim came from | why-provenance |
| `labeled` / `diarized` / `inferred` / `human` | a method annotation |
| confidence | a numeric annotation |
| **may this be published?** | a **clearance** annotation |

**What it buys.** Today's plan is to carry `method` and `confidence` as fields on
an edge and check them at the export seam. That works for a claim that came from
one place. It stops working the moment a claim is *derived* from two — "this
statement is attributed to X because cluster 7 was named X and segment 142 is in
cluster 7" — because then the question "is this publishable" is a question about
a *combination*, and hand-written propagation rules are where such things go
wrong silently. A semiring answers it by construction: annotations propagate
through `+` and `×`, and the publishability check reads the result.

**The honest caveat.** Allomone composes opinions with a **join semilattice**;
this is a **semiring**, with two operations. The security/clearance instance of
the semiring framework is lattice-shaped, so the two are plainly related, but
**the exact correspondence is something to work out before claiming it**, not
after. Flagged rather than asserted.

# 4. Functorial data migration — vocabulary for thinking, not code

Schemas as **categories**, instances as **set-valued functors**, and a functor
between schemas inducing **three adjoint migration functors** — Δ (pullback), Σ
and Π (the two pushforwards) — that translate instances canonically
([Spivak](https://arxiv.org/pdf/1502.05947); [relational
foundations](https://arxiv.org/pdf/1212.5303); implemented in CQL/FQL).

**What it genuinely buys: a checklist.** When writing an adapter, "which of the
three is this?" is a real and clarifying question — is this a *pullback* (read
the target's shape through the mapping), a *left pushforward* (union-like, freely
generate what the target needs), or a *right pushforward* (join-like, take only
what is fully determined)? Getting a Σ where a Π was meant is a class of import
bug that otherwise gets found in the data months later.

It also underwrites the pivot rule one level up from lenses: lenses give the
**instance**-level law, functoriality gives the **schema**-level one — migrations
compose because functors do.

**What it does not buy: an implementation.** We are not building CQL, our schemas
are not finitely-presented categories, and adopting the vocabulary wholesale
would invite contributors to reason in a frame the code does not implement —
exactly the failure mode Void Maiz's rule exists to prevent. **Use it to think;
do not cite it to decide.**

# 5. Memento (RFC 7089) — the protocol our design already resembles

[RFC 7089](https://www.rfc-editor.org/rfc/rfc7089) adds a time dimension to HTTP:
**datetime negotiation** (ask for a resource *as it was* at a preferred datetime)
and **TimeMaps** (an enumeration of a resource's prior states). It is supported
by every major web archive, including the Internet Archive.

Two payments:

1. **Uniform temporal access.** "What did this page look like on 2019-06-01" is
   one protocol against every archive, instead of one scraper per archive.
2. **It is the same shape we already have.** Void Core's `scry(state, context)`
   with `date` in the context is *datetime negotiation for a mantle*. That two
   independent designs converged on "the resource plus a preferred datetime
   yields a representation" is decent evidence the shape is right — and it means
   Reyna could plausibly **serve** Memento over its own archive, making the
   evidence locker readable by tools that already exist.

# 6. What we are not doing, and why

- **No sheaf/cohomology framing.** Void Maiz evaluated and rejected it for
  Allomone on two independent grounds, and neither is weaker here.
- **No CQL implementation.** §4.
- **No generative model in the pipeline.** An LLM's output is irreproducible
  *and* uncitable, which fails both the boundary invariant and the archive's
  reason for existing. A small bounded local model, recorded with its version,
  is fine — the objection is to generation, not to models.
- **No general-purpose crawler.** [harvest](/concepts/harvest.md) argues
  per-platform adapters instead, which is the pivot rule applied to sources.

# Sources

- Green, Karvounarakis & Tannen, *Provenance Semirings*, PODS 2007 —
  <https://web.cs.ucdavis.edu/~green/papers/pods07.pdf>
- Tannen, *The Semiring Framework for Database Provenance* —
  <https://www.cis.upenn.edu/~val/15MayPODS.pdf>
- *Provenance Analysis and Semiring Semantics for First-Order Logic* —
  <https://arxiv.org/pdf/2412.07986>
- Spivak, *Functorial Data Migration: From Theory to Practice* —
  <https://arxiv.org/pdf/1502.05947>
- Spivak & Wisnesky, *Relational Foundations for Functorial Data Migration* —
  <https://arxiv.org/pdf/1212.5303>
- Clarke, *Delta lenses as coalgebras for a comonad* —
  <https://arxiv.org/abs/2108.00390>
- Van de Sompel, Nelson & Sanderson, *HTTP Framework for Time-Based Access to
  Resource States — Memento*, RFC 7089 — <https://www.rfc-editor.org/rfc/rfc7089>
