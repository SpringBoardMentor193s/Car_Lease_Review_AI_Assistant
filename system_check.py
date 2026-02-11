"""
Simple validation script for Milestone 4 features
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("\n" + "="*60)
print("MILESTONE 4 VALIDATION")
print("="*60 + "\n")

try:
    # Test 1: Import pricing service
    print("[1/5] Testing Pricing Service import...")
    from app.pricing_service import get_comprehensive_pricing, estimate_edmunds_fair_value
    print("[OK] Pricing service imported successfully")
    
    # Test 2: Import fairness score
    print("[2/5] Testing Fairness Score import...")
    from app.fairness_score import calculate_fairness_score
    print("[OK] Fairness score module imported successfully")
    
    # Test 3: Test fairness score calculation
    print("[3/5] Testing Fairness Score calculation...")
    sample_sla = {
        "monthly_payment": 350,
        "lease_term": 36,
        "interest_rate": 5.5,
        "mileage_limit": 12000,
        "early_termination": 1500,
        "penalties": 25,
        "total_cost": 12600
    }
    result = calculate_fairness_score(json.dumps(sample_sla))
    assert "fairness_score" in result
    assert "fairness_level" in result
    assert "breakdown" in result
    assert "recommendations" in result
    print(f"[OK] Fairness Score: {result['fairness_score']}/100 ({result['fairness_level']})")
    
    # Test 4: Test pricing API
    print("[4/5] Testing Pricing API...")
    pricing = estimate_edmunds_fair_value("Toyota", "Camry", "2024")
    assert "fair_value" in pricing
    assert "low_estimate" in pricing
    assert "high_estimate" in pricing
    print(f"[OK] Pricing estimates generated: ${pricing['fair_value']}")
    
    # Test 5: Test API endpoint imports
    print("[5/5] Testing API endpoint imports...")
    from app.main import app
    assert hasattr(app, 'routes') or hasattr(app, 'router')
    print("[OK] FastAPI app loaded successfully")
    
    print("\n" + "="*60)
    print("[PASS] MILESTONE 4 VALIDATION SUCCESSFUL")
    print("="*60)
    print("\nMilestone 4 Features Implemented:")
    print("  1. Pricing Service with API integrations")
    print("  2. Contract Fairness Score calculation")
    print("  3. Fair price range estimation")
    print("  4. Comprehensive recommendations")
    print("  5. QA tests for contract formats")
    print("  6. End-to-end test framework")
    print("\n")
    
except Exception as e:
    print(f"\n[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
