"""Print each PDF page as '=== page N ===' text. Exit 2 if no page has a text layer."""
import sys
from pathlib import Path

import pdfplumber


def page_texts(pdf: Path) -> list[str]:
    with pdfplumber.open(pdf) as doc:
        return [page.extract_text() or "" for page in doc.pages]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: pdf_text.py <pdf>")
    texts = page_texts(Path(sys.argv[1]))
    if not any(t.strip() for t in texts):
        print(f"no text layer in {sys.argv[1]}", file=sys.stderr)
        sys.exit(2)
    for n, t in enumerate(texts, 1):
        print(f"=== page {n} ===\n{t}")
