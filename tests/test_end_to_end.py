"""
End-to-End Tests for Car Lease Agreement Reviewer

Tests the complete workflow:
1. Upload contract
2. Extract SLA
3. Generate negotiation advice
4. Calculate pricing
5. Compute fairness score
6. Generate full report
"""

import json
import sys
import os
from io import BytesIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine


class TestEndToEnd:
    """End-to-end test suite"""
    
    def __init__(self):
        self.client = TestClient(app)
        # Create tables
        Base.metadata.create_all(bind=engine)
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = self.client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "API running"
        print("[OK] API root endpoint working")
    
    def test_contract_upload_text(self):
        """Test uploading a contract (text file simulation)"""
        contract_text = """
        CAR LEASE AGREEMENT
        
        LESSOR: AutoCorp Finance Inc.
        LESSEE: John Doe
        
        LEASE TERM: 36 months
        EFFECTIVE DATE: 2024-01-01
        
        MONTHLY PAYMENT: $350
        TOTAL COST: $12,600
        
        MILEAGE ALLOWANCE: 12,000 miles per year
        EXCESS MILEAGE: $0.25 per mile
        
        INTEREST RATE: 5.5%
        
        EARLY TERMINATION FEE: $1,500
        LATE PAYMENT PENALTY: $25
        
        This agreement is binding and enforceable.
        """
        
        # Simulate file upload
        files = {
            "file": ("test_contract.txt", BytesIO(contract_text.encode()), "text/plain")
        }
        
        response = self.client.post("/upload-contract/", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "contract_id" in data
        assert "preview_text" in data
        assert len(data["preview_text"]) > 0
        
        self.contract_id = data["contract_id"]
        print(f"[OK] Contract uploaded successfully (ID: {self.contract_id})")
        return self.contract_id
    
    def test_sla_extraction(self):
        """Test SLA extraction from uploaded contract"""
        if not hasattr(self, "contract_id"):
            self.test_contract_upload_text()
        
        response = self.client.post(f"/extract-sla/{self.contract_id}")
        assert response.status_code == 200
        data = response.json()
        assert "sla" in data
        assert "contract_id" in data
        
        # Store SLA for later tests
        self.sla = data["sla"]
        print(f"[OK] SLA extracted: {len(self.sla)} fields")
        return data
    
    def test_vin_lookup(self):
        """Test VIN lookup endpoint"""
        vin = "JTHBP5C23A5028174"  # Example Toyota Avalon
        
        response = self.client.get(f"/vin/{vin}")
        assert response.status_code == 200
        data = response.json()
        assert "vin" in data or "error" not in data
        
        self.vin = vin
        print(f"[OK] VIN lookup working for {vin}")
        return data
    
    def test_pricing_api(self):
        """Test pricing API integration"""
        if not hasattr(self, "vin"):
            self.test_vin_lookup()
        
        response = self.client.get(f"/pricing/{self.vin}")
        assert response.status_code == 200
        data = response.json()
        
        # Should contain vehicle and pricing info
        assert "vehicle" in data or "edmunds" in data or "truecar" in data
        
        print("[OK] Pricing API returned data")
        return data
    
    def test_fairness_score_calculation(self):
        """Test fairness score calculation"""
        if not hasattr(self, "contract_id"):
            self.test_contract_upload_text()
        if not hasattr(self, "vin"):
            self.test_vin_lookup()
        
        response = self.client.post(
            f"/fairness-score/{self.contract_id}",
            params={"vin": self.vin}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "fairness_score" in data
        assert "fairness_level" in data
        assert "breakdown" in data
        assert "recommendations" in data
        
        score = data["fairness_score"]
        assert 0 <= score <= 100
        
        print(f"[OK] Fairness score calculated: {score}/100 ({data['fairness_level']})")
        return data
    
    def test_full_report(self):
        """Test comprehensive full report generation"""
        if not hasattr(self, "contract_id"):
            self.test_contract_upload_text()
        if not hasattr(self, "vin"):
            self.test_vin_lookup()
        
        response = self.client.get(
            f"/full-report/{self.contract_id}",
            params={"vin": self.vin}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify all components are present
        assert "contract_id" in data
        assert "filename" in data
        assert "sla_extraction" in data
        assert "negotiation_advice" in data
        assert "pricing_data" in data
        assert "fairness_score" in data
        assert "fairness_level" in data
        assert "fairness_breakdown" in data
        assert "recommendations" in data
        
        print(f"[OK] Full report generated with all components")  
        print(f"  - SLA: {len(data['sla_extraction'])} fields")
        print(f"  - Fairness Score: {data['fairness_score']}/100")
        print(f"  - Recommendations: {len(data['recommendations'])} items")
        
        return data
    
    def test_contract_summary(self):
        """Test contract summary endpoint"""
        if not hasattr(self, "contract_id"):
            self.test_contract_upload_text()
        if not hasattr(self, "vin"):
            self.test_vin_lookup()
        
        response = self.client.get(
            f"/contract-summary/{self.contract_id}",
            params={"vin": self.vin}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "sla" in data
        assert "vehicle" in data
        
        print(f"[OK] Contract summary generated")  
        return data
    
    def test_negotiation_advice(self):
        """Test negotiation advice generation"""
        if not hasattr(self, "contract_id"):
            self.test_contract_upload_text()
        
        response = self.client.get(f"/negotiation/{self.contract_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert "negotiation_advice" in data
        advice_text = data["negotiation_advice"]
        assert len(advice_text) > 0
        
        print(f"[OK] Negotiation advice generated ({len(advice_text)} chars)")
        return data
    
    def test_invalid_contract_id(self):
        """Test error handling for invalid contract ID"""
        response = self.client.get("/negotiation/999999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or data
        
        print(f"[OK] Invalid contract ID properly rejected")  
    
    def test_pricing_with_different_vins(self):
        """Test pricing API with multiple VINs"""
        test_vins = [
            "JTHBP5C23A5028174",  # Toyota
            "1HGBH41JXMN109186",  # Honda
            "1FTFW1ET5CFB10662",  # Ford
        ]
        
        for vin in test_vins:
            response = self.client.get(f"/pricing/{vin}")
            assert response.status_code == 200
            data = response.json()
            
            # Should have vehicle data or error message
            assert "vehicle" in data or "error" in data or "average_fair_value" in data
        
        print(f"[OK] Pricing API tested with {len(test_vins)} different VINs")
    
    def run_all(self):
        """Run all end-to-end tests"""
        print("\n" + "="*60)
        print("RUNNING END-TO-END TESTS")
        print("="*60 + "\n")
        
        try:
            # Basic connectivity
            self.test_api_root()
            print()
            
            # Upload and extraction pipeline
            self.test_contract_upload_text()
            self.test_sla_extraction()
            print()
            
            # Pricing and VIN lookup
            self.test_vin_lookup()
            self.test_pricing_api()
            self.test_pricing_with_different_vins()
            print()
            
            # Fairness and scoring
            self.test_fairness_score_calculation()
            print()
            
            # Complete workflows
            self.test_contract_summary()
            self.test_negotiation_advice()
            self.test_full_report()
            print()
            
            # Error handling
            self.test_invalid_contract_id()
            
            print("\n" + "="*60)
            print("[PASS] ALL END-TO-END TESTS PASSED")
            print("="*60 + "\n")
            return True
            
        except AssertionError as e:
            print(f"\n[FAIL] TEST FAILED: {e}\n")
            return False
        except Exception as e:
            print(f"\n[ERROR] UNEXPECTED ERROR: {e}\n")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    tester = TestEndToEnd()
    success = tester.run_all()
    sys.exit(0 if success else 1)
