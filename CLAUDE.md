# Void Reyna — agent instructions

You are working on **Void Reyna**, a Python application that **manufactures
datasets out of the unstructured public world** and emits them as Void Core
command transcripts. It is built on **Void Core** (`../VoidCore` — the engine,
which ships a real Python package). Its first client is **Void Hormiga**
(`../VoidHormiga`), which keeps, maps, dates and publishes what Reyna produces.

**Reyna** — the queen. A queen ant does not forage or build; she *founds the
colony*. This founds a dataset.

## Ground rules

1. **OKF first.** `okf/` is the source of truth; code follows concepts. Every
   session that changes design or code captures it in `okf/log.md` and trues up
   the affected concept docs. Read `okf/index.md` before doing anything.
2. **The repo root is a public artifact.** No harvested content, no personal
   data, no credentials, no API keys — ever, in any commit. Harvested material
   lives only where the tool puts it at runtime, and that path is gitignored.
3. **The archive is the product; the parser is disposable.** Fetching is easy.
   Being able to prove, in two years, what a page said on a given day is the
   hard part and the valuable one. Nothing is parsed before it is archived, and
   **the archive is never edited**.
4. **Impurity lives at the boundary, and nowhere else.** Void Core's banked
   invariant: *effects live at the holiday boundary; none of reduce/temper/scry
   ever fires one.* Network, disk and **models** are boundary work. Everything
   downstream must be a pure function of what the boundary recorded — which is
   what makes a run re-runnable without a GPU.
5. **We emit VERBS, not data structures.** The contract with Hormiga is
   `../VoidHormiga/okf/verbs.md` — a command transcript, nothing linked, no
   shared header, no schema to keep in sync. A tool that emits text is a tool
   nobody is locked into.
6. **Models distinguish; humans identify.** A model may propose a grouping.
   Only a human may attach a name to it, and that confirmation happens in
   **Hormiga**, as a dispatcher command, so it is logged and replayable. Reyna
   proposes and never asserts identity. See `okf/concepts/attribution.md`.
7. **Scope is public records published by public bodies.** Not social media,
   nothing behind a login, nothing about private individuals. The narrowness is
   the ethics, and it is also what keeps the crawler defensible.
8. **Upstream messages, not upstream edits.** Void Core and Void Maiz gaps are
   drafted at this repo root as `MESSAGE_FOR_<RECIPIENT>_reyna-<topic>-<date>.md`
   for the author to relay. A consumed message folds into `okf/log.md` and is
   then deleted — the log is the durable record.
9. **The author decides.** Open decisions go to `okf/developer_questions.md`
   with a lean; answers fold into concepts and clear from there.

## What this is NOT

- **Not a view.** No canvas, no node graph, no Void Maiz. Reyna is headless and
  batch; its review surface is Hormiga's, because confirmation must be a logged
  command (see rule 6).
- **Not a general web crawler.** It is a harvester with an evidence locker,
  aimed at a known, narrow set of public sources.
- **Not a place for an LLM to write published text.** An LLM's output is
  irreproducible *and* uncitable, which fails both rule 4 and the archive's
  reason for existing.
