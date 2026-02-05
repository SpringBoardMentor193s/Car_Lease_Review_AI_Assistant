# SLA Extraction with Contract Fairness Score - Quick Reference

## Overview

Extract 11 key parameters from car lease contracts and provide a **Contract Fairness Score (0-100)** with detailed assessment.

---

## Required SLA Parameters to Extract

### 1. Interest Rate / APR
- Extract APR percentage or money factor
- Convert money factor to APR if needed (Money Factor × 2400 = APR)
- Compare to market rates

### 2. Lease Term Duration
- Length in months (typically 24, 36, 48)
- Start/end dates if available

### 3. Monthly Payment
- Base monthly payment amount
- Verify against calculation

### 4. Down Payment
- Total due at signing
- Breakdown: deposit, first payment, fees, cap reduction

### 5. Residual Value
- Amount at lease end
- Percentage of MSRP (typically 40-70%)

### 6. Mileage Allowance & Overage Charges
- Annual miles (10K, 12K, 15K)
- Cost per excess mile ($0.15-$0.30 typical)

### 7. Early Termination Clause
- Fee amount and structure
- Conditions for termination

### 8. Purchase Option (Buyout Price)
- End-of-lease purchase price
- Usually equals residual value

### 9. Maintenance Responsibilities
- What lessee pays for
- What lessor covers
- Required service schedule

### 10. Warranty and Insurance Coverage
- Factory warranty details
- Required insurance minimums
- Gap insurance status

### 11. Penalties or Late Fee Clauses
- Late fee amount/percentage
- Grace period
- Consequences of missed payments

---

## Output Structure

```json
{
  "sla_parameters": {
    // Each of the 11 parameters with:
    // - extracted value
    // - market comparison
    // - assessment (is it fair?)
  },
  
  "red_flags": [
    {
      "category": "payment|fees|mileage|etc",
      "severity": "critical|high|medium|low",
      "issue": "What's wrong",
      "impact": "How it affects customer",
      "recommendation": "What to negotiate"
    }
  ],
  
  "contract_fairness_score": {
    "overall_score": 0-100,
    "rating": "Excellent|Good|Fair|Poor|Very Poor",
    
    "category_scores": {
      "interest_rate": 0-100,
      "payment_structure": 0-100,
      "mileage_terms": 0-100,
      "fees_and_charges": 0-100,
      "flexibility": 0-100,
      "transparency": 0-100
    },
    
    "strengths": ["Positive aspects"],
    "weaknesses": ["Issues found"],
    "negotiation_priority": ["Top items to negotiate, ordered by savings potential"],
    "summary": "2-3 sentence overall assessment"
  },
  
  "structured_summary": {
    "key_terms_at_glance": {
      "monthly": number,
      "down": number,
      "term": number,
      "apr": number,
      "total_due": number
    },
    "recommended_action": "accept|negotiate|reject"
  }
}
```

---

## Fairness Score Ranges

- **90-100 = Excellent**: Highly competitive, customer-friendly
- **75-89 = Good**: Fair market terms, minor negotiation areas
- **60-74 = Fair**: Average deal, several negotiation opportunities
- **40-59 = Poor**: Below market, significant red flags
- **0-39 = Very Poor**: Unfavorable terms, recommend rejecting

---

## Category Scoring Guide

### Interest Rate (0-100)
- **100**: APR 0-1% above prime rate
- **75**: APR 1-2% above prime (market rate)
- **50**: APR 2-4% above prime
- **25**: APR 4%+ above prime
- **0**: Predatory/exceptionally high

### Payment Structure (0-100)
- **100**: Down <$2K, competitive monthly
- **75**: Down $2-3K, market monthly
- **50**: Down $3-5K, high monthly
- **25**: Down >$5K, excessive monthly
- **0**: Unfair payment structure

### Mileage Terms (0-100)
- **100**: 12K+ miles/year, <$0.20/mile overage
- **75**: 10-12K miles, $0.20-$0.25/mile
- **50**: 7.5-10K miles, $0.25-$0.30/mile
- **25**: <7.5K miles, $0.30-$0.50/mile
- **0**: Severely restrictive

