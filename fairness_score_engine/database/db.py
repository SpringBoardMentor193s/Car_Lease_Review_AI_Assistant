from typing import List, Dict, Any
from pathlib import Path
import sqlite3
from models.contract_facts import ContractFacts

class ContractFactsDB:
    def __init__(self, db_path: str = "contract_facts.db"):
        self.db_path = Path(db_path)
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contract_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    apr REAL,
                    monthly_payment REAL,
                    lease_term_months INTEGER,
                    down_payment REAL,
                    mileage_limit_per_year INTEGER,
                    overage_fee_per_mile REAL,
                    early_termination_policy TEXT,
                    residual_value_percent REAL,
                    late_fee_policy TEXT,
                    maintenance_responsibility TEXT,
                    buyout_price REAL,
                    warranty_coverage TEXT,
                    insurance_coverage TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def insert_contract_facts(self, facts: ContractFacts) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO contract_facts (
                    apr, monthly_payment, lease_term_months, down_payment,
                    mileage_limit_per_year, overage_fee_per_mile, early_termination_policy,
                    residual_value_percent, late_fee_policy, maintenance_responsibility,
                    buyout_price, warranty_coverage, insurance_coverage
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                float(facts.apr) if facts.apr else None,
                float(facts.monthly_payment) if facts.monthly_payment else None,
                facts.lease_term_months,
                float(facts.down_payment) if facts.down_payment else None,
                facts.mileage_limit_per_year,
                float(facts.overage_fee_per_mile) if facts.overage_fee_per_mile else None,
                facts.early_termination_policy,
                float(facts.residual_value_percent) if facts.residual_value_percent else None,
                facts.late_fee_policy,
                facts.maintenance_responsibility.value if facts.maintenance_responsibility else None,
                float(facts.buyout_price) if facts.buyout_price else None,
                facts.warranty_coverage,
                facts.insurance_coverage
            ))
            conn.commit()
            return cursor.lastrowid

    def get_all_contract_facts(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM contract_facts')
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]