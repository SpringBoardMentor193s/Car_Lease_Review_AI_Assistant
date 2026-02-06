"""
LLM-based extractor for car lease contract parameters.

This module uses Groq's free API with Llama 3 to reliably extract SLA parameters
from real lease contracts with varied formats and terminology.

Groq offers free API access - get your key at: https://console.groq.com/keys
"""

import os
import json
import logging
from decimal import Decimal
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Check for Groq availability
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq not installed. Run: pip install groq")


# The fields we want to extract, with descriptions to guide the LLM
EXTRACTION_SCHEMA = {
    "apr": "Annual Percentage Rate (APR) or interest rate as a percentage number (e.g., 3.5 for 3.5%)",
    "monthly_payment": "Monthly payment amount in dollars (just the number, e.g., 450.00)",
    "lease_term_months": "Lease duration in months (e.g., 36)",
    "down_payment": "Down payment or capitalized cost reduction in dollars",
    "mileage_limit_per_year": "Annual mileage allowance/limit (e.g., 12000)",
    "overage_fee_per_mile": "Excess mileage fee per mile in dollars (e.g., 0.25)",
    "early_termination_policy": "Early termination fee or policy description",
    "residual_value_percent": "Residual value as a percentage of MSRP (e.g., 55 for 55%)",
    "residual_value_amount": "Residual value amount in dollars if stated as a dollar value (e.g., 18000)",
    "late_fee_policy": "Late payment fee or policy description",
    "maintenance_responsibility": "Who is responsible for maintenance: 'lessee', 'lessor', or 'shared'",
    "buyout_price": "Purchase option or buyout price in dollars",
    "warranty_coverage": "Warranty coverage details",
    "insurance_coverage": "Insurance requirements or coverage details"
}

SYSTEM_PROMPT = """You are an expert at extracting structured data from car lease contracts.
Extract the requested fields from the contract text. Be precise with numbers.

Rules:
- Extract ONLY values explicitly stated in the contract
- For monetary values, extract just the number (no $ sign)
- For percentages, extract just the number (no % sign)
- If a field is not found or unclear, return null
- For policy descriptions, provide a brief summary (max 100 characters)
- maintenance_responsibility must be exactly one of: "lessee", "lessor", "shared", or null

Return a valid JSON object with the extracted values."""


class LLMExtractor:
    """Extract lease contract parameters using Groq's free Llama 3 API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the LLM extractor.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
                    Get free key at: https://console.groq.com/keys
            model: Groq model to use (default: llama-3.3-70b-versatile)
                   Other options: llama-3.1-8b-instant, mixtral-8x7b-32768
        """
        if not GROQ_AVAILABLE:
            raise ImportError("Groq package not installed. Run: pip install groq")
        
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Groq API key not provided. Get a free key at https://console.groq.com/keys\n"
                "Then set: $env:GROQ_API_KEY = 'your-key'"
            )
        
        self.client = Groq(api_key=self.api_key)
        self.model = model
    
    def extract_fields(self, text: str) -> Dict[str, Any]:
        """
        Extract SLA parameters from contract text using LLM.
        
        Args:
            text: The contract text to extract from
            
        Returns:
            Dictionary of extracted field values
        """
        if not text or len(text.strip()) < 50:
            logger.warning("Text too short for extraction")
            return {}
        
        # Build the extraction prompt
        fields_description = "\n".join(
            f"- {field}: {description}" 
            for field, description in EXTRACTION_SCHEMA.items()
        )
        
        user_prompt = f"""Extract the following fields from this car lease contract:

{fields_description}

CONTRACT TEXT:
{text[:15000]}  # Limit text length to avoid token limits

Return a JSON object with the extracted values. Use null for fields not found."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=1024
            )
            
            result_text = response.choices[0].message.content
            extracted = json.loads(result_text)
            
            # Post-process and validate extracted values
            return self._post_process(extracted)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return {}
    
    def _post_process(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-process extracted values to ensure correct types.
        
        Args:
            extracted: Raw extracted dictionary from LLM
            
        Returns:
            Cleaned dictionary with proper types
        """
        result = {}
        
        # Numeric fields that should be Decimal
        decimal_fields = [
            'apr', 'monthly_payment', 'down_payment', 
            'overage_fee_per_mile', 'residual_value_percent', 'residual_value_amount', 'buyout_price'
        ]
        
        # Integer fields
        int_fields = ['lease_term_months', 'mileage_limit_per_year']
        
        # String fields
        string_fields = [
            'early_termination_policy', 'late_fee_policy',
            'maintenance_responsibility', 'warranty_coverage', 'insurance_coverage'
        ]
        
        for field in decimal_fields:
            value = extracted.get(field)
            if value is not None:
                try:
                    # Handle string numbers like "$450" or "3.5%"
                    if isinstance(value, str):
                        value = value.replace('$', '').replace('%', '').replace(',', '').strip()
                    result[field] = Decimal(str(value))
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert {field}={value} to Decimal")
        
        for field in int_fields:
            value = extracted.get(field)
            if value is not None:
                try:
                    if isinstance(value, str):
                        value = value.replace(',', '').strip()
                    result[field] = int(float(value))
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert {field}={value} to int")
        
        for field in string_fields:
            value = extracted.get(field)
            if value is not None and value != "null" and str(value).strip():
                # Normalize maintenance_responsibility
                if field == 'maintenance_responsibility':
                    value = str(value).lower().strip()
                    if value not in ('lessee', 'lessor', 'shared'):
                        continue
                result[field] = str(value).strip()
        
        return result


class HybridExtractor:
    """
    Combines regex-based and LLM-based extraction.
    Uses regex first for speed, falls back to LLM for complex documents.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize hybrid extractor.
        
        Args:
            api_key: Groq API key for LLM extraction
            model: Groq model to use
        """
        from engine.pdf_extractor import PDFExtractor
        
        self.regex_extractor = PDFExtractor()
        self.llm_extractor = None
        
        # Only initialize LLM if API key is available
        if api_key or os.getenv("GROQ_API_KEY"):
            try:
                self.llm_extractor = LLMExtractor(api_key=api_key, model=model)
            except (ImportError, ValueError) as e:
                logger.warning(f"LLM extractor not available: {e}")
    
    def extract_fields(self, text: str, force_llm: bool = False) -> Dict[str, Any]:
        """
        Extract fields using hybrid approach.
        
        Args:
            text: Contract text to extract from
            force_llm: Skip regex and use LLM directly
            
        Returns:
            Dictionary of extracted values
        """
        if force_llm and self.llm_extractor:
            logger.info("Using LLM extraction (forced)")
            return self.llm_extractor.extract_fields(text)
        
        # Try regex first
        regex_result = self.regex_extractor.extract_fields(text)
        
        # Check if we got enough required fields
        required_fields = ['apr', 'monthly_payment', 'lease_term_months']
        found_required = sum(1 for f in required_fields if f in regex_result and regex_result[f] is not None)
        
        if found_required >= 2:
            logger.info(f"Regex extraction successful ({len(regex_result)} fields)")
            return regex_result
        
        # Fall back to LLM for complex documents
        if self.llm_extractor:
            logger.info("Regex extraction insufficient, using LLM")
            llm_result = self.llm_extractor.extract_fields(text)
            
            # Merge results (LLM takes precedence for missing fields)
            merged = {**regex_result, **llm_result}
            return merged
        
        logger.warning("LLM not available, returning partial regex results")
        return regex_result
