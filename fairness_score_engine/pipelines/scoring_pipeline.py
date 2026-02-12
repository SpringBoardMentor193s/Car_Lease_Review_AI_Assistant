"""
Scoring pipeline: ContractFacts -> FairnessReport
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from models.contract_facts import ContractFacts
from models.fairness_report import FairnessReport
from models.scoring_rules import ScoringRules
from engine.scorer import FairnessScorer

logger = logging.getLogger(__name__)


class ScoringPipeline:
    def __init__(
        self,
        rules_path: str = "data/scoring_rules.json",
        benchmarks_path: str = "data/market_benchmarks.json",
    ):
        self.rules_path = Path(rules_path)
        self.benchmarks_path = Path(benchmarks_path)
        self.rules = self._load_rules()
        self.benchmarks = self._load_benchmarks()
        self.scorer = FairnessScorer(self.rules, self.benchmarks)

    def run(self, facts: Union[ContractFacts, Dict[str, Any]]) -> FairnessReport:
        if isinstance(facts, ContractFacts):
            contract_facts = facts
        else:
            # Drop non-model keys (e.g., DB metadata like id/created_at).
            fact_fields = set(ContractFacts.__fields__.keys())
            sanitized_facts = {k: v for k, v in facts.items() if k in fact_fields}
            contract_facts = ContractFacts(**sanitized_facts)
        return self.scorer.score(contract_facts)

    def _load_rules(self) -> ScoringRules:
        if not self.rules_path.exists():
            raise FileNotFoundError(f"Missing scoring rules: {self.rules_path}")
        raw = self._read_json(self.rules_path)
        return ScoringRules(**raw)

    def _load_benchmarks(self) -> Dict[str, Dict[str, Any]]:
        if not self.benchmarks_path.exists():
            logger.warning("Market benchmarks missing; using empty defaults")
            return {}
        return self._read_json(self.benchmarks_path) or {}

    def _read_json(self, path: Path) -> Dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to read JSON: {path} ({e})")
