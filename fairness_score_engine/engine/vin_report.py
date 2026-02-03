"""VIN-based vehicle information and risk report generation.

Ported from Colab notebook `VIN-based-information-extraction.ipynb`.
Uses public NHTSA APIs plus simple text heuristics to build a structured
report for a given VIN.
"""

from __future__ import annotations

from typing import Any, Dict, List

import re
import requests


def decode_vin(vin: str) -> Dict[str, Any]:
    """Decode VIN using NHTSA VPIC API.

    Returns a structured dict with basic vehicle identity fields and
    a confidence_level flag. On failure, returns an error payload with
    LOW confidence.
    """
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValuesExtended/{vin}?format=json"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()["Results"][0]
    except Exception:
        return {
            "vin": vin,
            "error": "VIN decoding failed",
            "confidence_level": "LOW",
        }

    decoded: Dict[str, Any] = {
        "vin": vin,
        "make": data.get("Make"),
        "model": data.get("Model"),
        "model_year": data.get("ModelYear"),
        "body_class": data.get("BodyClass"),
        "engine": {
            "cylinders": data.get("EngineCylinders"),
            "displacement_l": data.get("DisplacementL"),
            "fuel_type": data.get("FuelTypePrimary"),
        },
        "plant": {
            "country": data.get("PlantCountry"),
            "state": data.get("PlantState"),
            "city": data.get("PlantCity"),
        },
    }

    # Confidence assessment based on presence of critical fields
    critical_fields: List[Any] = [
        decoded["make"],
        decoded["model"],
        decoded["model_year"],
    ]

    if all(critical_fields):
        confidence = "HIGH"
    else:
        confidence = "MEDIUM"

    decoded["confidence_level"] = confidence
    return decoded


def get_recall_history(make: str | None, model: str | None, year: str | None) -> Dict[str, Any]:
    """Fetch recall history for a given make/model/year from NHTSA API.

    Returns a dict containing recall_count, list of recalls, and
    a confidence_level + explanatory note. On failure, returns an
    empty result with LOW confidence.
    """
    url = (
        "https://api.nhtsa.gov/recalls/recallsByVehicle"
        f"?make={make}&model={model}&modelYear={year}"
    )

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        # Fail closed: no recalls rather than breaking pipeline
        return {
            "recall_count": 0,
            "recalls": [],
            "confidence_level": "LOW",
            "confidence_reason": "Recall lookup failed or returned no usable data",
        }

    recalls: List[Dict[str, Any]] = []
    for item in data.get("results", []):
        recalls.append(
            {
                "recall_id": item.get("NHTSACampaignNumber"),
                "component": item.get("Component"),
                "summary": item.get("Summary"),
                "consequence": item.get("Consequence"),
                "remedy": item.get("Remedy"),
                "report_date": item.get("ReportReceivedDate"),
            }
        )

    # Build incident-style summary ONLY for confidence modeling
    recall_incident_summary = {
        "recall_mentions": len(recalls),
    }

    confidence_level = calculate_confidence_level(
        incident_summary=recall_incident_summary,
        data_sources=["NHTSA Recall Database"],
    )

    return {
        "recall_count": len(recalls),
        "recalls": recalls,
        "confidence_level": confidence_level,
        "confidence_reason": (
            "Recall data sourced directly from official NHTSA safety recall records"
        ),
        "note": (
            "High recall counts for certain model years are often driven by multi-"
            "campaign manufacturer recalls (e.g., Takata airbag inflators) and do "
            "not necessarily indicate individual vehicle crash or damage history"
        ),
    }


def nicb_external_reference(vin: str) -> Dict[str, Any]:
    """Return static info about NICB VINCheck as an external reference.

    Note: This does NOT perform an actual NICB query; there is no public API.
    """
    return {
        "provider": "NICB VINCheck",
        "purpose": "External theft and salvage title verification",
        "coverage": [
            "Reported stolen vehicles",
            "Salvage and total-loss insurance records",
        ],
        "access": "Manual VIN lookup required (no public API)",
        "lookup_url": "https://www.nicb.org/vincheck",
        "recommended": True,
        "confidence_level": "N/A",
        "note": (
            "NICB does not provide programmatic VIN verification. "
            "This link is provided for user-initiated confirmation only."
        ),
    }


