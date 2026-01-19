from pathlib import Path
from models.contract_facts import ContractFacts
from models.scoring_rules import ScoringRules
from models.fairness_report import FairnessReport
import json


OUTPUT_DIR = Path("schemas")
OUTPUT_DIR.mkdir(exist_ok=True)


def write_schema(model, filename: str):
    schema = model.schema()
    (OUTPUT_DIR / filename).write_text(
        json.dumps(schema, indent=2, default=str)
    )
    print(f"Generated {filename}")


if __name__ == "__main__":
    write_schema(ContractFacts, "contract_facts.schema.json")
    write_schema(ScoringRules, "scoring_rules.schema.json")
    write_schema(FairnessReport, "fairness_report.schema.json")
