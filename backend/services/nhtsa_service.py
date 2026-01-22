import requests


# 🔹 Existing — VIN decode (keep as is)
def get_vehicle_details_from_vin(vin: str):
    if not vin:
        return None

    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
    response = requests.get(url)

    if response.status_code != 200:
        return None

    data = response.json().get("Results", [])

    vehicle_info = {}
    for item in data:
        if item["Variable"] in ["Make", "Model", "Model Year"]:
            vehicle_info[item["Variable"]] = item["Value"]

    return vehicle_info
def normalize_model_for_recalls(model: str):
    """
    Normalize model names for NHTSA recall compatibility
    """

    if not model:
        return model

    model = model.upper()

    # Common Dodge Ram cases
    if "RAM" in model and "3500" in model:
        return "RAM 3500"

    if "RAM" in model:
        return "RAM"

    # Remove technical words
    blacklist = ["CHASSIS", "CAB", "CREW", "EXTENDED"]
    for word in blacklist:
        model = model.replace(word, "")

    return model.strip()



# 🔹 NEW — RECALL DATA (THIS MATCHES WEBSITE 🔥)
import requests


def get_vehicle_recalls(vin: str, vehicle_data: dict | None = None):
    """
    Fetch recall data using:
    1️⃣ VIN-based recall API
    2️⃣ Fallback → Make + Model + Year recall API
    """

    # ---------- TRY VIN BASED FIRST ----------

    if vin:
        url = f"https://api.nhtsa.gov/recalls/recallsByVehicle?vin={vin}"

        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                if results:
                    return _process_recall_results(results)

        except:
            pass

    # ---------- FALLBACK: MAKE + MODEL + YEAR ----------

    if vehicle_data:
        make = vehicle_data.get("Make")
        raw_model = vehicle_data.get("Model")
        model = normalize_model_for_recalls(raw_model)
        year = vehicle_data.get("Model Year")

        if make and model and year:
            url = f"https://api.nhtsa.gov/recalls/recallsByVehicle?make={make}&model={model}&modelYear={year}"

            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])

                    if results:
                        return _process_recall_results(results)

            except:
                pass

    # ---------- NO RECALL DATA FOUND ----------

    return {
        "total_recalls": 0,
        "open_recalls": 0,
        "recall_details": []
    }


def _process_recall_results(results):
    open_recalls = [r for r in results if r.get("RecallStatus") == "Recall Incomplete"]

    recall_details = []
    for r in open_recalls:
        recall_details.append({
            "recall_number": r.get("NHTSACampaignNumber"),
            "summary": r.get("Summary"),
            "risk": r.get("SafetyRisk"),
            "remedy": r.get("Remedy"),
            "status": r.get("RecallStatus")
        })

    return {
        "total_recalls": len(results),
        "open_recalls": len(open_recalls),
        "recall_details": recall_details
    }
# 🔹 NEW — SAFETY RATING (STAR RATING)
def get_vehicle_safety_rating(make: str, model: str, year: str):
    if not make or not model or not year:
        return None

    url = f"https://api.nhtsa.gov/SafetyRatings/modelyear/{year}/make/{make}/model/{model}?format=json"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return None

        data = response.json().get("Results", [])

        if not data:
            return None

        vehicle_id = data[0].get("VehicleId")

        # Fetch rating by VehicleId
        rating_url = f"https://api.nhtsa.gov/SafetyRatings/VehicleId/{vehicle_id}?format=json"
        rating_resp = requests.get(rating_url, timeout=5)

        if rating_resp.status_code != 200:
            return None

        rating_data = rating_resp.json().get("Results", [])

        if not rating_data:
            return None

        return {
            "overall_rating": rating_data[0].get("OverallRating"),
            "front_crash": rating_data[0].get("OverallFrontCrashRating"),
            "side_crash": rating_data[0].get("OverallSideCrashRating"),
            "rollover": rating_data[0].get("RolloverRating")
        }

    except Exception:
        return None

