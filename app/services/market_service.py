from typing import Dict, Any, Tuple

def get_market_price(make: str, model: str, year: int) -> Tuple[float, float]:
    """
    Returns min/max market price. Mocked for demo.
    """
    # Simple Mock DB
    if make.lower() == "toyota" and model.lower() == "camry":
        return (24000.0, 27000.0)
    
    return (20000.0, 30000.0) # Generic fallback

def get_vin_info(vin: str) -> Dict[str, Any]:
    """
    Fetches VIN info from NHTSA or Mock.
    """
    # Mock Response
    return {
        "Make": "Toyota",
        "Model": "Camry",
        "Year": 2024,
        "RecallCount": 0,
        "SafetyRating": "5 Stars"
    }
