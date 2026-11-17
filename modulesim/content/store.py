"""Course content (Simplified): the module's notes as text files, with keyword search.

Interface:
    search(module, query, limit) -> list of passages
    get(passage_id) -> passage or None
    quote_matches(passage_id, quote) -> True if the quote really is in that passage

A passage is one paragraph of a note: {"id", "title", "text"}.
Ids look like "critical-path#2" (note file name, then paragraph number).

In the target design this is a meaning-based search index. Swapping it in
changes this file only, because callers use these three methods.
"""

import re
from pathlib import Path

NOTES_DIR = Path(__file__).parent / "notes"
_WORD = re.compile(r"[a-z]+")
_STOP = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "is", "it",
         "for", "by", "with", "as", "be", "this", "that", "are", "at", "not"}


def _words(text: str) -> list[str]:
    return [w for w in _WORD.findall(text.lower()) if w not in _STOP]


def _normalise(text: str) -> str:
    return " ".join(text.split()).lower()


class ContentStore:
    def __init__(self, notes_dir: Path = NOTES_DIR) -> None:
        self._passages: dict[str, dict] = {}
        self._by_module: dict[str, list[str]] = {}
        for module_dir in sorted(p for p in Path(notes_dir).iterdir() if p.is_dir()):
            module = module_dir.name.upper()
            for note in sorted(module_dir.glob("*.txt")):
                lines = note.read_text(encoding="utf-8").strip().split("\n\n")
                title = lines[0].lstrip("# ").strip()
                for n, paragraph in enumerate(lines[1:], start=1):
                    pid = f"{note.stem}#{n}"
                    self._passages[pid] = {"id": pid, "title": title,
                                           "text": " ".join(paragraph.split())}
                    self._by_module.setdefault(module, []).append(pid)

    def modules(self) -> list[str]:
        return sorted(self._by_module)

    def get(self, passage_id: str) -> dict | None:
        p = self._passages.get(passage_id)
        return dict(p) if p else None

    def quote_matches(self, passage_id: str, quote: str) -> bool:
        p = self._passages.get(passage_id)
        return bool(p and quote.strip() and _normalise(quote) in _normalise(p["text"]))

    def search(self, module: str, query: str, limit: int = 5) -> list[dict]:
        """Score each passage by how often the query words appear.

        A match in the note's title counts three times, and a passage that
        contains the whole query as a phrase gets a bonus.
        """
        terms = _words(query)
        phrase = _normalise(query)
        scored = []
        for pid in self._by_module.get(module.upper(), []):
            p = self._passages[pid]
            body, title = _words(p["text"]), _words(p["title"])
            score = sum(body.count(t) + 3 * title.count(t) for t in terms)
            if phrase and phrase in _normalise(p["text"]):
                score += 5
            if score:
                scored.append((score, pid))
        scored.sort(key=lambda s: (-s[0], s[1]))
        return [dict(self._passages[pid]) for _, pid in scored[:limit]]
