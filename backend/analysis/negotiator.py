import os
from groq import Groq

# -------------------- SYSTEM PROMPT -------------------- #

SYSTEM_PROMPT = """
You are a professional car lease negotiation assistant used in a consumer finance advisory system.

Your responsibilities:
- Explain lease terms clearly to non-technical users
- Identify risky, unfair, or negotiable clauses
- Suggest realistic and practical negotiation strategies
- Provide short dealer-ready negotiation sentences

Strict rules:
- Use ONLY the provided contract, SLA data, risk assessment, and vehicle data
- Do NOT invent numbers, clauses, or policies
- Do NOT provide legal guarantees or legal advice
- Be polite, calm, and professional
- Focus on financial fairness, safety, and negotiation leverage
- If data is missing, clearly say so

Output style:
- Start with a brief risk-based assessment (2–3 lines)
- Then list key negotiation points (bullet points)
- Then provide 3–5 dealer-ready negotiation sentences
- End with a short caution or tip
"""

# -------------------- CLIENT -------------------- #

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# -------------------- NEGOTIATION FUNCTION -------------------- #

def negotiate_with_user(user_message: str, sla_data: dict, risk_data: dict, vehicle_data: dict):

    try:
        # 🧠 Build clean structured context
        context = f"""
SLA DATA:
{sla_data}

RISK ASSESSMENT:
{risk_data}

VEHICLE DATA:
{vehicle_data}
"""

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context},
            {"role": "user", "content": user_message}
        ]

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",   # ✅ ACTIVE GROQ MODEL
            messages=messages,
            temperature=0.3,               # lower = more stable, less hallucination
            max_tokens=500
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        # 🔴 LOG ERROR (VERY IMPORTANT FOR DEBUGGING)
        print("Negotiator error:", str(e))

        return (
            "I’m currently unable to generate negotiation advice due to a system issue. "
            "Please try again in a moment."
        )
