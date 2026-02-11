"""
QA Tests for Contract Format Handling

Tests the system's ability to extract SLA and calculate fairness scores
from various contract formats and structures.
"""

import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.fairness_score import calculate_fairness_score, parse_sla, safe_float


class TestContractFormats:
    """Test suite for different contract formats"""
    
    # Sample contract SLAs in different formats
    
    STANDARD_FORMAT = {
        "interest_rate": 5.5,
        "lease_term": "36 months",
        "monthly_payment": 350,
        "mileage_limit": 12000,
        "penalties": 25,
        "early_termination": 1500,
        "total_cost": 12600
    }
    
    JSON_STRING_FORMAT = """{
        "interest_rate": "6.2%",
        "lease_term": "48",
        "monthly_payment": "$425",
        "mileage_limit": "15000 miles/year",
        "penalties": "$30",
        "early_termination": "1200",
        "total_cost": "$20400"
    }"""
    
    MINIMAL_FORMAT = {
        "monthly_payment": 300,
        "lease_term": 36
    }
    
    HIGH_RISK_FORMAT = {
        "interest_rate": 14.5,
        "lease_term": "24",
        "monthly_payment": 600,
        "mileage_limit": 8000,
        "penalties": 150,
        "early_termination": 4500,
        "total_cost": 14400
    }
    
    CURRENCY_MIXED_FORMAT = {
        "interest_rate": "7.5%",
        "lease_term": "36 months",
        "monthly_payment": "$399.99",
        "mileage_limit": "12,000 miles per year",
        "penalties": "$35",
        "early_termination": "1500",
        "total_cost": "$14,396"
    }
    
    def test_standard_format(self):
        """Test extraction from standard numerical format"""
        result = calculate_fairness_score(json.dumps(self.STANDARD_FORMAT))
        assert result["fairness_score"] >= 0 and result["fairness_score"] <= 100
        assert result["fairness_level"] in ["EXCELLENT", "GOOD", "FAIR", "POOR", "VERY POOR"]
        assert "breakdown" in result
        print(f"[PASS] Standard format: Score = {result['fairness_score']}, Level = {result['fairness_level']}")
        return result
    
    def test_json_string_format(self):
        """Test extraction from JSON string with currency symbols"""
        result = calculate_fairness_score(self.JSON_STRING_FORMAT)
        assert result["fairness_score"] >= 0 and result["fairness_score"] <= 100
        assert "breakdown" in result
        print(f"[PASS] JSON string format: Score = {result['fairness_score']}, Level = {result['fairness_level']}")
        return result
    
    def test_minimal_format(self):
        """Test extraction from minimal contract data"""
        result = calculate_fairness_score(json.dumps(self.MINIMAL_FORMAT))
        assert result["fairness_score"] >= 0 and result["fairness_score"] <= 100
        print(f"[PASS] Minimal format: Score = {result['fairness_score']}, Level = {result['fairness_level']}")
        return result
    
    def test_high_risk_format(self):
        """Test detection of high-risk contracts"""
        result = calculate_fairness_score(json.dumps(self.HIGH_RISK_FORMAT))
        assert result["fairness_score"] < 50  # Should be below fair
        assert "POOR" in result["fairness_level"] or "VERY POOR" in result["fairness_level"]
        assert len(result["recommendations"]) > 0
        print(f"[PASS] High-risk format detected: Score = {result['fairness_score']}, Level = {result['fairness_level']}")
        return result
    
    def test_safe_float_conversion(self):
        """Test safe float conversion from various string formats"""
        test_cases = [
            ("$500", 500),
            ("500", 500),
            ("5.5%", 5.5),
            ("$12,000", 12000),
            ("invalid", 0),
            (None, 0),
            (350, 350),
            ("", 0),
        ]
        
        for value, expected in test_cases:
            result = safe_float(value)
            assert result == expected, f"Failed for {value}: got {result}, expected {expected}"
            print(f"[PASS] safe_float('{value}') = {result}")
    
    def test_parse_sla_formats(self):
        """Test SLA parsing from different formats"""
        
        # Dict format
        result1 = parse_sla(self.STANDARD_FORMAT)
        assert isinstance(result1, dict)
        assert "monthly_payment" in result1
        print(f"[PASS] Parsed dict format: {len(result1)} fields")
        
        # JSON string format
        result2 = parse_sla(self.JSON_STRING_FORMAT)
        assert isinstance(result2, dict)
        assert "monthly_payment" in result2
        print(f"[PASS] Parsed JSON string format: {len(result2)} fields")
        
        # Invalid formats
        result3 = parse_sla("invalid json")
        assert isinstance(result3, dict) and len(result3) == 0
        print("[OK] Invalid JSON returns empty dict")
        
        result4 = parse_sla(None)
        assert isinstance(result4, dict) and len(result4) == 0
        print("[OK] None input returns empty dict")
    
    def test_breakdown_completeness(self):
        """Test that fairness score breakdown includes all components"""
        result = calculate_fairness_score(json.dumps(self.STANDARD_FORMAT))
        
        expected_components = [
            "monthly_payment",
            "interest_rate",
            "mileage_allowance",
            "early_termination",
            "penalty_structure",
            "market_comparison"
        ]
        
        for component in expected_components:
            assert component in result["breakdown"], f"Missing component: {component}"
            assert "score" in result["breakdown"][component]
            assert "max" in result["breakdown"][component]
            assert "reason" in result["breakdown"][component]
            print(f"[PASS] Breakdown includes {component}")
    
    def test_recommendations_generated(self):
        """Test that recommendations are generated for high-risk contracts"""
        result = calculate_fairness_score(json.dumps(self.HIGH_RISK_FORMAT))
        
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0
        
        # At least one warning recommendation should be present
        warnings = [r for r in result["recommendations"] if "⚠️" in r or "🔴" in r or "🟡" in r]
        assert len(warnings) > 0, "Expected warning recommendations for high-risk contract"
        
        print(f"[PASS] Generated {len(result['recommendations'])} recommendations")
        for rec in result["recommendations"]:
            print(f"  - {rec}")
    
    def run_all(self):
        """Run all QA tests"""
        print("\n" + "="*60)
        print("RUNNING QA TESTS FOR CONTRACT FORMATS")
        print("="*60 + "\n")
        
        try:
            self.test_safe_float_conversion()
            print()
            self.test_parse_sla_formats()
            print()
            self.test_standard_format()
            self.test_json_string_format()
            self.test_minimal_format()
            self.test_high_risk_format()
            print()
            self.test_breakdown_completeness()
            print()
            self.test_recommendations_generated()
            
            print("\n" + "="*60)
            print("[PASS] ALL QA TESTS PASSED")
            print("="*60 + "\n")
            return True
            
        except AssertionError as e:
            print(f"\n[FAIL] TEST FAILED: {e}\n")
            return False
        except Exception as e:
            print(f"\n[ERROR] UNEXPECTED ERROR: {e}\n")
            return False


if __name__ == "__main__":
    tester = TestContractFormats()
    success = tester.run_all()
    sys.exit(0 if success else 1)
