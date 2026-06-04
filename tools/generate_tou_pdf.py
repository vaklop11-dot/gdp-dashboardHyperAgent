from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pathlib import Path

md_path = Path(__file__).parents[1] / 'TERMS_OF_USE.md'
pdf_path = Path(__file__).parents[1] / 'TERMS_OF_USE.pdf'

text = md_path.read_text(encoding='utf-8')

c = canvas.Canvas(str(pdf_path), pagesize=A4)
width, height = A4

left = 50
top = height - 50
line_height = 14

lines = text.splitlines()

y = top
for line in lines:
    # naive wrap for long lines
    if not line:
        y -= line_height
        continue
    # Simple wrapping
    max_chars = 90
    while len(line) > max_chars:
        chunk = line[:max_chars]
        c.drawString(left, y, chunk)
        y -= line_height
        line = line[max_chars:]
    c.drawString(left, y, line)
    y -= line_height
    if y < 80:
        c.showPage()
        y = top

c.save()

print(f"Generated PDF at: {pdf_path}")
