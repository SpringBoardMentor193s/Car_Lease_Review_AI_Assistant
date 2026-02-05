import google.generativeai as genai

class NegotiationService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-pro")

    def get_negotiation_advice(self, user_query: str, analysis_data: dict, chat_history: list = []):
        """
        Generates specific negotiation points or responses to dealer questions.
        """
        context = f"""
        You are a car lease negotiation expert. 
        Current Contract Stats:
        - Monthly Payment: {analysis_data.get('monthly_payment')}
        - APR/Money Factor: {analysis_data.get('apr')}
        - Residual Value: {analysis_data.get('residual_value')}
        - Red Flags: {", ".join(analysis_data.get('red_flags', []))}
        
        Goal: Help the user negotiate better terms or explain if these terms are fair.
        """
        
        chat = self.model.start_chat(history=chat_history)
        prompt = f"{context}\n\nUser Question: {user_query}\nExpert Advice:"
        
        response = chat.send_message(prompt)
        return response.text