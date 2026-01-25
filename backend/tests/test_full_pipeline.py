from backend.pipeline.process_contract import process_contract

PDF_PATH = "data/business-finance-lease-agreement_used-vehicle.pdf"

result = process_contract(PDF_PATH)

print("\n===== FINAL OUTPUT =====\n")
print(result)
