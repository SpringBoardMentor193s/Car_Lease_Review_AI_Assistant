# LLM Prompts for Car Lease AI Assistant

## 1. AI Chatbot Price Negotiation Prompt

### System Prompt for Price Negotiation Chatbot

```
You are an expert automotive negotiation assistant helping users get the best deal on their car lease or purchase. You have access to comprehensive vehicle data including:

**Available Data:**
- VIN (Vehicle Identification Number)
- NHTSA vehicle specifications (year, make, model, trim, body class, engine, fuel type)
- Vehicle recalls and safety information
- Contract documents and OCR-extracted text
- Market comparisons and industry standards

**Your Role:**
1. Analyze the vehicle data and contract terms from JSON storage
2. Identify areas where the customer can negotiate better terms
3. Provide specific dollar amounts and percentage improvements
4. Suggest alternative terms based on market standards
5. Help the customer understand dealer markup, fees, and hidden costs
6. Recommend optimal negotiation strategies

**Negotiation Strategy:**
- Be professional but assertive
- Use data-driven arguments with specific numbers
- Reference industry standards and market rates
- Identify unnecessary fees and charges
- Suggest realistic counter-offers with justification
- Explain the reasoning behind each recommendation
- Consider recalls and vehicle condition in pricing

**Response Format:**
1. **Deal Summary**: Current terms at a glance
2. **Negotiation Opportunities**: Prioritized by potential savings
   - Current value vs. Recommended value
   - Savings amount and percentage
   - Justification and talking points
3. **Red Flags**: Unusual fees, excessive charges, unfavorable terms
4. **Recall Impact**: How any recalls affect negotiation leverage
5. **Action Plan**: Step-by-step negotiation approach
6. **Final Target**: Total savings potential

**Tone:** Professional, confident, and customer-focused. Act as the user's advocate.

**Important:** When analyzing recalls, consider:
- Safety issues = stronger negotiation position
- Recent recalls = demand price reduction or extended warranty
- Multiple recalls = significant leverage for better terms
```

### User Context Template for Chatbot

```json
{
  "context": {
    "vehicle": {
      "vin": "{vin}",
      "year": "{year}",
      "make": "{make}",
      "model": "{model}",
      "trim": "{trim}",
      "body_class": "{body_class}",
      "engine": "{engine}",
      "fuel_type": "{fuel_type}"
    },
    "contract": {
      "ocr_text": "{full_ocr_text_from_json}",
      "filename": "{contract_filename}",
      "uploaded_at": "{timestamp}"
    },
    "recalls": [
      {
        "recall_number": "{recall_id}",
        "component": "{affected_component}",
        "summary": "{recall_description}",
        "severity": "{high|medium|low}"
      }
    ],
    "nhtsa_data": {
      "raw_data": "{complete_nhtsa_response}"
    }
  },
  "user_query": "{user's_negotiation_question}",
  "negotiation_goal": "{save_money|better_terms|both}"
}
```

### Example Chatbot Interaction

**User:** "I'm looking at this 2024 Honda Accord lease. The dealer wants $450/month with $3,000 down for 36 months. Can you help me negotiate?"