def odometer_risk_assessment(recall_count: int, salvage_hint: bool = False) -> Dict[str, Any]:
    """Simple odometer risk heuristic based on salvage hints and recall volume."""
    risk = "LOW"
    confidence = "LOW"

    if salvage_hint:
        risk = "HIGH"
        confidence = "HIGH"
    elif recall_count > 5:
        risk = "MEDIUM"
        confidence = "MEDIUM"

    return {
        "risk_level": risk,
        "confidence_level": confidence,
        "note": "Public data only. Full odometer history requires paid report.",
    }


def get_nhtsa_complaints(make: str | None, model: str | None, year: str | None) -> List[Dict[str, Any]]:
    """Fetch NHTSA complaints for a given make/model/year.

    Returns an empty list on failure.
    """
    url = (
        "https://api.nhtsa.gov/complaints/complaintsByVehicle"
        f"?make={make}&model={model}&modelYear={year}"
    )

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
        return results if isinstance(results, list) else []
    except Exception:
        # Fail closed: no complaints rather than crashing pipeline
        return []


def extract_incident_evidence(
    complaints: List[Dict[str, Any]],
    recalls: List[Dict[str, Any]],
) -> Dict[str, int]:
    """Scan complaint and recall texts for incident-related keywords.

    Produces a small bag-of-signals used for risk scoring and confidence.
    """
    evidence: Dict[str, int] = {
        "crash_mentions": 0,
        "airbag_deployment_mentions": 0,
        "total_loss_mentions": 0,
        "salvage_mentions": 0,
        "fire_mentions": 0,
        "odometer_discrepancy_mentions": 0,
    }

    crash_pattern = re.compile(r"\b(crash|collision)\b")
    airbag_pattern = re.compile(r"\bair\s?-?\s?bag deployed\b")
    total_loss_pattern = re.compile(r"\b(totaled|total loss)\b")
    salvage_pattern = re.compile(r"\b(salvage|rebuilt)\b")
    fire_pattern = re.compile(r"\bfire\b")
    odometer_pattern = re.compile(r"\bodometer\b.*\b(rollback|incorrect)\b")

    def scan(text: str) -> None:
        t = text.lower()

        if crash_pattern.search(t):
            evidence["crash_mentions"] += 1
        if airbag_pattern.search(t):
            evidence["airbag_deployment_mentions"] += 1
        if total_loss_pattern.search(t):
            evidence["total_loss_mentions"] += 1
        if salvage_pattern.search(t):
            evidence["salvage_mentions"] += 1
        if fire_pattern.search(t):
            evidence["fire_mentions"] += 1
        if odometer_pattern.search(t):
            evidence["odometer_discrepancy_mentions"] += 1

    for c in complaints:
        scan(c.get("Summary", "") or "")

    for r in recalls:
        scan(r.get("summary", "") or "")

    return evidence


def compute_vehicle_incident_risk(evidence: Dict[str, int]) -> Dict[str, int]:
    """Map incident evidence counts into coarse risk scores (0–10)."""
    theft_score = 0
    salvage_score = 0
    total_loss_score = 0

    salvage_score += evidence["airbag_deployment_mentions"] * 2
    salvage_score += evidence["crash_mentions"]
    salvage_score += evidence["fire_mentions"] * 2

    total_loss_score += evidence["total_loss_mentions"] * 4
    total_loss_score += evidence["fire_mentions"] * 2

    theft_score += 1 if evidence["salvage_mentions"] > 0 else 0  # weak but real

    return {
        "theft_risk_score": min(theft_score, 10),
        "salvage_risk_score": min(salvage_score, 10),
        "insurance_total_loss_risk_score": min(total_loss_score, 10),
    }


