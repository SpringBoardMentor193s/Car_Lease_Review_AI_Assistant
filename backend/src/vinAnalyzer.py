"""
VIN Analyzer Module
Handles VIN decoding and analysis using Ollama
"""

import json
import ollama


def analyze_vin(vin_number: str):
    """Analyze a VIN using Ollama and return JSON-decoded result."""
    vin = vin_number.strip().upper()

    # Local deterministic decode (basic ISO 3779 fields)
    def local_decode(v):
        mapping_year = {
            'A': 2010, 'B': 2011, 'C': 2012, 'D': 2013, 'E': 2014, 'F': 2015, 'G': 2016,
            'H': 2017, 'J': 2018, 'K': 2019, 'L': 2020, 'M': 2021, 'N': 2022, 'P': 2023,
            'R': 2024, 'S': 2025, 'T': 2026, 'V': 2027, 'W': 2028, 'X': 2029, 'Y': 2030,
            '1': 2001, '2': 2002, '3': 2003, '4': 2004, '5': 2005, '6': 2006, '7': 2007, '8': 2008, '9': 2009
        }

        country_codes = {
            '1': 'United States', '4': 'United States', '5': 'United States',
            '2': 'Canada', '3': 'Mexico', 'J': 'Japan', 'K': 'Korea', 'S': 'United Kingdom',
            'W': 'Germany', 'Z': 'Italy', 'Y': 'Sweden/Finland', 'V': 'France/Spain'
        }

        decoded = {
            'vin': v,
            'country': country_codes.get(v[0], 'Unknown'),
            'manufacturer': v[1:3],
            'vehicle_attributes': v[3:8],
            'check_digit': v[8],
            'model_year_code': v[9],
            'model_year': mapping_year.get(v[9], 'Unknown'),
            'plant_code': v[10],
            'serial_number': v[11:17]
        }

        return decoded

    local = None
    if len(vin) == 17:
        local = local_decode(vin)
    else:
        local = {'error': 'VIN must be 17 characters', 'vin': vin}

    # System prompt with strict JSON requirement and Team-BHP exception logic
    system_prompt = (
        "You are a VIN decoding assistant. Follow ISO 3779 rules: 1st character=country, 2nd-3rd=manufacturer, "
        "positions 4-8=vehicle attributes, 9th=check digit, 10th=model year, 11th=plant, 12-17=serial.\n\n"
        "Important: If the VIN appears to use Team-BHP exceptions (brands like Chevrolet or Mahindra where the 7th char may represent month and 9th char may represent year), detect and note this in 'exceptions'.\n\n"
        "You must produce ONLY valid JSON with these exact keys:\n"
        "- decoded: object with detailed VIN breakdown\n"
        "- exceptions: array of strings noting any decoding exceptions\n"
        "- confidence: number between 0-100\n"
        "- explanation: short text description\n\n"
        "Use the local decoding as the baseline and correct or augment it as needed."
    )

    user_message = f"VIN: {vin}\nLocal decode: {json.dumps(local)}"

    try:
        # Try primary call with JSON format
        print(f"[DEBUG] Analyzing VIN: {vin}")
        response = ollama.chat(
            model='llama3.2',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            format='json'
        )

        content = response['message']['content']
        print(f"[DEBUG] VIN Ollama response: {content[:200]}...")

        # Attempt to parse JSON
        try:
            parsed = json.loads(content)
            # attach local decode for frontend convenience
            parsed.setdefault('local_decoded', local)
            print(f"[DEBUG] VIN parsed successfully")
            return parsed
        except Exception as parse_err:
            print(f"[WARN] VIN JSON parse failed: {parse_err}. Retrying...")
            # Retry once with a correction instruction
            correction_prompt = (
                "The previous response was not valid JSON. Here is the response:\n" + content +
                "\n\nPlease respond ONLY with valid JSON matching this schema: {\n  \"decoded\": {...},\n  \"exceptions\": [...],\n  \"confidence\": number,\n  \"explanation\": \"short text\"\n}\nDo not add any extra text."
            )

            response2 = ollama.chat(
                model='llama3.2',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': correction_prompt}
                ],
                format='json'
            )

            content2 = response2['message']['content']
            print(f"[DEBUG] VIN retry response: {content2[:200]}...")
            try:
                parsed2 = json.loads(content2)
                parsed2.setdefault('local_decoded', local)
                print(f"[DEBUG] VIN retry parsed successfully")
                return parsed2
            except Exception as parse_err2:
                # give up and return local decode plus raw contents
                print(f"[ERROR] VIN retry also failed: {parse_err2}")
                return {'error': 'Model returned non-JSON content', 'raw': content, 'retry_raw': content2, 'local_decoded': local}

    except Exception as e:
        print(f"[ERROR] VIN Ollama call failed: {str(e)}")
        return {'error': f'Ollama call failed: {str(e)}', 'local_decoded': local}
