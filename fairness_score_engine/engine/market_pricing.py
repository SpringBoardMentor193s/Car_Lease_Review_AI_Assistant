"""
Online market pricing adapter for dynamic buyout benchmarking.

This module is provider-agnostic. Configure your endpoint with:
- MARKET_PRICE_API_URL (required to enable online pricing)
- MARKET_PRICE_API_KEY (optional)
- MARKET_PRICE_API_KEY_HEADER (optional, default: x-api-key)
"""

from __future__ import annotations

import os
import logging
import time
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

import requests

from models.contract_facts import ContractFacts

logger = logging.getLogger(__name__)


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


class MarketPricingClient:
    """Fetch live market benchmark stats from an external API."""

    def __init__(self) -> None:
        self.provider = os.getenv("MARKET_PRICING_PROVIDER", "generic").strip().lower() or "generic"
        self.url = os.getenv("MARKET_PRICE_API_URL", "").strip()
        self.api_key = os.getenv("MARKET_PRICE_API_KEY", "").strip()
        self.api_secret = os.getenv("MARKET_PRICE_API_SECRET", "").strip()
        self.api_key_header = os.getenv("MARKET_PRICE_API_KEY_HEADER", "x-api-key").strip() or "x-api-key"
        self.marketcheck_oauth_url = os.getenv("MARKETCHECK_OAUTH_URL", "https://api.marketcheck.com/oauth2/token").strip()
        use_oauth_text = os.getenv("MARKETCHECK_USE_OAUTH", "true").strip().lower()
        self.marketcheck_use_oauth = use_oauth_text in {"1", "true", "yes", "on"}
        self.marketcheck_search_url = os.getenv(
            "MARKETCHECK_SEARCH_URL",
            "https://api.marketcheck.com/v2/search/car/active",
        ).strip()
        timeout_text = os.getenv("MARKET_PRICE_TIMEOUT_SEC", "8").strip()
        try:
            self.timeout_sec = max(2, int(timeout_text))
        except Exception:
            self.timeout_sec = 8
        self._oauth_token: Optional[str] = None
        self._oauth_expires_at: float = 0.0

    @property
    def enabled(self) -> bool:
        if self.provider == "marketcheck":
            return bool(self.api_key)
        return bool(self.url)

    def fetch_buyout_benchmark(self, facts: ContractFacts) -> Optional[Dict[str, Decimal]]:
        if not self.enabled:
            return None

        if self.provider == "marketcheck":
            return self._fetch_marketcheck_buyout_benchmark(facts)

        params = self._build_query_params(facts)
        headers: Dict[str, str] = {}
        if self.api_key:
            headers[self.api_key_header] = self.api_key

        try:
            resp = requests.get(self.url, params=params, headers=headers, timeout=self.timeout_sec)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as e:
            logger.warning("Online market pricing request failed: %s", e)
            return None

        stats = self._extract_stats(payload)
        if not stats:
            logger.warning("Online market pricing response did not include usable price stats")
            return None
        return stats

    def _fetch_marketcheck_buyout_benchmark(self, facts: ContractFacts) -> Optional[Dict[str, Decimal]]:
        """
        Query MarketCheck inventory search with stats=price and derive mean/std/min/max.
        This requires at minimum vehicle identity fields and location.
        """
        params = self._build_marketcheck_params(facts)
        if not params:
            return None

        headers: Dict[str, str] = {"Accept": "application/json"}
        if self.marketcheck_use_oauth and self.api_secret:
            token = self._get_marketcheck_access_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
            else:
                params["api_key"] = self.api_key
        else:
            params["api_key"] = self.api_key

        payload = self._execute_marketcheck_request(params, headers)
        if payload is None:
            return None

        stats = self._extract_marketcheck_stats(payload)
        if stats:
            return stats

        for relaxed_params in self._build_relaxed_marketcheck_params(params):
            payload_relaxed = self._execute_marketcheck_request(relaxed_params, headers)
            if payload_relaxed is None:
                continue
            stats_relaxed = self._extract_marketcheck_stats(payload_relaxed)
            if stats_relaxed:
                return stats_relaxed

        logger.warning("MarketCheck response missing usable price stats; falling back")
        return None

    def _build_relaxed_marketcheck_params(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build progressively broader fallback queries.
        """
        variants: List[Dict[str, Any]] = []

        if "city" in params:
            p1 = dict(params)
            p1.pop("city", None)
            variants.append(p1)

        if "state" in params or "zip" in params:
            p2 = dict(params)
            p2.pop("city", None)
            p2.pop("state", None)
            p2.pop("zip", None)
            variants.append(p2)

        if "year" in params:
            p3 = dict(params)
            p3.pop("city", None)
            p3.pop("state", None)
            p3.pop("zip", None)
            p3.pop("year", None)
            variants.append(p3)

        return variants

    def _execute_marketcheck_request(self, params: Dict[str, Any], headers: Dict[str, str]) -> Optional[Any]:
        try:
            resp = requests.get(
                self.marketcheck_search_url,
                params=params,
                headers=headers,
                timeout=self.timeout_sec,
            )
            # Some MarketCheck plans/endpoints accept api_key query auth but reject bearer auth.
            if resp.status_code == 401 and "Authorization" in headers:
                retry_params = dict(params)
                retry_params["api_key"] = self.api_key
                retry_headers = {"Accept": "application/json"}
                resp = requests.get(
                    self.marketcheck_search_url,
                    params=retry_params,
                    headers=retry_headers,
                    timeout=self.timeout_sec,
                )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning("MarketCheck pricing request failed: %s", e)
            return None

    def _build_marketcheck_params(self, facts: ContractFacts) -> Optional[Dict[str, Any]]:
        vin = getattr(facts, "vin", None)
        make = getattr(facts, "vehicle_make", None)
        model = getattr(facts, "vehicle_model", None)
        year = getattr(facts, "vehicle_year", None)
        city = facts.lessee_city
        state = facts.lessee_state

        # Need at least location + some vehicle identity to avoid broad-market noise.
        has_identity = bool(vin or (make and model and year))
        has_location = bool((city and state) or getattr(facts, "lessee_zip", None))
        if not has_identity or not has_location:
            logger.info(
                "MarketCheck skipped: insufficient identity/location (vin or year+make+model and city/state or zip required)"
            )
            return None

        params: Dict[str, Any] = {
            "rows": 0,
            "stats": "price",
        }

        # Use year/make/model for comparables. VIN is usually too restrictive for market stats.
        if make and model and year:
            params["year"] = str(year)
            params["make"] = str(make).lower()
            params["model"] = str(model).lower()
        elif make and model:
            params["make"] = str(make).lower()
            params["model"] = str(model).lower()
        elif vin:
            params["vins"] = vin
            params["match"] = "year,make,model,trim"
        else:
            return None

        if city and state:
            params["city"] = city
            params["state"] = state
        else:
            zip_code = getattr(facts, "lessee_zip", None)
            if zip_code:
                params["zip"] = zip_code

        miles = getattr(facts, "vehicle_mileage", None)
        if miles is not None:
            try:
                miles_val = int(miles)
                if miles_val > 0:
                    lower = max(0, miles_val - 20000)
                    upper = miles_val + 20000
                    params["miles_range"] = f"{lower}-{upper}"
            except Exception:
                pass

        return params

    def _extract_marketcheck_stats(self, payload: Any) -> Optional[Dict[str, Decimal]]:
        if not isinstance(payload, dict):
            return None

        stats_obj = payload.get("stats")
        if isinstance(stats_obj, dict):
            price_stats = stats_obj.get("price")
            if isinstance(price_stats, dict):
                # Field names can vary; handle common aliases.
                mean = _to_decimal(price_stats.get("avg")) or _to_decimal(price_stats.get("mean"))
                std = _to_decimal(price_stats.get("std")) or _to_decimal(price_stats.get("stddev"))
                min_val = _to_decimal(price_stats.get("min"))
                max_val = _to_decimal(price_stats.get("max"))
                if mean is not None:
                    if std is None:
                        std = max(Decimal("1200"), mean * Decimal("0.18"))
                    if min_val is None:
                        min_val = max(Decimal("1000"), mean - (std * Decimal("2")))
                    if max_val is None:
                        max_val = mean + (std * Decimal("2"))
                    return {
                        "mean": mean.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                        "std": std.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                        "min": min_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                        "max": max_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                    }

        # Fallback to generic parser for other structures.
        return self._extract_stats(payload)

    def _get_marketcheck_access_token(self) -> Optional[str]:
        now = time.time()
        if self._oauth_token and now < self._oauth_expires_at:
            return self._oauth_token
        if not self.api_key or not self.api_secret:
            return None
        try:
            resp = requests.post(
                self.marketcheck_oauth_url,
                json={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.api_secret,
                },
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                timeout=self.timeout_sec,
            )
            resp.raise_for_status()
            data = resp.json()
            token = data.get("access_token")
            expires_in = int(data.get("expires_in", 3600))
            if not token:
                return None
            # Refresh slightly early to avoid edge expiry.
            self._oauth_token = token
            self._oauth_expires_at = now + max(60, expires_in - 60)
            return token
        except Exception as e:
            logger.warning("MarketCheck OAuth token fetch failed: %s", e)
            return None

    def _build_query_params(self, facts: ContractFacts) -> Dict[str, Any]:
        location_parts = [facts.lessee_city, facts.lessee_state, facts.lease_region]
        location = ", ".join([p.strip() for p in location_parts if p and str(p).strip()])

        params: Dict[str, Any] = {
            "location": location or None,
            "condition": facts.vehicle_condition,
            "lease_term_months": facts.lease_term_months,
            "mileage_limit_per_year": facts.mileage_limit_per_year,
            "monthly_payment": str(facts.monthly_payment) if facts.monthly_payment is not None else None,
            "down_payment": str(facts.down_payment) if facts.down_payment is not None else None,
            "residual_value_percent": str(facts.residual_value_percent) if facts.residual_value_percent is not None else None,
            "residual_value_amount": str(facts.residual_value_amount) if facts.residual_value_amount is not None else None,
            "buyout_price": str(facts.buyout_price) if facts.buyout_price is not None else None,
        }
        return {k: v for k, v in params.items() if v is not None}

    def _extract_stats(self, payload: Any) -> Optional[Dict[str, Decimal]]:
        if isinstance(payload, dict):
            direct = self._extract_direct_stats(payload)
            if direct:
                return direct

            for key in ("benchmark", "stats", "data", "result"):
                nested = payload.get(key)
                if isinstance(nested, dict):
                    direct_nested = self._extract_direct_stats(nested)
                    if direct_nested:
                        return direct_nested

            prices = self._extract_prices(payload)
            if prices:
                return self._stats_from_prices(prices)

        elif isinstance(payload, list):
            prices: List[Decimal] = []
            for item in payload:
                val = _to_decimal(item)
                if val is not None and val > 0:
                    prices.append(val)
            if prices:
                return self._stats_from_prices(prices)

        return None

    def _extract_direct_stats(self, data: Dict[str, Any]) -> Optional[Dict[str, Decimal]]:
        mean = _to_decimal(data.get("mean"))
        std = _to_decimal(data.get("std"))
        min_val = _to_decimal(data.get("min"))
        max_val = _to_decimal(data.get("max"))
        if mean is None or std is None:
            return None
        if min_val is None:
            min_val = max(Decimal("1000"), mean - (std * Decimal("2")))
        if max_val is None:
            max_val = mean + (std * Decimal("2"))
        return {
            "mean": mean.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "std": std.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "min": min_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "max": max_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        }

    def _extract_prices(self, data: Dict[str, Any]) -> List[Decimal]:
        prices: List[Decimal] = []
        list_keys = ("prices", "comparable_prices", "listings", "results", "items")
        scalar_keys = ("price", "amount", "listing_price", "market_price")

        for key in list_keys:
            rows = data.get(key)
            if not isinstance(rows, list):
                continue
            for row in rows:
                if isinstance(row, (int, float, str)):
                    val = _to_decimal(row)
                    if val is not None and val > 0:
                        prices.append(val)
                    continue
                if not isinstance(row, dict):
                    continue
                for sk in scalar_keys:
                    val = _to_decimal(row.get(sk))
                    if val is not None and val > 0:
                        prices.append(val)
                        break
        return prices

    def _stats_from_prices(self, prices: List[Decimal]) -> Optional[Dict[str, Decimal]]:
        if len(prices) < 3:
            return None
        prices_sorted = sorted(prices)
        n = Decimal(str(len(prices_sorted)))
        mean = sum(prices_sorted, Decimal("0")) / n
        variance = sum((p - mean) * (p - mean) for p in prices_sorted) / n
        std = variance.sqrt() if variance > 0 else Decimal("1200")
        std = max(std, Decimal("1200"))
        min_val = prices_sorted[0]
        max_val = prices_sorted[-1]
        return {
            "mean": mean.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "std": std.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "min": min_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "max": max_val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        }
