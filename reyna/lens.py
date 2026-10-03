"""
reyna/lens.py — the round-trip law, now Void Core's implementation.

WAS ~60 LINES, IS NOW A RE-EXPORT. This file used to carry its own `Lens`,
written deliberately API-compatible with Void Core's `scry/lens.py` but defined
here so the law was available under `dependencies = []`. We asked Void Core
whether their version could be imported without the compiled engine; the answer
(2026-08-17) was yes, *and* they added `pure_import_test.py` — which poisons
`ctypes.CDLL` so any load-on-import raises — so that it stays yes. That test
existing is what justified deleting our copy; "it happens to work today" would
not have.

So the law now has ONE implementation again, which is the whole argument the
Lens itself makes, applied to the Lens.

VENDORED, NOT IMPORTED — see `vendor/voidcore/README.md`. Rule 2 says the
evidence locker works on a fresh checkout with nothing installed, and a sibling
repo on disk is a dependency like any other.

WHAT CHANGED FOR CALLERS. `Lens` is the same shape (`forward`, `backward`,
`normalize`, `label`; `check`, `check_inverse`, `inverse`, `compose`,
`identity`, `pipeline`). The report is **richer**: it carries `mismatches` —
`(index, key, expected, got)`, a structured diff rather than the whole pair —
and prints through `.render()`. That is strictly better for a large document,
where our version printed two 300-character strings that looked identical.

`compose` also gained an explicit `normalize=` override. Its default is our
correction: `self.normalize or other.normalize`, because **`None` means no
opinion, not no normalization** — we proposed the wrong version, built it,
watched it fail on the first real composition, and sent the fix.
"""

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path

# `lens.py` does `from roundtrip import …` — a flat import — so its directory
# has to be on the path, and both files must stay side by side.
_VENDOR = _Path(__file__).resolve().parents[1] / "vendor" / "voidcore"
if str(_VENDOR) not in _sys.path:
    _sys.path.insert(0, str(_VENDOR))

from lens import Lens, pipeline            # noqa: E402,F401
from roundtrip import RoundTripReport, check_roundtrip   # noqa: E402,F401

__all__ = ["Lens", "pipeline", "RoundTripReport", "check_roundtrip"]
