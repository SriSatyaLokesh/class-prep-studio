"""Write synthetic sample PDFs into inputs/ (never overwrites). Usage: make_sample_inputs.py"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors

S = getSampleStyleSheet()
H, B = S["Heading2"], S["BodyText"]

TEXTBOOK = [
    [("Chapter 3: Ohm's Law and Kirchhoff's Laws", "h"),
     ("3.1 Definitions", "h"),
     ("Electric current is the rate at which charge moves past a point in a wire. It is measured in amperes (A).", "b"),
     ("Voltage is the energy given to each unit of charge as it moves between two points. It is measured in volts (V).", "b"),
     ("Resistance is how strongly a component opposes current. It is measured in ohms.", "b"),
     ("Ohm's law says that for a resistor at steady temperature, the voltage across it equals the current through it "
      "multiplied by its resistance: V = I x R.", "b")],
    [("3.2 Worked example: a series circuit", "h"),
     ("A 12 V battery drives three resistors in a single loop: R1 = 2 ohms, R2 = 4 ohms and R3 = 6 ohms.", "b"),
     ("In a series loop the same current passes through every resistor, and the resistances add: "
      "R total = 2 + 4 + 6 = 12 ohms.", "b"),
     ("The current is I = V / R total = 12 / 12 = 1 A. The voltage drops are 2 V, 4 V and 6 V, which sum to 12 V.", "b")],
    [("3.3 Worked example: a parallel circuit", "h"),
     ("The same 12 V battery now feeds two branches side by side: R1 = 6 ohms and R2 = 12 ohms.", "b"),
     ("In parallel every branch has the full battery voltage across it. Each branch current is found separately: "
      "I1 = 12 / 6 = 2 A and I2 = 12 / 12 = 1 A.", "b"),
     ("The battery supplies the sum of the branch currents, 3 A. The combined resistance is 12 / 3 = 4 ohms, "
      "which is smaller than either branch.", "b")],
    [("3.4 Kirchhoff's laws", "h"),
     ("Kirchhoff's current law (KCL): the currents flowing into a junction add up to the currents flowing out of it.", "b"),
     ("Kirchhoff's voltage law (KVL): going once around any closed loop, the rises and drops in voltage add up to zero.", "b"),
     ("Example with two loops: a 10 V source feeds a junction. One branch holds a 5 ohm resistor and the other branch "
      "holds a 10 ohm resistor. KCL at the junction gives I total = I1 + I2. KVL around each loop gives "
      "10 = 5 x I1 and 10 = 10 x I2, so I1 = 2 A, I2 = 1 A and I total = 3 A.", "b")],
    [("3.5 Common mistakes", "h"),
     ("<b>Common mistakes box.</b>|Many learners say that current splits up in a series circuit and that voltage is shared "
      "in a parallel circuit. This swaps the two cases.|Remember: series means one path, so the current is the same "
      "everywhere and the voltage is shared. Parallel means several paths, so the voltage is the same on every branch "
      "and the current is shared.|Another slip is adding parallel resistances like series ones. Parallel resistance is "
      "always lower than the smallest branch.", "box")]]

SYLLABUS = [
    ("Unit 2: DC Circuits", "h"),
    ("Course outcomes covered in this unit:", "b"),
    ("CO-1: State and apply Ohm's law.", "b"),
    ("CO-2: Apply KCL and KVL to simple circuits.", "b"),
    ("CO-3: Analyse series and parallel resistor networks.", "b"),
]


def _build(path: Path, pages: list[list[tuple[str, str]]], numbered: bool) -> None:
    from reportlab.platypus import PageBreak

    def footer(canvas, doc):
        if numbered:
            canvas.setFont("Helvetica", 10)
            canvas.drawCentredString(A4[0] / 2, 30, f"Page {doc.page}")

    flow = []
    for i, page in enumerate(pages):
        if i:
            flow.append(PageBreak())
        for text, kind in page:
            if kind == "box":
                box = Table([[[Paragraph(t, B) for t in text.split("|")]]], colWidths=[400])
                box.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, colors.red),
                                         ("BACKGROUND", (0, 0), (-1, -1), colors.mistyrose)]))
                flow.append(box)
            else:
                flow.append(Paragraph(text, H if kind == "h" else B))
            flow.append(Spacer(1, 8))
    SimpleDocTemplate(str(path), pagesize=A4).build(flow, onFirstPage=footer, onLaterPages=footer)


def main(inputs: Path = Path("inputs")) -> list[Path]:
    inputs.mkdir(parents=True, exist_ok=True)
    written = []
    for name, pages, numbered in (("textbook-chapter.pdf", TEXTBOOK, True), ("syllabus-unit.pdf", [SYLLABUS], False)):
        path = inputs / name
        if not path.exists():
            _build(path, pages, numbered)
            written.append(path)
    return written


if __name__ == "__main__":
    for p in main():
        print(f"wrote {p}")