### Fees and Charges (0-100)
- **100**: <$1K total, transparent
- **75**: $1-2K, clearly disclosed
- **50**: $2-3.5K, some hidden fees
- **25**: >$3.5K, many hidden fees
- **0**: Excessive/predatory fees

### Flexibility (0-100)
- **100**: Reasonable termination, fair buyout
- **75**: Standard terms
- **50**: Restrictive
- **25**: Very restrictive
- **0**: No flexibility

### Transparency (0-100)
- **100**: All terms clear
- **75**: Most terms clear
- **50**: Some unclear
- **25**: Many unclear
- **0**: Vague/deceptive

---

## Red Flag Categories

1. **Interest Rate**: APR too high, predatory lending
2. **Payment**: Excessive down payment, high monthly
3. **Fees**: Hidden charges, excessive acquisition/doc fees
4. **Mileage**: Low allowance, high overage charges
5. **Termination**: Harsh early termination penalties
6. **Maintenance**: Unfair cost allocation
7. **Insurance**: Unreasonable requirements, missing gap insurance
8. **Penalties**: Excessive late fees, no grace period
9. **Other**: Vague terms, one-sided clauses

**Severity Levels:**
- **Critical**: Deal-breaker, recommend rejection
- **High**: Major concern, must negotiate
- **Medium**: Should negotiate if possible
- **Low**: Minor issue, nice to improve

---

## Implementation Example

```python
@app.post("/contract/{contract_id}/extract-sla")
async def extract_sla_with_score(contract_id: str):
    """Extract SLA and calculate fairness score"""
    
    # Load contract from JSON
    contract_data = load_contract_from_json(contract_id)
    
    # Call LLM with SLA extraction prompt
    response = llm_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SLA_EXTRACTION_PROMPT},
            {"role": "user", "content": json.dumps(contract_data)}
        ],
        response_format={"type": "json_object"}
    )
    
    sla_result = json.loads(response.choices[0].message.content)
    
    # Return structured output
    return {
        "status": "success",
        "contract_id": contract_id,
        "fairness_score": sla_result["contract_fairness_score"]["overall_score"],
        "rating": sla_result["contract_fairness_score"]["rating"],
        "red_flags_count": len(sla_result["red_flags"]),
        "recommended_action": sla_result["structured_summary"]["recommended_action"],
        "full_analysis": sla_result
    }
```

---

## Quick Testing

**Sample API Response:**

```json
{
  "status": "success",
  "contract_id": "abc-123",
  "fairness_score": 68,
  "rating": "Fair",
  "red_flags_count": 5,
  "recommended_action": "negotiate",
  "top_negotiation_items": [
    "Reduce down payment from $7,500 to $2,500 (Save $5,000)",
    "Increase mileage to 12K miles/year",
    "Lower monthly payment by $50 (Save $1,800)"
  ]
}
```

---

## Full Prompt

See [PROMPTS_DESIGN.md](PROMPTS_DESIGN.md) for:
- Complete system prompt with all instructions
- Detailed scoring methodology
- Full example output with all 11 parameters
- Integration code samples
- Price negotiation chatbot prompt

---

## Key Benefits

✅ **Comprehensive Analysis**: All 11 critical SLA parameters extracted
✅ **Fairness Scoring**: Objective 0-100 score based on market standards
✅ **Red Flag Detection**: Identifies unfair terms and hidden costs
✅ **Actionable Insights**: Prioritized negotiation recommendations
✅ **Structured Output**: Easy to integrate with frontend displays
✅ **Cost Transparency**: Shows total cost and effective monthly rate

---

## Notes

- Always use latest market rates (2026) for comparisons
- Score fairly and objectively based on actual market data
- Identify ALL red flags, even minor ones
- Prioritize negotiation items by potential savings
- Provide clear, customer-focused assessments
- Use `null` for missing data, never guess
