"""
Dispatcher argument quoting, pinned against Void Core SPEC 6.1.

WHY THIS FILE EXISTS. This four-line function has now been written wrong four
times, in three codebases, in two languages, and every failure was **silent
content corruption** rather than an error:

  1. Hormiga (C++, Aug 10) emitted a backslash AND a closing quote for an
     apostrophe, so an Allomone comment saying "don't" truncated the rest of
     the script.
  2. Reyna (Python, Aug 17) wrote `s.replace("\'", "'")`, which Python reads as
     replacing a quote with a quote -- a no-op that let every apostrophe in a
     corpus of municipal policy survive escaped.
  3. Void Core found the third (Aug 17): any value *ending* in a backslash puts
     it immediately before the closing quote, where the tokenizer reads the pair
     as an escaped apostrophe. The argument never closes, it swallows the rest
     of the line, and dispatch still reports ok.
  4. Void Maiz shipped `maiz::arg` (Aug 18) with the naive spelling, one day
     after Core documented the trap -- reported back, not yet adopted here.

Three independent implementations agreeing read as verification. It was three
copies of one blind spot. So this is pinned rather than trusted, against the
expectations in `VoidCore/conformance/cases/12-arg-quoting.vs`.

    python tests/test_quoting.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reyna.emit import json_arg, quote, _one_arg   # noqa: E402

BS = chr(92)
FAILS: list[str] = []


def check(cond, what: str) -> None:
    if not cond:
        FAILS.append(what)
        print(f"FAIL: {what}")


def main() -> int:
    # The trap, exactly as case 12 pins it: the correct spelling closes the
    # quote BEFORE the trailing backslash and emits it bare.
    check(_one_arg("C:" + BS) == "'C:'" + BS,
          f"a trailing backslash goes outside the quotes (got {_one_arg('C:' + BS)!r})")
    check(_one_arg("a" + BS * 3) == "'a'" + BS * 3,
          "a whole trailing RUN goes outside")

    # ...and the naive spelling, which is what upstream's case asserts corrupts.
    naive = "'" + ("C:" + BS).replace("'", BS + "'") + "'"
    check(naive != _one_arg("C:" + BS),
          "we do not emit the spelling upstream pins as corrupting")

    # The apostrophe: one backslash, not a backslash plus a quote.
    check(_one_arg("don't") == "'don" + BS + "'t'",
          f"an apostrophe escapes to one backslash (got {_one_arg(chr(39).join(['don', 't']))!r})")

    # A backslash NOT at the end is literal and must not be doubled: inside
    # single quotes args.c only consumes one before an apostrophe, so escaping
    # it would make a doubled backslash arrive as two.
    check(_one_arg("a" + BS + "b") == "'a" + BS + "b'",
          "an interior backslash is passed through untouched")

    # Everything a policy document is full of rides inside single quotes.
    for v in ['say "hi"', "a b\tc", "100%", "a;b|c", "-- flag", ""]:
        check(_one_arg(v).startswith("'") and _one_arg(v).endswith("'"),
              f"{v!r} needs no special handling")

    # quote() additionally collapses whitespace (the line-oriented wire); both
    # still share the escaping, which is the property that keeps them honest.
    check(quote("a\nb") == "'a b'", "quote collapses newlines")
    check(quote("x" + BS) == "'x'" + BS, "quote inherits the backslash rule")
    check(json_arg('{"a":"b  c"}') == '\'{"a":"b  c"}\'',
          "json_arg does NOT collapse whitespace inside a JSON string")

    if FAILS:
        print(f"\n{len(FAILS)} check(s) failed")
        return 1
    print("OK - quoting matches Void Core SPEC 6.1, including the backslash trap")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
