import requests
from typing import Dict, Any, Optional
from models.schemas import VehicleDetails

class VINService:
    @staticmethod
    def validate_vin(vin: str) -> bool:
        """Validate VIN format."""
        if len(vin) != 17:
            return False
        
        invalid_chars = set('IOQ')
        return not any(char in invalid_chars for char in vin.upper())
    
    @staticmethod
    def get_vehicle_details(vin: str) -> VehicleDetails:
        """Get vehicle details from NHTSA API."""
        try:
            vin_url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json"
            response = requests.get(vin_url, timeout=10)
            response.raise_for_status()
            
            specs_data = response.json()["Results"][0]
            
            cleaned_specs = {
                k: v for k, v in specs_data.items() 
                if v and v not in ["0", "Not Applicable", ""] and not k.startswith("_")
            }
            
            recalls = VINService.get_recalls(
                cleaned_specs.get("Make"),
                cleaned_specs.get("Model"),
                cleaned_specs.get("ModelYear")
            )
            
            return VehicleDetails(
                vin=vin,
                specifications=cleaned_specs,
                recalls=recalls.get("results", []),
                recall_count=recalls.get("Count", 0)
            )
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch vehicle details: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing vehicle data: {str(e)}")
    
    @staticmethod
    def get_recalls(make: str, model: str, year: str) -> Dict[str, Any]:
        """Get recall information for vehicle."""
        try:
            recall_url = "https://api.nhtsa.gov/recalls/recallsByVehicle"
            params = {
                "make": make,
                "model": model,
                "modelYear": year,
                "format": "json"
            }
            
            params = {k: v for k, v in params.items() if v is not None}
            
            response = requests.get(recall_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except:
            return {"results": [], "Count": 0}