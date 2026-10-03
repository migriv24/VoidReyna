"""Void Reyna — a dataset generator. See okf/index.md.

Phase 1 is the evidence locker and nothing else: harvest politely, archive the
bytes, stamp a content-derived id, prove what changed. No parsing lives here yet
and none should until this is trustworthy.
"""

from .archive import Archive, Record, content_id, utc_now_iso
from .harvest import Harvester, Politeness, USER_AGENT

__all__ = [
    "Archive", "Record", "content_id", "utc_now_iso",
    "Harvester", "Politeness", "USER_AGENT",
]
__version__ = "0.1.0"
