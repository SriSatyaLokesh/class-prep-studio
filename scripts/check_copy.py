"""Flag n-word runs copied from the textbook. Usage: check_copy.py <textbook.pdf> <file>..."""
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pdf_text import page_texts  # noqa: E402


def normalise(text: str) -> list[str]:
    text = re.sub(r"-\r?\n", "", unicodedata.normalize("NFKC", text))
    return re.findall(r"[a-z0-9']+", text.lower())


def overlaps(source: str, target: str, n: int = 12) -> list[str]:
    src, tgt = normalise(source), normalise(target)
    grams = {tuple(src[i:i + n]) for i in range(len(src) - n + 1)}
    hits = []
    for i in range(len(tgt) - n + 1):
        phrase = " ".join(tgt[i:i + n])
        if tuple(tgt[i:i + n]) in grams and phrase not in hits:
            hits.append(phrase)
    return hits


def read_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return "\n".join(page_texts(path))
    if ext == ".pptx":
        from markitdown import MarkItDown

        return MarkItDown().convert(str(path)).text_content
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: check_copy.py <textbook.pdf> <file>...", file=sys.stderr)
        sys.exit(2)
    def read_or_exit(path: Path) -> str:
        try:
            return read_file(path)
        except Exception as e:  # corrupt PDF/PPTX raises pdfminer/markitdown errors
            print(f"cannot read {path}: {e}", file=sys.stderr)
            sys.exit(2)  # distinct from 1 (copy found)

    source = read_or_exit(Path(sys.argv[1]))
    if not source.strip():
        print(f"no text layer in {sys.argv[1]}", file=sys.stderr)
        sys.exit(2)
    found = False
    for f in sys.argv[2:]:
        if Path(f).is_dir():
            continue
        for phrase in overlaps(source, read_or_exit(Path(f))):
            print(f'{f}: "{phrase}"')
            found = True
    sys.exit(1 if found else 0)