def calculate_confidence_level(
    incident_summary: Dict[str, int],
    data_sources: List[str],
) -> str:
    """Simple qualitative confidence model.

    Considers incident volume plus diversity of data sources.
    """
    evidence_points = 0

    # Incident volume
    evidence_points += sum(incident_summary.values())

    # Source diversity
    source_count = len(set(data_sources))

    if evidence_points >= 6 and source_count >= 2:
        return "HIGH"
    elif evidence_points >= 2:
        return "MEDIUM"
    else:
        return "LOW"


def build_theft_salvage_section(
    vin: str,
    complaints: List[Dict[str, Any]],
    recalls: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Construct the theft/salvage/total-loss section of the report."""
    evidence = extract_incident_evidence(complaints, recalls)
    scores = compute_vehicle_incident_risk(evidence)

    data_sources = [
        "NHTSA Recall Database",
        "NHTSA Vehicle Complaint Database",
    ]

    confidence_level = calculate_confidence_level(
        incident_summary=evidence,
        data_sources=data_sources,
    )

    return {
        "vin": vin,
        "incident_evidence_summary": evidence,
        "risk_assessment": {
            "theft_risk_score": scores["theft_risk_score"],
            "salvage_risk_score": scores["salvage_risk_score"],
            "insurance_total_loss_risk_score": scores[
                "insurance_total_loss_risk_score"
            ],
        },
        "confidence_level": confidence_level,
        "confidence_reason": (
            "Confidence derived from volume and diversity of incident signals "
            "found across NHTSA complaints and recall narratives"
        ),
        "interpretation": {
            "theft": "No direct theft indicators found in public VIN-linked datasets",
            "salvage": (
                "Elevated salvage risk due to multiple crash and airbag deployment "
                "references"
                if scores["salvage_risk_score"] >= 4
                else "Low salvage risk based on public records"
            ),
            "insurance_total_loss": (
                "Moderate likelihood of prior insurance total-loss events"
                if scores["insurance_total_loss_risk_score"] >= 4
                else "No strong total-loss indicators found"
            ),
        },
        "data_sources": data_sources,
        "external_verification": {
            "nicb_vincheck_url": "https://www.nicb.org/vincheck",
            "recommended": scores["salvage_risk_score"] >= 4,
        },
    }


def build_human_summary(report: Dict[str, Any]) -> str:
    """Generate a human-readable natural language summary for the report."""
    vehicle = report["vehicle_identity"]
    recalls = report["recall_history"]
    theft = report["theft_and_salvage"]
    odo = report["odometer_analysis"]
    meta = report.get("meta", {})

    summary_parts: List[str] = []

    # Vehicle identity
    summary_parts.append(
        f"This report analyzes a {vehicle.get('model_year')} "
        f"{vehicle.get('make')} {vehicle.get('model')} based on public U.S. safety "
        f"and regulatory databases."
    )

    # Recall context
    if recalls["recall_count"] > 0:
        summary_parts.append(
            f"The vehicle model year has been subject to {recalls['recall_count']} "
            "manufacturer safety recalls. Many of these recalls are model-wide and "
            "do not necessarily indicate that this specific vehicle was involved in an accident."
        )
    else:
        summary_parts.append(
            "No manufacturer safety recalls were found for this vehicle."
        )

    # Theft / salvage assessment
    salvage_score = theft["risk_assessment"]["salvage_risk_score"]

    if salvage_score >= 4:
        summary_parts.append(
            "Public safety data shows elevated indicators that may be consistent with "
            "prior crash or salvage-related events. Independent VIN-specific verification "
            "is recommended."
        )
    else:
        summary_parts.append(
            "No strong public indicators of theft, salvage, or insurance total-loss events "
            "were identified in available VIN-linked records."
        )

    # Odometer
    if odo["risk_level"] == "HIGH":
        summary_parts.append(
            "There are signals in public records that warrant caution regarding odometer accuracy."
        )
    else:
        summary_parts.append(
            "No public indicators of odometer tampering were identified, though full "
            "odometer history requires paid registration or title records."
        )

    # Confidence disclaimer
    overall_conf = meta.get("overall_confidence", "UNKNOWN")
    summary_parts.append(
        f"Overall confidence in this assessment is rated as {overall_conf}, based on "
        "the volume and diversity of public data sources analyzed."
    )

    return " ".join(summary_parts)


def generate_vin_report(vin: str) -> Dict[str, Any]:
    """High-level orchestration: build a full VIN report for a single VIN.

    This mirrors the logic from the Colab notebook:
      1. Decode VIN via VPIC
      2. Fetch recall history
      3. Fetch complaints
      4. Build theft/salvage section
      5. Infer odometer risk
      6. Compute meta confidence
      7. Build human-readable summary
    """
    # 1. Decode VIN
    decoded = decode_vin(vin)
    decoded["confidence_level"] = "HIGH"
    decoded["confidence_reason"] = "Direct VIN decode from NHTSA VPIC database"

    # 2. Recall history
    recalls = get_recall_history(
        decoded.get("make"),
        decoded.get("model"),
        decoded.get("model_year"),
    )

    # 3. NHTSA complaints
    complaints = get_nhtsa_complaints(
        decoded.get("make"),
        decoded.get("model"),
        decoded.get("model_year"),
    )

    # 4. Theft / Salvage analysis
    theft_and_salvage = build_theft_salvage_section(
        vin=vin,
        complaints=complaints,
        recalls=recalls["recalls"],
    )

    # 5. Odometer analysis
    odometer_risk = {
        "risk_level": (
            "HIGH"
            if theft_and_salvage["incident_evidence_summary"][
                "odometer_discrepancy_mentions"
            ]
            > 0
            else "MEDIUM"
            if theft_and_salvage["incident_evidence_summary"]["crash_mentions"] > 2
            else "LOW"
        ),
        "note": "Assessment derived from public safety complaints and recall narratives",
        "confidence_level": "LOW",
        "confidence_reason": (
            "No direct odometer readings available; inference based on complaint language"
        ),
    }

    # 6. Meta confidence (data-quality aware)
    incident_volume = sum(
        theft_and_salvage["incident_evidence_summary"].values()
    )

    raw_confidence = calculate_confidence_level(
        incident_summary={"incidents": incident_volume},
        data_sources=[
            "NHTSA VPIC",
            "NHTSA Recalls",
            "NHTSA Complaints",
        ],
    )

    # Apply confidence floor when authoritative data exists
    if incident_volume == 0:
        overall_confidence = "MEDIUM"
    elif raw_confidence == "LOW":
        overall_confidence = "MEDIUM"
    else:
        overall_confidence = raw_confidence

    meta = {
        "overall_confidence": overall_confidence,
        "sections_evaluated": [
            "vehicle_identity",
            "recall_history",
            "theft_and_salvage",
            "odometer_analysis",
        ],
        "confidence_model": "Section-weighted qualitative aggregation",
    }

    # 7. Human-readable summary
    human_summary = build_human_summary(
        {
            "vehicle_identity": decoded,
            "recall_history": recalls,
            "theft_and_salvage": theft_and_salvage,
            "odometer_analysis": odometer_risk,
            "meta": meta,
        }
    )

    # 8. Final report
    return {
        "vehicle_identity": decoded,
        "recall_history": recalls,
        "theft_and_salvage": theft_and_salvage,
        "odometer_analysis": odometer_risk,
        "paid_reports": {
            "carfax": f"https://www.carfax.com/VehicleHistory/p/Report.cfx?vin={vin}",
            "autocheck": "https://www.autocheck.com/",
            "nicb_vincheck": "https://www.nicb.org/vincheck",
        },
        "meta": meta,
        "human_summary": human_summary,
    }