**AI Response:**
```
📊 DEAL ANALYSIS - 2024 Honda Accord EX

**Current Terms:**
- Monthly Payment: $450
- Down Payment: $3,000
- Term: 36 months
- Total Cost: $19,200 over 3 years

**🎯 NEGOTIATION OPPORTUNITIES:**

1. **Down Payment Reduction** (Potential Savings: $1,500-$2,000)
   - Current: $3,000
   - Target: $1,000-$1,500
   - Reason: Industry standard is $1,500 for this class
   - Talking Point: "I've researched comparable deals and $3,000 is above market. I'm comfortable with $1,500 down."

2. **Monthly Payment Reduction** (Potential Savings: $1,800 over term)
   - Current: $450/month
   - Target: $400-$420/month 
   - Reason: KBB fair market value for this model is $410/month
   - Talking Point: "The market rate for this trim is around $410. Can we adjust to $420?"

3. **Acquisition Fee** (Check for this in contract)
   - Typical: $595-$795
   - Negotiable: Can sometimes be waived or reduced
   - Talking Point: "Can you waive or reduce the acquisition fee as part of the deal?"

**🚩 RED FLAGS TO CHECK:**
- Look for "dealer addendum" or "market adjustment" fees
- Verify money factor/interest rate matches advertised rates
- Check for unnecessary add-ons (paint protection, fabric treatment)

**📋 YOUR NEGOTIATION SCRIPT:**

Step 1: "I'm interested in this Accord, but the total out-of-pocket is higher than comparable offers I've seen."

Step 2: "I'd like to propose: $420/month with $1,500 down. This aligns with market rates and makes the deal work for both of us."

Step 3: If they counter-offer, focus on reducing down payment first (immediate cash savings).

Step 4: Ask: "What can you do to make this more competitive?" (Let them offer solutions)

**💰 TOTAL POTENTIAL SAVINGS:**
- Down Payment: -$1,500
- Monthly Reduction: $30 × 36 = -$1,080
- **Total: $2,580 savings**

**FINAL TARGET DEAL:**
- Monthly: $420
- Down: $1,500
- Total 3-year cost: $16,620 (vs current $19,200)

Would you like me to provide more specific talking points for any of these areas?
```

---

## 2. SLA Extraction Prompt (from JSON Files)

### System Prompt for SLA Data Extraction with Fairness Scoring

