# Void Reyna

**A dataset generator.** It harvests the unstructured public world, archives what
it fetched as evidence, transforms it through pure mappings with laws attached,
and emits the result as a [Void Core](../VoidCore) command transcript.

*Reyna* — the queen. A queen ant does not forage or build; she **founds the
colony**. This founds a dataset; [Void Hormiga](../VoidHormiga) then keeps it,
maps it, dates it and publishes it.

**Status: design only. Nothing is built.** Start at [`okf/index.md`](okf/index.md).

---

## The idea in four steps

    HARVEST   fetch public records politely — portals, PDFs, video, GIS
      ↓
    ARCHIVE   raw bytes + URL + timestamp + a content-derived snapshot id
      ↓
    EXTRACT   pure transforms: parse, structure, normalize, cluster
      ↓
    EMIT      a transcript of Void Core commands

**The archive is the product.** Fetching is easy; being able to prove in two
years what a page said on a given day is the hard and valuable part.

## What makes it different from a scraper

- **Nothing is parsed before it is archived, and the archive is never edited.**
  Every claim points back at the bytes it came from, at a timestamp.
- **Impurity lives at one boundary.** Network, disk and *models* are boundary
  work; everything downstream is a pure function of what the boundary recorded —
  so a run is re-runnable without a GPU and testable without a network.
- **It emits verbs, not data structures.** No shared header, no schema to keep in
  sync. A tool that emits a text transcript is a tool nobody is locked into.
- **Models distinguish; humans identify.** A model may propose that forty
  segments are one voice. Only a person may say whose — and that confirmation
  happens in the consuming application, as a logged command.

## First client

Void Hormiga's [civic record](../VoidHormiga/okf/concepts/civic-record.md): a
public website monitoring Springfield, Oregon's city government.

## License

MIT (intended; not yet added).
