SLA_FIELDS = [
    "APR",
    "TermMonths",
    "MonthlyPayment",
    "DownPayment",
    "ResidualValue",
    "MileageAllowancePerYear",
    "MileageOverageFee",
    "EarlyTerminationFee",
    "PurchaseOptionPrice",
    "InsuranceRequirements",
    "MaintenanceResponsibilities",
    "WarrantySummary",
    "LateFeePolicy",
    "OtherTerms"
]

def empty_sla():
    return {
        "APR": None,
        "TermMonths": None,
        "MonthlyPayment": None,
        "DownPayment": None,
        "ResidualValue": None,
        "MileageAllowancePerYear": None,
        "MileageOverageFee": None,
        "EarlyTerminationFee": None,
        "PurchaseOptionPrice": None,
        "InsuranceRequirements": None,
        "MaintenanceResponsibilities": None,
        "WarrantySummary": None,
        "LateFeePolicy": None,
        "OtherTerms": None
    }