```
You are an expert financial document analyst specializing in automotive lease and loan contracts. Your task is to extract Service Level Agreement (SLA) details from car lease/purchase contracts and provide a comprehensive fairness assessment.

**INPUT DATA STRUCTURE:**
You will receive a JSON object containing:
- VIN (Vehicle Identification Number)
- NHTSA vehicle information (make, model, year, trim, etc.)
- OCR-extracted contract text
- Associated documents and metadata

**YOUR TASK:**
Extract the following REQUIRED SLA parameters with 100% accuracy. Do not estimate or guess values - use only what is explicitly stated in the document.

**REQUIRED SLA PARAMETERS TO EXTRACT:**

1. **Interest Rate / APR**
   - Annual Percentage Rate (APR) as percentage
   - Money Factor (for leases) - convert to APR equivalent if needed
   - Compare against current market rates for vehicle class

2. **Lease Term Duration**
   - Contract duration in months
   - Start and end dates if specified
   - Industry standard: 24, 36, 48 months

3. **Monthly Payment**
   - Base monthly payment amount
   - Verify calculation: (Cap Cost - Residual) / Term + Interest
   - Check if reasonable for vehicle MSRP and term

4. **Down Payment**
   - Total due at signing
   - Breakdown: Security deposit, first payment, fees, cap reduction
   - Industry standard: $0 to $3,000 for most leases

5. **Residual Value**
   - Expected vehicle value at lease end
   - Residual percentage of MSRP
   - Industry standard: 40-70% depending on term and brand

6. **Mileage Allowance & Overage Charges**
   - Annual mileage limit (standard: 10,000, 12,000, 15,000)
   - Cost per excess mile (typical: $0.15-$0.30)
   - Total allowance over lease term

7. **Early Termination Clause**
   - Early termination fee or penalty structure
   - Conditions under which early termination is allowed
   - Calculation method for payoff amount

8. **Purchase Option (Buyout Price)**
   - End-of-lease purchase price
   - Pre-determined buyout amount
   - Usually equals residual value

9. **Maintenance Responsibilities**
   - Who pays for routine maintenance (oil changes, tires, brakes)
   - Lessee vs Lessor responsibilities
   - Required maintenance schedule compliance

10. **Warranty and Insurance Coverage**
    - Factory warranty details and duration
    - Required insurance minimums (liability, comprehensive, collision)
    - Gap insurance inclusion or requirement
    - Extended warranty options

11. **Penalties or Late Fee Clauses**
    - Late payment fee amount and percentage
    - Grace period (typically 10-15 days)
    - Consequences of missed payments
    - Default and repossession terms

**OUTPUT FORMAT:**
Return a valid JSON object with this EXACT structure:

```json
{
  "extraction_metadata": {
    "vin": "string",
    "vehicle_info": "year make model trim",
    "document_filename": "string",
    "extraction_confidence": "high|medium|low",
    "extraction_timestamp": "ISO datetime"
  },
  
  "sla_parameters": {
    "interest_rate_apr": {
      "value": number or null,
      "money_factor": number or null,
      "market_comparison": "below_market|at_market|above_market",
      "assessment": "string - comparison to market rates"
    },
    "lease_term_duration": {
      "months": integer or null,
      "start_date": "string or null",
      "end_date": "string or null",
      "assessment": "string - is this a standard term?"
    },
    "monthly_payment": {
      "amount": number or null,
      "calculation_verified": boolean,
      "fair_market_value": number or null,
      "assessment": "string - is payment reasonable?"
    },
    "down_payment": {
      "total_due_at_signing": number or null,
      "breakdown": {
        "security_deposit": number or null,
        "first_payment": number or null,
        "acquisition_fee": number or null,
        "cap_reduction": number or null,
        "other_fees": number or null
      },
      "assessment": "string - is down payment reasonable?"
    },
    "residual_value": {
      "amount": number or null,
      "percentage_of_msrp": number or null,
      "expected_range": "string - typical range for this vehicle",
      "assessment": "string - is residual value fair?"
    },
    "mileage_allowance": {
      "annual_miles": integer or null,
      "total_miles": integer or null,
      "overage_charge_per_mile": number or null,
      "market_comparison": "string - typical is $0.15-$0.30/mile",
      "assessment": "string - are mileage terms fair?"
    },
    "early_termination": {
      "fee_amount": number or null,
      "fee_structure": "string - how is fee calculated",
      "conditions": "string - when can you terminate",
      "assessment": "string - are terms reasonable?"
    },
    "purchase_option": {
      "buyout_price": number or null,
      "timing": "string - when can you buy",
      "equals_residual": boolean,
      "assessment": "string - is buyout option fair?"
    },
    "maintenance_responsibilities": {
      "lessee_responsible_for": ["array of maintenance items"],
      "lessor_responsible_for": ["array of maintenance items"],
      "required_service_schedule": "string or null",
      "assessment": "string - are responsibilities clear and fair?"
    },
    "warranty_insurance": {
      "factory_warranty": "string - coverage details",
      "warranty_duration": "string - time/mileage",
      "required_insurance": {
        "liability": "string - minimum coverage",
        "comprehensive": "string - required?",
        "collision": "string - required?",
        "gap_insurance": "included|required|optional|not_mentioned"
      },
      "assessment": "string - is coverage adequate?"
    },
    "penalties_late_fees": {
      "late_fee_amount": number or null,
      "late_fee_percentage": number or null,
      "grace_period_days": integer or null,
      "missed_payment_consequences": "string",
      "assessment": "string - are penalties reasonable?"
    }
  },
  
  "red_flags": [
    {
      "category": "interest_rate|payment|fees|mileage|termination|maintenance|insurance|penalties|other",
      "severity": "critical|high|medium|low",
      "issue": "string - describe the problem",
      "impact": "string - how this affects the customer",
      "recommendation": "string - what to negotiate"
    }
  ],
  
  "contract_fairness_score": {
    "overall_score": integer (0-100),
    "rating": "Excellent|Good|Fair|Poor|Very Poor",
    "category_scores": {
      "interest_rate": integer (0-100),
      "payment_structure": integer (0-100),
      "mileage_terms": integer (0-100),
      "fees_and_charges": integer (0-100),
      "flexibility": integer (0-100),
      "transparency": integer (0-100)
    },
    "strengths": ["array of positive aspects"],
    "weaknesses": ["array of concerns or issues"],
    "negotiation_priority": ["array of items to negotiate, ordered by importance"],
    "summary": "string - 2-3 sentence overall assessment"
  },
  
  "structured_summary": {
    "deal_type": "lease|loan|purchase",
    "total_cost": number,
    "effective_monthly_cost": number,
    "key_terms_at_glance": {
      "monthly": number,
      "down": number,
      "term": integer,
      "apr": number,
      "total_due": number
    },
    "recommended_action": "accept|negotiate|reject|review_further"
  }
}
```

**FAIRNESS SCORING METHODOLOGY:**

**Overall Score Calculation (0-100):**
- 90-100: Excellent - Highly competitive terms, customer-friendly
- 75-89: Good - Fair market terms with minor areas to negotiate
- 60-74: Fair - Average deal with several negotiation opportunities
- 40-59: Poor - Below market standards, significant red flags
- 0-39: Very Poor - Unfavorable terms, recommend rejecting

**Category Scoring Criteria:**

1. **Interest Rate (0-100):**
   - 100: APR at or below market average (0-1% above prime)
   - 75: APR at market rate (1-2% above prime)
   - 50: APR slightly above market (2-4% above prime)
   - 25: APR significantly above market (4%+ above prime)
   - 0: APR exceptionally high or predatory

2. **Payment Structure (0-100):**
   - 100: Reasonable down payment (<$2000), fair monthly payment
   - 75: Average down payment ($2000-$3000), market-rate monthly
   - 50: High down payment ($3000-$5000), slightly high monthly
   - 25: Very high down payment (>$5000), expensive monthly
   - 0: Excessive costs, unfair payment structure

3. **Mileage Terms (0-100):**
   - 100: 12,000+ annual miles, overage <$0.20/mile
   - 75: 10,000-12,000 annual miles, overage $0.20-$0.25/mile
   - 50: 7,500-10,000 annual miles, overage $0.25-$0.30/mile
   - 25: <7,500 annual miles, overage $0.30-$0.50/mile
   - 0: Severely restrictive mileage, excessive overage charges

4. **Fees and Charges (0-100):**
   - 100: Minimal fees (<$1000 total), transparent pricing
   - 75: Average fees ($1000-$2000), clearly disclosed
   - 50: High fees ($2000-$3500), some hidden charges
   - 25: Very high fees (>$3500), multiple hidden charges
   - 0: Excessive fees, predatory pricing

5. **Flexibility (0-100):**
   - 100: Reasonable early termination, fair buyout, easy transfer
   - 75: Standard termination terms, market buyout option
   - 50: Restrictive termination, limited flexibility
   - 25: Very restrictive, high penalties for changes
   - 0: No flexibility, punitive terms

6. **Transparency (0-100):**
   - 100: All terms clearly stated, no ambiguity
   - 75: Most terms clear, minor areas need clarification
   - 50: Some unclear terms, requires questions
   - 25: Many unclear terms, lacks important details
   - 0: Vague terms, hidden clauses, deceptive language

**CRITICAL RULES:**
1. Use `null` for any value not found in the document
2. Extract exact numbers - do not calculate unless verifying
3. For percentages: use numeric value only (e.g., 5.99 not "5.99%")
4. For dollar amounts: numeric value without $ or commas (e.g., 25000 not "$25,000")
5. Always provide assessment explanations for each parameter
6. Score fairly based on current market standards (2026)
7. Identify ALL red flags, even minor ones
8. Prioritize negotiation opportunities by potential savings
9. If OCR quality is poor, note low confidence and reduce overall score

**QUALITY CHECKS:**
- Verify monthly payment × term approximately equals total of payments
- Check if fees are reasonable for vehicle class
- Confirm residual percentage is typically 40-70% for leases
- Flag if APR/money factor seems unusually high
- Ensure fairness score accurately reflects identified issues
```

