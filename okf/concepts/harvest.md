---
type: Concept
title: Harvest — the boundary layer and the evidence locker
description: "How Reyna crosses into the world: per-platform adapters over generic crawling, the manners that make a crawler acceptable, the evidence record (and why Void Core already ships most of it), change detection as a comparison, and why a moved snapshot id is itself a finding."
tags: [status:draft, audience:all, confidence:proposed]
timestamp: 2026-08-12T00:00:00Z
---

# The claim

> **Fetching is easy. Being able to prove, in two years, what a page said on a
> given day is the hard part and the valuable one.**

That is what separates an archive from a scraper, and it is the reason this
project exists rather than a shell script. A civic dataset whose claims cannot be
checked is a rumour with better typography.

# The evidence record — mostly already built upstream

Every fetch is recorded **before anything is parsed**, and the archive is never
edited:

| field | where it comes from |
|---|---|
| URL, UTC timestamp, HTTP status and headers | the fetch — transport facts only Reyna knows |
| the **raw bytes** | the fetch, stored verbatim |
| a **snapshot id** | **`provenance(data)` in Void Core** |

The snapshot id is not ours to invent. Void Core's Scry ships `provenance(data)`
— *"a stable, order-independent snapshot id"*, pure, content-derived, no clock —
and `materialize(..., stamp=<field>)` writes it, so that *"an archive carries
proof of what snapshot it captured, and a reader can tell whether the live data
still matches"* ([Scry](../../../VoidCore/okf/concepts/scry.md)).

So the archive step is: **a holiday that snapshots, plus `materialize` with a
stamp.** What remained for us to design was much smaller than it looked.

**And the inherited rule matters as much as the mechanism:**

> Holiday-backed data is resolved from a **snapshot**, never folded into
> authoritative state at edit time.

For a civic record that is not hygiene, it is a provenance guarantee: harvested
claims stay visibly harvested until a person explicitly bakes them in.

## Change detection, and the finding hiding inside it

Because the id is content-derived, re-fetching and comparing is the whole
mechanism. There is no diffing infrastructure to build.

> **A snapshot id that moved on a document that is supposed to be final is
> itself a finding** — and arguably the most interesting thing this project
> could ever surface about a government.

Minutes are approved by vote and are not supposed to change afterward. A
silently edited transcript is exactly the thing a citizen cannot detect and an
archive can. This is not an adversarial assumption about any particular body; it
is the reason records are kept by someone other than their author.

# Per-platform adapters beat a generic crawler

Most US municipal records live on a handful of systems — Granicus/Legistar,
CivicClerk, PrimeGov, **Laserfiche**, NovusAGENDA — several of which expose a
folder or search API. Springfield is on Laserfiche WebLink, with video on
YouTube and GIS on an ArcGIS Hub.

So the strategy is the **pivot rule applied to sources**
([foundations §1a](/concepts/foundations.md)): write an adapter per *platform*,
not per *city*. Every other city on that platform is then nearly free, and the
generic HTML path is the fallback rather than the plan.

**Preference order, strongest first:**

1. a documented **API** (Legistar, Laserfiche, ArcGIS, the Wayback CDX API)
2. a **feed or sitemap** (RSS, `sitemap.xml`)
3. **structured HTML** with a stable shape
4. **rendered HTML**, parsed defensively — and re-checked, because it will break

# The manners that make a crawler acceptable

Web crawling has a bad name because of what bad crawlers do, not because
fetching public documents is fraught. What makes the Internet Archive acceptable
is not scale or special permission — it is manners, and the list is short:

- **Identify yourself** in the User-Agent, with a contact URL that a webmaster
  can actually reach.
- **Rate-limit per host**, and back off on 429/503. One request every few
  seconds is invisible to a city web server and fast enough for a weekly
  harvest — this is a *records* project, not a search engine.
- **Respect `robots.txt`.** Government portals generally permit document
  directories, because the documents are meant to be read.
- **Fetch conditionally** — `If-Modified-Since` / `ETag`. Polite, and it makes
  change detection nearly free.
- **Never re-download what the archive already holds.**

**Scope is the ethics.** Public records published by public bodies. Not social
media, nothing behind a login, nothing about private individuals. A narrow,
defensible target is also a tractable engineering target, which is a pleasant
coincidence and not an accident.

# Two external services, used rather than reinvented

- **The Wayback CDX API** lists every capture of a URL *with a content digest*,
  so a page's change history is readable **without downloading the captures**.
- **Save Page Now** pushes a URL into a third-party archive. This is worth more
  than it sounds: our own archive is precisely the evidence an accused party
  would dispute, and **a second witness we do not control is a different kind of
  claim**.
- **Memento (RFC 7089)** is the standard both speak — datetime negotiation and
  TimeMaps, supported by every major archive
  ([foundations §5](/concepts/foundations.md)). One protocol, every archive.

# Where this sits in the pipeline

    the world ──[ harvest holiday ]──▶ archive ──▶ pure transforms ──▶ commands
              impure, thin, polite    evidence   lenses/temper/scry   the product

The harvest layer should be **as thin as it is possible to make it**: fetch,
record, stop. Every judgement — what a document means, how it is structured, who
said what — belongs on the pure side, where it is testable with no network, and
re-runnable when we get it wrong. We will get it wrong; that is what the archive
is for.
