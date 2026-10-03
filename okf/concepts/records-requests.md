---
type: Concept
title: When the door is closed, ask
description: "The escalation ladder for material a harvester cannot reach — read the file, look for another host, write to the records officer, file a formal request — with the reasoning for each rung, the Oregon statutory specifics, and the Springfield/Laserfiche letter as a worked example. Answers R1."
tags: [status:current, audience:all, confidence:asserted]
timestamp: 2026-08-17T00:00:00Z
---

**Answers [R1](/developer_questions.md).** Springfield's Laserfiche portal —
which holds every agenda packet and set of minutes before November 2024 —
returns `Disallow: /`. Our harvester obeyed it and refused. This page is what we
do instead, written to generalise past that one portal, because every city has
some version of this door.

# The rule

> **A closed door is a reason to ask, not a reason to find another way in.**

This is not squeamishness, and it is not only ethics. It is the only version of
this project that survives contact with the organisation it is documenting. A
records project that routes around access controls has, on the first day it is
noticed, handed the body it is watching a reason to talk about *us* instead of
about the record — and it will be noticed, because the whole point is to publish.

There is also a practical asymmetry worth naming: **asking usually works, and it
is cheap.** A blanket `Disallow: /` on a records portal is almost always the
*vendor's* shipped default for load management, not a policy the city chose or
even knows about. Nobody at the city decided you should not read the minutes;
the minutes are public by law. The file is a configuration artifact.

# The ladder

Four rungs, cheapest first. Each is a real answer that ends the process most of
the time, and each is a step the *next* one is stronger for having taken.

### 1. Read the file properly

Before concluding anything: fetch `robots.txt` and read it, by hand, with the
standard in view. Ours is checked by `urllib.robotparser`, which is **not RFC
9309** — first match in file order rather than longest match, and it errs
*permissive* ([R2](/developer_questions.md)). So a machine "yes" is not
evidence; a machine "no" against a human read of the file is worth checking.

Distinguish, too, between what the file says and what it means:

- `Disallow: /` under `User-agent: *` — a blanket refusal. Obey it.
- A disallow on a `/search` or `/browse` path with the documents themselves
  permitted — that is a *load* rule about the expensive query endpoint, not a
  refusal of the documents. Respect the endpoint; the documents are fine.
- A `Crawl-delay` — an explicit invitation with a speed limit. Take it.

### 2. Look for another host

This is the rung that resolved Springfield within the hour, and it generalises
better than it looks. Public bodies publish the *same document* in several
places, because different offices put it there for different reasons: the CMS
upload directory, a department page, a press release, the agenda system, the
state archive, a newspaper's copy of record.

`springfield-or.gov/wp-content/uploads/…` permits everything and carries the
packets. **The same bytes, and the archive proves they are the same bytes** —
which matters, because the content id is what makes "we got this elsewhere" a
verifiable claim rather than an excuse.

Two limits to be honest about. Alternate hosts are usually **incomplete** — they
have this year's packets, not 2014's — so this rung often solves the immediate
task and not the corpus. And a third-party copy is *not* the same evidence as
the body's own publication; if you cite one, cite it as what it is.

### 3. Write to the records officer

An email, to a named person, from a named person. The whole content of this rung
is that most access problems are one message from being solved, and the message
costs ten minutes.

What it must contain:

- **Who you are, and that you are automated.** Do not bury this. The single most
  common reason a portal blocks crawlers is that some crawler previously behaved
  badly, and the fastest way to be treated as different is to say what you are
  and how slowly you run.
- **What you want, specifically.** "Agenda packets and minutes, 2014 to present"
  is answerable. "Access to your document portal" invites a lawyer.
- **Why the current route does not work**, factually and without accusation:
  the robots.txt says this, our harvester obeys it, so we stopped.
- **What you are offering.** A rate limit, a User-Agent they can allowlist, a
  window (overnight), a contact who answers, and — worth more than any of these
  — the fact that a public archive of their documents *reduces* their records
  workload. Every question your archive answers is a request they do not process.
- **A fallback ask**, so a "no" still moves: a bulk export, a sitemap, an API
  key, or simply confirmation that the alternate host is complete.

### 4. File a formal public-records request

The rung that exists so the others are not the end. It is slower and more
adversarial in tone than it needs to be, and it is also a **statutory right**,
which is the point: the material is public whether or not a web server agrees.

