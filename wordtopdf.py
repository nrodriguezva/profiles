from docx import Document
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

docx_file = "archivo.docx"
pdf_file = "archivo.pdf"

doc = Document(docx_file)

pdf = SimpleDocTemplate(pdf_file)
styles = getSampleStyleSheet()

content = []

for para in doc.paragraphs:
    text = para.text.strip()
    if text:
        content.append(Paragraph(text, styles['Normal']))
        content.append(Spacer(1, 12))

pdf.build(content)

print("PDF generado")

pip install python-docx reportlab