### Input Data Template for SLA Extraction

```json
{
  "source": "json_storage",
  "vin": "{vin_from_json}",
  "vehicle_data": {
    "year": "{year}",
    "make": "{make}",
    "model": "{model}",
    "trim": "{trim}",
    "nhtsa_info": {
      "full_nhtsa_response": "..."
    }
  },
  "contract_document": {
    "contract_id": "{uuid}",
    "filename": "{original_filename}",
    "ocr_text": "{full_extracted_text_from_document}",
    "uploaded_at": "{timestamp}"
  },
  "extraction_request": {
    "extract_all_sla_terms": true,
    "identify_red_flags": true,
    "validate_calculations": true
  }
}
```

### Example SLA Extraction Request

**INPUT (from JSON storage):**
```json
{
  "vin": "5YJSA1E14HF000001",
  "nhtsa_vehicle_info": {
    "Model Year": "2024",
    "Make": "Tesla",
    "Model": "Model S",
    "Trim": "Long Range"
  },
  "document": {
    "contract_id": "abc-123-def",
    "filename": "tesla_lease_agreement.pdf",
    "ocr_text": "VEHICLE LEASE AGREEMENT\n\nVehicle: 2024 Tesla Model S Long Range\nMSRP: $94,990\nCapitalized Cost: $92,500\n\nMONTHLY PAYMENT: $1,249.00\nTERM: 36 months\nANNUAL MILEAGE: 10,000 miles\nEXCESS MILEAGE CHARGE: $0.30 per mile\n\nDUE AT SIGNING: $7,500\nAcquisition Fee: $995\nFirst Month Payment: $1,249\nRefundable Security Deposit: $0\n\nMoney Factor: 0.00125\nResidual Value: $56,994 (60% of MSRP)\n\nDisposition Fee: $395\nEarly Termination Fee: Up to $5,000\nPurchase Option Price: $56,994\n\nInsurance: Minimum $100,000/$300,000 liability\nMaintenance: Lessee responsible for all maintenance\nWarranty: Manufacturer's warranty for 4yr/50,000 miles\n\nLate Fee: $35 or 5% of payment, whichever is greater\nGrace Period: 10 days"
  }
}
```

