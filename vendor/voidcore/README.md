# Vendored from Void Core

`lens.py` and `roundtrip.py`, copied verbatim from `../VoidCore/scry/` on
**2026-08-18**. `LICENSE` is Void Core's, carried with them.

## Why vendored rather than imported

Rule 2 of this repo is that the evidence locker must work on a fresh checkout
with nothing installed — the thing that proves what a document said in 2026
should not need a working toolchain, or a sibling repo on disk, in 2031.

Void Core's agent confirmed on 2026-08-17 that `from voidcore import Lens`
loads **no compiled library** (`ctypes.CDLL` is called inside `VoidCore.__init__`,
never at module scope), and added `voidcore/pure_import_test.py` — which poisons
`CDLL` so any load-on-import raises — specifically so we could rely on that in
2031 rather than on it happening to be true today. They also confirmed that
vendoring *exactly these two files* is a supported path and that they will keep
it working.

So this is not distrust of the package; it is the same "vendor, don't depend"
rule the rest of the family follows, applied to the one structure that
guarantees we are not losing public records.

## What we deleted in exchange

`reyna/lens.py` was ~60 duplicated lines. It is now a thin re-export of these
files, so there is one implementation of the round-trip law again.

## The one thing we contributed back

`compose`'s normalizer is `self.normalize or other.normalize`. We proposed
`self.normalize` to Void Core, built it that way, watched it fail on the first
real composition, and sent the correction — `None` means *no opinion*, not *no
normalization*. That is the version in this file, with our case named in its
docstring.

## Refreshing

Re-copy both files together (`lens.py` does `from roundtrip import …`, a flat
import, so they must stay side by side) and re-run `python tests/run_all.py`.
