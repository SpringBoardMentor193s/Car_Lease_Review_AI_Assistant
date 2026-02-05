from __future__ import annotations

import json
import os
import time
from typing import Dict, List, Optional, Tuple

import requests

DEFAULT_MODEL = "stepfun/step-3.5-flash:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
FREE_MODEL_SUFFIX = ":free"
FALLBACK_FREE_MODELS = [
    "stepfun/step-3.5-flash:free"
]
SOURCE_TEXT_LIMIT = 0
PAYLOAD_CHAR_LIMIT = 8000


def _compact_sla_data(sla_data: Dict) -> Dict:
    if not sla_data:
        return {}
    keep_keys = {
        "apr_percent",
        "lease_term_months",
        "monthly_payment",
        "down_payment",
        "residual_value",
        "mileage_per_year",
        "overage_per_mile",
        "buyout_price",
    }
    return {
        key: value
        for key, value in sla_data.items()
        if key in keep_keys and value not in (None, "", [])
    }


def _compact_vin_details(vin_details: Dict[str, str]) -> Dict[str, str]:
    if not vin_details:
        return {}
    return {key: value for key, value in vin_details.items() if value not in (None, "", [])}


def _build_sla_summary(sla_data: Dict) -> str:
    if not sla_data:
        return "No SLA data extracted."
    parts = []
    mapping = [
        ("apr_percent", "APR"),
        ("lease_term_months", "Term (months)"),
        ("monthly_payment", "Monthly payment"),
        ("down_payment", "Down payment"),
        ("residual_value", "Residual value"),
        ("mileage_per_year", "Mileage per year"),
        ("overage_per_mile", "Overage per mile"),
        ("buyout_price", "Buyout price"),
    ]
    for key, label in mapping:
        value = sla_data.get(key)
        if value not in (None, "", []):
            parts.append(f"{label}: {value}")
    return "; ".join(parts) if parts else "No SLA data extracted."




def build_payload(
    *,
    source_text: str,
    sla_data: Dict,
    vin_value: Optional[str],
    vin_details: Dict[str, str],
    user_goals: Dict[str, Optional[str]],
) -> Dict:
    compact_sla = _compact_sla_data(sla_data)
    compact_vin = _compact_vin_details(vin_details)
    payload = {
        "source_text": "",
        "source_text_included": False,
        "sla_extraction": compact_sla,
        "sla_summary": _build_sla_summary(compact_sla),
        "vin": {
            "value": vin_value,
            "details": compact_vin,
        },
        "user_goals": user_goals,
        "output_requirements": {
            "tone": "concise, practical, negotiation-focused",
            "format": [
                "summary",
                "key leverage points",
                "counteroffer strategy",
                "questions to ask",
                "negotiation script",
                "red flags",
            ],
            "avoid": [
                "legal advice",
                "inventing numbers not in data",
                "claiming certainty without evidence",
            ],
        },
    }

    payload_size = len(json.dumps(payload, ensure_ascii=False))
    if payload_size > PAYLOAD_CHAR_LIMIT:
        payload["vin"]["details"] = {}
        payload["sla_summary"] = _build_sla_summary(compact_sla)

    return payload


def _build_messages(payload: Dict) -> List[Dict[str, str]]:
    system_prompt = (
        "You are a car lease negotiation assistant. Use only the provided JSON data. "
        "Be transparent about missing information. Do not invent values. "
        "Provide negotiation guidance, counteroffers, and a short script. "
        "Respond with final answer only. Do not include analysis or reasoning. "
        "Keep the response under 450 words. Use concise bullet points."
    )
    user_content = json.dumps(payload, ensure_ascii=False, indent=2)
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]


def generate_negotiation_response(payload: Dict) -> Tuple[Optional[str], Optional[str], str]:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    key_status = "yes" if api_key else "no"
    if not api_key:
        return None, "Missing OPENROUTER_API_KEY environment variable. (key present: no)", ""

    model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
    if FREE_MODEL_SUFFIX not in model:
        return None, "OPENROUTER_MODEL must be a free model (suffix :free).", model
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    site_url = os.getenv("OPENROUTER_SITE_URL", "").strip() or "http://localhost"
    app_name = os.getenv("OPENROUTER_APP_NAME", "Lease Negotiation Assistant").strip()
    headers["HTTP-Referer"] = site_url
    if app_name:
        headers["X-Title"] = app_name

    models_to_try = [model] + [m for m in FALLBACK_FREE_MODELS if m != model]
    last_error = "OpenRouter error."

    for candidate in models_to_try:
        payload_body = {
            "model": candidate,
            "messages": _build_messages(payload),
            "temperature": 0.4,
        }

        try:
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload_body, timeout=30)
        except requests.RequestException as exc:
            last_error = f"OpenRouter request failed: {exc} (key present: {key_status}, model: {candidate})"
            continue

        content_type = response.headers.get("Content-Type", "").lower()
        data = None
        if "application/json" in content_type:
            try:
                data = response.json()
            except ValueError:
                body_preview = response.text[:500].strip() if response.text else "<empty body>"
                last_error = (
                    f"OpenRouter returned invalid JSON (status {response.status_code}). "
                    f"Body: {body_preview} (key present: {key_status}, model: {candidate})"
                )
                continue
        else:
            raw_body = response.text.strip()
            if response.status_code < 400 and raw_body:
                return raw_body, None, candidate
            body_preview = raw_body[:500] if raw_body else "<empty body>"
            last_error = (
                f"OpenRouter returned non-JSON body (status {response.status_code}). "
                f"Body: {body_preview} (key present: {key_status}, model: {candidate})"
            )
            continue

        if response.status_code == 429:
            last_error = (
                f"Rate limited by provider (status: 429, key present: {key_status}, model: {candidate}). "
                "Wait a minute and retry."
            )
            time.sleep(1.5)
            continue

        if response.status_code >= 400 or "error" in data:
            error = data.get("error", {})
            message = error.get("message", "OpenRouter error.")
            provider_message = error.get("metadata", {}).get("provider_error")
            if provider_message:
                message = f"{message} (provider: {provider_message})"
            last_error = (
                f"{message} (status: {response.status_code}, key present: {key_status}, model: {candidate})"
            )
            continue

        choices = data.get("choices", [])
        if not choices:
            last_error = f"OpenRouter returned no choices. (key present: {key_status}, model: {candidate})"
            continue
        message = choices[0].get("message", {})
        content = (message.get("content") or "").strip()
        if not content:
            content = (message.get("reasoning") or "").strip()
        if not content:
            content = (choices[0].get("text") or "").strip()
        if not content:
            content = (data.get("output_text") or "").strip()
        if not content:
            raw_preview = json.dumps(data, ensure_ascii=False)[:500]
            last_error = (
                "OpenRouter returned an empty response. "
                f"Body: {raw_preview} (key present: {key_status}, model: {candidate})"
            )
            continue

        return content, None, candidate

    return None, last_error, model