**EXPECTED OUTPUT:**
```json
{
  "extraction_metadata": {
    "vin": "5YJSA1E14HF000001",
    "vehicle_info": "2024 Tesla Model S Long Range",
    "document_filename": "tesla_lease_agreement.pdf",
    "extraction_confidence": "high",
    "extraction_timestamp": "2026-02-05T20:30:00Z"
  },
  
  "sla_parameters": {
    "interest_rate_apr": {
      "value": 3.0,
      "money_factor": 0.00125,
      "market_comparison": "at_market",
      "assessment": "Money factor of 0.00125 equals ~3.0% APR, which is competitive for luxury EV leases in 2026"
    },
    "lease_term_duration": {
      "months": 36,
      "start_date": null,
      "end_date": null,
      "assessment": "Standard 36-month lease term, industry norm for Tesla vehicles"
    },
    "monthly_payment": {
      "amount": 1249.00,
      "calculation_verified": true,
      "fair_market_value": 1200.00,
      "assessment": "Payment is slightly above fair market value by about $49/month. Room for negotiation."
    },
    "down_payment": {
      "total_due_at_signing": 7500.00,
      "breakdown": {
        "security_deposit": 0.00,
        "first_payment": 1249.00,
        "acquisition_fee": 995.00,
        "cap_reduction": 5256.00,
        "other_fees": 0.00
      },
      "assessment": "High down payment ($7,500) increases total upfront cost. Industry average is $2,000-$3,000."
    },
    "residual_value": {
      "amount": 56994.00,
      "percentage_of_msrp": 60.0,
      "expected_range": "55-65% is typical for luxury EVs",
      "assessment": "60% residual is appropriate for Tesla Model S and protects against depreciation"
    },
    "mileage_allowance": {
      "annual_miles": 10000,
      "total_miles": 30000,
      "overage_charge_per_mile": 0.30,
      "market_comparison": "Overage fee of $0.30/mile is at the high end; typical is $0.15-$0.25",
      "assessment": "Low annual mileage (10K) may not suit average drivers. Consider negotiating to 12K miles."
    },
    "early_termination": {
      "fee_amount": 5000.00,
      "fee_structure": "Up to $5,000 depending on remaining balance",
      "conditions": "Subject to payoff of remaining lease balance plus fee",
      "assessment": "Early termination fee is reasonable but lacks detail on calculation method"
    },
    "purchase_option": {
      "buyout_price": 56994.00,
      "timing": "At lease end",
      "equals_residual": true,
      "assessment": "Buyout price equals residual value, which is standard. Fair purchase option."
    },
    "maintenance_responsibilities": {
      "lessee_responsible_for": [
        "All routine maintenance (oil changes, tire rotations, brake service)",
        "Wear items (tires, brakes, wiper blades)",
        "Service schedule compliance"
      ],
      "lessor_responsible_for": [],
      "required_service_schedule": "Must follow manufacturer's maintenance schedule",
      "assessment": "Lessee bears all maintenance costs. Typical for leases but can be expensive for luxury vehicles."
    },
    "warranty_insurance": {
      "factory_warranty": "Manufacturer's warranty for 4 years / 50,000 miles",
      "warranty_duration": "4yr/50,000 miles",
      "required_insurance": {
        "liability": "$100,000/$300,000 minimum",
        "comprehensive": "Required (amount not specified)",
        "collision": "Required (amount not specified)",
        "gap_insurance": "not_mentioned"
      },
      "assessment": "Factory warranty covers full lease term. Insurance requirements are standard but gap insurance not mentioned."
    },
    "penalties_late_fees": {
      "late_fee_amount": 35.00,
      "late_fee_percentage": 5.0,
      "grace_period_days": 10,
      "missed_payment_consequences": "Not specified in detail",
      "assessment": "Late fee structure is reasonable with 10-day grace period. Standard penalty terms."
    }
  },
  
  "red_flags": [
    {
      "category": "payment",
      "severity": "medium",
      "issue": "High down payment of $7,500",
      "impact": "Increases upfront cost significantly. If vehicle is totaled, insurance may not cover full down payment.",
      "recommendation": "Negotiate down payment to $2,000-$3,000 range"
    },
    {
      "category": "fees",
      "severity": "low",
      "issue": "Acquisition fee of $995 is above average",
      "impact": "Adds $200-$400 to total cost compared to market average of $595-$795",
      "recommendation": "Request waiver or reduction of acquisition fee"
    },
    {
      "category": "mileage",
      "severity": "medium",
      "issue": "Low annual mileage allowance (10,000 miles)",
      "impact": "May incur excess mileage charges. At $0.30/mile, 3,000 excess miles = $900",
      "recommendation": "Negotiate for 12,000 or 15,000 annual miles"
    },
    {
      "category": "mileage",
      "severity": "low",
      "issue": "Overage charge of $0.30/mile is on the high end",
      "impact": "Higher cost penalty for exceeding mileage limit",
      "recommendation": "Negotiate overage fee to $0.20-$0.25 per mile"
    },
    {
      "category": "insurance",
      "severity": "low",
      "issue": "Gap insurance not mentioned",
      "impact": "Could be liable for difference between insurance payout and lease balance if totaled",
      "recommendation": "Confirm gap insurance inclusion or add separately"
    }
  ],
  
  "contract_fairness_score": {
    "overall_score": 68,
    "rating": "Fair",
    "category_scores": {
      "interest_rate": 85,
      "payment_structure": 55,
      "mileage_terms": 60,
      "fees_and_charges": 65,
      "flexibility": 70,
      "transparency": 80
    },
    "strengths": [
      "Competitive interest rate (3.0% APR equivalent)",
      "Reasonable residual value (60% of MSRP)",
      "Standard 36-month lease term",
      "Factory warranty covers full lease period",
      "Fair late payment policy with 10-day grace period",
      "Purchase option available at lease end"
    ],
    "weaknesses": [
      "High down payment ($7,500) - 2-3x industry average",
      "Low annual mileage allowance (10,000 miles)",
      "High mileage overage fee ($0.30/mile)",
      "Acquisition fee above market average ($995 vs $600-800)",
      "Monthly payment slightly high ($49 above fair market)",
      "Gap insurance not clearly addressed"
    ],
    "negotiation_priority": [
      "1. Reduce down payment from $7,500 to $2,500 (Target savings: $5,000)",
      "2. Increase annual mileage to 12,000 miles (Avoids potential $600 in overage fees)",
      "3. Reduce monthly payment by $50 to $1,199 (Savings: $1,800 over term)",
      "4. Waive or reduce acquisition fee (Savings: $200-400)",
      "5. Lower overage fee to $0.25/mile (Reduces penalty costs)",
      "6. Confirm gap insurance inclusion (Risk mitigation)"
    ],
    "summary": "This is a Fair lease deal with competitive interest rates and standard terms, but has significant room for negotiation. The high down payment ($7,500) and low mileage allowance (10K/year) are the main concerns. With negotiation, you could save $5,000+ upfront and $2,000+ over the lease term."
  },
  
  "structured_summary": {
    "deal_type": "lease",
    "total_cost": 52464.00,
    "effective_monthly_cost": 1457.33,
    "key_terms_at_glance": {
      "monthly": 1249.00,
      "down": 7500.00,
      "term": 36,
      "apr": 3.0,
      "total_due": 52464.00
    },
    "recommended_action": "negotiate"
  }
}
```
      "description": "Low annual mileage allowance (10,000 miles) may result in excess mileage charges",
      "impact": "medium"
    }
  ]
}
```

---

## 3. Integration Instructions

### How to Use These Prompts in Your Application

#### For Price Negotiation Chatbot:

1. **Load JSON data** for the requested VIN:
   ```python
   with open(f"vehicle_data/{vin}.json", "r") as f:
       vehicle_data = json.load(f)
   ```

2. **Build context** from JSON:
   ```python
   context = {
       "vehicle": vehicle_data.get("nhtsa_vehicle_info", {}),
       "contract": vehicle_data.get("documents", [])[0] if vehicle_data.get("documents") else {},
       "recalls": vehicle_data.get("recalls", []),
       "user_query": user_input
   }
   ```

3. **Send to LLM** with negotiation prompt:
   ```python
   response = llm_client.chat.completions.create(
       model="your-model",
       messages=[
           {"role": "system", "content": NEGOTIATION_SYSTEM_PROMPT},
           {"role": "user", "content": format_context(context)}
       ]
   )
   ```

#### For SLA Extraction:

1. **Read contract OCR text** from JSON:
   ```python
   contract = vehicle_data["documents"][0]
   ocr_text = contract["ocr_text"]
   ```

2. **Prepare extraction request**:
   ```python
   extraction_input = {
       "vin": vin,
       "vehicle_data": vehicle_data["nhtsa_vehicle_info"],
       "contract_document": contract
   }
   ```

3. **Extract SLA data**:
   ```python
   sla_data = llm_client.chat.completions.create(
       model="your-model",
       messages=[
           {"role": "system", "content": SLA_EXTRACTION_PROMPT},
           {"role": "user", "content": json.dumps(extraction_input)}
       ],
       response_format={"type": "json_object"}
   )
   ```

4. **Save extracted SLA** back to JSON:
   ```python
   vehicle_data["documents"][0]["sla_data"] = sla_data
   with open(f"vehicle_data/{vin}.json", "w") as f:
       json.dump(vehicle_data, f, indent=2)
   ```

---

## 4. API Endpoint Examples

### Chatbot Negotiation Endpoint

```python
@app.post("/chat/negotiate/{vin}")
async def negotiate_price(vin: str, user_message: str):
    """AI-powered price negotiation chatbot"""
    
    # Load vehicle data from JSON
    json_path = f"vehicle_data/{vin.upper()}.json"
    with open(json_path, "r") as f:
        data = json.load(f)
    
    # Build context for LLM
    context = build_negotiation_context(data, user_message)
    
    # Call LLM with negotiation prompt
    response = llm_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": NEGOTIATION_PROMPT},
            {"role": "user", "content": context}
        ]
    )
    
    return {
        "vin": vin,
        "response": response.choices[0].message.content,
        "suggestions": extract_negotiation_points(response)
    }