**Oregon specifics** (this project's jurisdiction — ORS 192.311–192.478):

- Requests go to the **custodian** of the record; for a city, the City Recorder.
- The body must **acknowledge within 5 business days** and respond within 15,
  with limited extensions.
- **Fees** may be charged for the actual cost of making records available, and
  may be **waived or reduced when disclosure is in the public interest** — which
  a free, cited, public archive is, and which is worth stating in the request
  rather than hoping is inferred.
- A denial may be appealed to the **District Attorney** (local bodies) — a real
  and routinely used avenue, not a threat to make in the first letter.
- Ask for the **native electronic format**. A PDF of a spreadsheet is a
  downgrade the law does not require you to accept, and re-deriving structure
  from a printout is where extraction errors come from.

Two things this project does that a records request usually does not:

1. **We archive the response as evidence.** `reyna ingest` exists for exactly
   this — material that arrives by post, email or a shared drive rather than
   HTTP, recorded with its origin, its content id and the fact that it did not
   come over the wire. Catalogue case 22 was written from this.
2. **We record a refusal too.** A denial is a fact about the record's
   availability, and `Cite.withheld` carries it. An archive that only holds what
   it was given cannot tell you what it was refused.

# What we are *not* doing

- **Not ignoring robots.txt**, including when we are confident the block is a
  vendor default. Confidence is not permission.
- **Not spoofing a browser User-Agent.** Ours identifies the project and a
  contact, which is most of the argument for why it is allowed to run at all.
- **Not using an authenticated session to get past a limit**, or scraping a
  portal's internal API because the HTML is hard.
- **Not going faster than 3 seconds per host**, ever, on the grounds that the
  documents are public. They are public; the server is still theirs.

# The Springfield letter

The worked example. Placeholders in `[brackets]`; nothing here is sent
automatically, and the author sends it or does not.

> **To:** City Recorder, City of Springfield, Oregon
> **Subject:** Access to archived agenda packets and minutes (Laserfiche portal)
>
> Dear City Recorder,
>
> I am building a free, public archive of Springfield city government records —
> agenda packets, minutes, and adopted policies — so that residents can see what
> the Council decided and when, with every claim linked back to the original
> document. It is a personal, non-commercial project. [name, contact]
>
> I am writing because of a technical block rather than a records dispute.
>
> The city's Laserfiche portal (`laserfiche.springfield-or.gov`) publishes a
> `robots.txt` that disallows all automated access. My software reads and obeys
> that file, so it does not retrieve anything from that host. I believe this is
> most likely the document system's shipped default rather than a decision the
> city made, but I did not want to assume that, and I did not want to work
> around it.
>
> Documents published under `springfield-or.gov` are reachable and I have been
> using those. What I am missing is the older material — my understanding is
> that packets and minutes before roughly November 2024 are only in Laserfiche.
>
> Three ways this could be resolved, in whichever order suits you:
>
> 1. **Confirm the block is not intentional**, and if so allow the user agent
>    `VoidReyna/0.1` in that `robots.txt`. My software requests **no more than
>    one document every three seconds**, identifies itself with a contact
>    address, fetches conditionally so unchanged documents are never downloaded
>    twice, and can run overnight or at any window you prefer.
> 2. **Point me at a bulk export or an index** of the archived packets and
>    minutes, in any format, and I will not touch the portal at all.
> 3. If neither is workable, treat this as a **request under ORS 192.311 to
>    192.478** for agenda packets and minutes of the City Council from [date] to
>    the present, in their native electronic format. I would ask that any fee be
>    waived or reduced under ORS 192.324(5), since the records will be made
>    freely available to the public with attribution to the city.
>
> I would rather do this the first way. I am also glad to describe exactly what
> the software does, or to show you the archive, if that is useful.
>
> Thank you for your time.
>
> [name] · [email] · [project URL]

Three deliberate features of that letter, for anyone writing the next one:

- **It offers a technical fix before invoking the statute.** The statute is the
  third option, phrased so a "no" to the first two still produces records.
- **It states the rate limit as a number.** "We are polite" is a claim; "one
  request every three seconds, conditional, overnight if you like" is a
  specification someone can evaluate in ten seconds.
- **It does not accuse anyone of hiding anything**, because as far as we know
  nobody is, and being wrong about that in writing costs the whole relationship.

# Generalising

Nothing above is specific to Laserfiche or to Oregon except the statute numbers
and the letter. The reusable parts:

| situation | rung |
|---|---|
| robots.txt disallows the path we want | 1, then 2 |
| the documents exist elsewhere on a permitted host | 2 |
| the portal is JavaScript-only or paginated with no stable URLs | 3 — ask for the export; do not reverse-engineer the API |
| a login or a captcha stands in front of public records | 3 then 4; never 0 |
| the body says no | 4, then the DA appeal, then publish the refusal |
| the body says yes, on a CD | `reyna ingest`, and cite the origin |

The last row is the one worth remembering. **The pipeline was built so that
evidence arriving by post is a first-class citizen**, not a special case — which
is what makes rung 4 an actual part of the system rather than a place the
software gives up.
