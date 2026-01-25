from backend.llm.negotiation_chatbot import negotiation_chat

sample_sla = {
    "Monthly Payment": None,
    "APR": None,
    "Early Termination Penalty": "200.00",
    "VIN": None
}

response = negotiation_chat(
    sample_sla,
    "Is this a good deal?"
)

print("\nAI Negotiation Response:\n")
print(response)
