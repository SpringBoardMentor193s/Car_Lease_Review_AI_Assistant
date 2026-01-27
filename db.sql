CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS contract_sla (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  contract_id UUID,
  apr_percent VARCHAR(20),
  term_months INT,
  monthly_payment VARCHAR(40),
  down_payment VARCHAR(40),
  residual_value VARCHAR(40),
  mileage_allowance_yr INT,
  mileage_overage_fee VARCHAR(40),
  early_termination_fee VARCHAR(40),
  purchase_option_price VARCHAR(40),
  insurance_requirements TEXT,
  maintenance_resp TEXT,
  warranty_summary TEXT,
  late_fee_policy TEXT,
  other_terms JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);