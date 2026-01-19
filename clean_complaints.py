import pdfplumber

def extract_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

contract_text = extract_text(r"C:\Users\anush\Downloads\car llm\data\cfpb_full_dbase_report.pdf")

with open("data/contract_text.txt", "w", encoding="utf-8") as f:
    f.write(contract_text)

print("Contract text extracted")