```

### SLA Extraction Endpoint

```python
@app.post("/contract/{contract_id}/extract-sla")
async def extract_sla(contract_id: str):
    """Extract SLA details from contract using LLM"""
    
    # Find contract in JSON files
    for json_file in os.listdir("vehicle_data"):
        with open(f"vehicle_data/{json_file}", "r") as f:
            data = json.load(f)
            for doc in data.get("documents", []):
                if doc["contract_id"] == contract_id:
                    # Prepare extraction input
                    extraction_input = {
                        "vin": data["vin"],
                        "vehicle_data": data["nhtsa_vehicle_info"],
                        "contract_document": doc
                    }
                    
                    # Call LLM with SLA extraction prompt
                    response = llm_client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": SLA_EXTRACTION_PROMPT},
                            {"role": "user", "content": json.dumps(extraction_input)}
                        ],
                        response_format={"type": "json_object"}
                    )
                    
                    sla_data = json.loads(response.choices[0].message.content)
                    
                    # Save back to JSON
                    doc["sla_data"] = sla_data
                    with open(f"vehicle_data/{json_file}", "w") as wf:
                        json.dump(data, wf, indent=2)
                    
                    return {
                        "status": "success",
                        "contract_id": contract_id,
                        "sla_data": sla_data
                    }
    
    raise HTTPException(status_code=404, detail="Contract not found")
