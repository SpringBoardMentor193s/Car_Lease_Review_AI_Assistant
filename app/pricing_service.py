"""
Pricing Service Integration for Car Lease Agreement Review

Integrates with:
- NHTSA API for vehicle safety/spec data
- Edmunds (mock) for fair market value estimation
- TrueCar (mock) for used car pricing

This module provides fair price range estimates and market data.
"""

import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# API endpoints
NHTSA_BASE_URL = "https://vpic.nhtsa.dot.gov/api/"
EDMUNDS_API_KEY = os.getenv("EDMUNDS_API_KEY", "mock_key")
TRUECAR_API_KEY = os.getenv("TRUECAR_API_KEY", "mock_key")

TIMEOUT = 10


def get_nhtsa_vehicle_data(vin: str) -> Dict[str, Any]:
    """
    Fetch vehicle specs from NHTSA API using VIN.
    
    Returns:
        Dictionary with vehicle make, model, year, and safety ratings
    """
    try:
        url = f"{NHTSA_BASE_URL}vehicles/DecodeVin/{vin}?format=json"
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("Results"):
                return {
                    "make": next((r["Value"] for r in data["Results"] if r["Variable"] == "Make"), "Unknown"),
                    "model": next((r["Value"] for r in data["Results"] if r["Variable"] == "Model"), "Unknown"),
                    "year": next((r["Value"] for r in data["Results"] if r["Variable"] == "Model Year"), "Unknown"),
                    "body_class": next((r["Value"] for r in data["Results"] if r["Variable"] == "Body Class"), "Unknown"),
                }
        return {"error": "NHTSA API returned no data"}
    except Exception as e:
        return {"error": f"NHTSA API error: {str(e)}"}


def estimate_edmunds_fair_value(make: str, model: str, year: str, mileage: int = 0) -> Dict[str, Any]:
    """
    Estimate fair market value using Edmunds-like pricing.
    (Mock implementation - replace with real API calls if keys available)
    
    Args:
        make: Vehicle make
        model: Vehicle model
        year: Vehicle year
        mileage: Current mileage (for used vehicles)
    
    Returns:
        Dictionary with fair value estimate and range
    """
    try:
        # Mock estimation based on vehicle attributes
        # In production, call: https://api.edmunds.com/v1/api/Offer/findListPrice
        base_prices = {
            ("Toyota", "Camry", "2024"): 28000,
            ("Toyota", "Camry", "2023"): 25000,
            ("Honda", "Accord", "2024"): 29000,
            ("Honda", "Accord", "2023"): 26000,
            ("Ford", "F-150", "2024"): 35000,
            ("Ford", "F-150", "2023"): 32000,
        }
        
        key = (make, model, year)
        base_price = base_prices.get(key, 25000)  # Default to 25k if not found
        
        # Adjust for mileage (if applicable)
        if mileage > 0:
            depreciation = min(mileage * 0.15 / 1000, base_price * 0.4)  # Max 40% depreciation
            base_price -= depreciation
        
        low_estimate = base_price * 0.92
        high_estimate = base_price * 1.08
        
        return {
            "fair_value": round(base_price, 2),
            "low_estimate": round(low_estimate, 2),
            "high_estimate": round(high_estimate, 2),
            "currency": "USD",
            "source": "Edmunds (Mock)"
        }
    except Exception as e:
        return {"error": f"Edmunds estimation error: {str(e)}"}


def estimate_truecar_pricing(make: str, model: str, year: str, body_type: str = "") -> Dict[str, Any]:
    """
    Estimate used car pricing using TrueCar-like data.
    (Mock implementation - replace with real API calls if keys available)
    
    Args:
        make: Vehicle make
        model: Vehicle model
        year: Vehicle year
        body_type: Vehicle body type (sedan, SUV, truck, etc.)
    
    Returns:
        Dictionary with market pricing data
    """
    try:
        # Mock pricing based on market data
        # In production, call: https://api.truecar.com/v1/listings/
        
        body_adjustment = {
            "SUV": 1.15,
            "Truck": 1.20,
            "Sedan": 1.0,
            "Coupe": 1.05,
            "Hatchback": 0.95,
        }
        
        adjustment = body_adjustment.get(body_type, 1.0)
        
        # Base market price
        market_price = 24000 * adjustment
        
        return {
            "market_high": round(market_price * 1.1, 2),
            "market_average": round(market_price, 2),
            "market_low": round(market_price * 0.9, 2),
            "listings_analyzed": 150,
            "source": "TrueCar (Mock)"
        }
    except Exception as e:
        return {"error": f"TrueCar estimation error: {str(e)}"}


def get_comprehensive_pricing(vin: str) -> Dict[str, Any]:
    """
    Fetch comprehensive pricing data from all sources.
    
    Args:
        vin: Vehicle VIN number
    
    Returns:
        Combined pricing data from NHTSA, Edmunds, and TrueCar
    """
    nhtsa_data = get_nhtsa_vehicle_data(vin)
    
    if "error" in nhtsa_data:
        return nhtsa_data
    
    make = nhtsa_data.get("make", "Unknown")
    model = nhtsa_data.get("model", "Unknown")
    year = nhtsa_data.get("year", "Unknown")
    body_class = nhtsa_data.get("body_class", "")
    
    edmunds_data = estimate_edmunds_fair_value(make, model, year)
    truecar_data = estimate_truecar_pricing(make, model, year, body_class)
    
    return {
        "vehicle": nhtsa_data,
        "edmunds": edmunds_data,
        "truecar": truecar_data,
        "average_fair_value": round(
            (edmunds_data.get("fair_value", 0) + truecar_data.get("market_average", 0)) / 2,
            2
        ) if "error" not in edmunds_data and "error" not in truecar_data else 0
    }