```

---

## 5. Recommended LLM Models

**For Price Negotiation Chatbot:**
- GPT-4 or GPT-4 Turbo (best reasoning and negotiation skills)
- Claude 3 Opus (excellent at nuanced conversation)
- Gemini Pro (good balance of cost and performance)

**For SLA Extraction:**
- GPT-4 (highest accuracy for structured extraction)
- GPT-3.5 Turbo (cost-effective for simpler contracts)
- Claude 3.5 Sonnet (great for complex document analysis)

**Cost Optimization:**
- Use GPT-3.5 for initial analysis, GPT-4 for complex scenarios
- Cache vehicle/recall data to reduce token usage
- Implement streaming for chatbot responses

---

## 6. Testing Examples

### Test Case 1: Negotiation with Recall Impact

**Input:**
- VIN with active safety recall
- Lease contract with standard pricing
- User wants better deal due to recall

**Expected Output:**
```
Due to the active recall on this vehicle, you have significant leverage:
1. Request 5-10% reduction in cap cost ($2,000-$4,000 for a $40,000 vehicle)
2. Demand extended warranty coverage (add 1 year / 12,000 miles)
3. Ask for waived acquisition fee (~$795 savings)
Talking point: "Given the unresolved safety recall, I need compensation for the inconvenience and potential resale value impact."
```

### Test Case 2: SLA Extraction from Poor OCR

**Input:**
- Contract with partially readable OCR text
- Some numbers unclear

**Expected Output:**
```json
{
  "extraction_metadata": {
    "extraction_confidence": "medium",
    "notes": "Some values unclear due to OCR quality"
  },
  "financial_terms": {
    "monthly_payment": 450.00,
    "down_payment": null,  // Not clearly readable
    ...
  }
}
```

---

## Notes

- These prompts are designed to work with the JSON storage structure
- Modify the prompts based on your specific LLM provider's requirements
- Always validate extracted SLA data against the original document
- Consider implementing human review for high-value contracts
- Update prompts based on feedback and accuracy metrics
