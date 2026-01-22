import streamlit as st
import requests
import json

# Configuration
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Car Lease AI Assistant", layout="wide")

st.title("🚗 Car Lease Review AI Assistant")
st.markdown("Upload your car lease contract and get AI-powered insights, fairness scoring, and negotiation tips.")

# Sidebar - Tools
st.sidebar.header("Tools")
tool_option = st.sidebar.radio("Select Tool", ["Contract Analysis", "Negotiation Assistant", "VIN Check"])

if tool_option == "Contract Analysis":
    st.header("📄 Contract Analysis & Feature Extraction")
    
    uploaded_file = st.file_uploader("Upload Lease Agreement (Image or PDF)", type=["png", "jpg", "jpeg", "pdf", "txt"])
    
    if uploaded_file is not None:
        if st.button("Analyze Contract"):
            with st.spinner("Analyzing... (OCR + LLM Extraction)"):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                    response = requests.post(f"{API_URL}/analysis/upload", files=files)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success("Analysis Complete!")
                        
                        # Display Results
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("📑 Extracted Clauses")
                            clauses = data.get("clauses", {})
                            st.json(clauses)
                            
                        with col2:
                            st.subheader("⚖️ Fairness Score")
                            score = data.get("fairness_score", 0)
                            st.metric(label="Fairness Score (0-100)", value=score)
                            st.info(data.get("fairness_explanation", "No explanation available."))
                            
                            st.subheader("💰 Market Price Estimation")
                            p_min = data.get("market_price_min")
                            p_max = data.get("market_price_max")
                            st.write(f"Estimated Market Price: **${p_min:,.2f} - ${p_max:,.2f}**")
                            
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")

elif tool_option == "Negotiation Assistant":
    st.header("💬 AI Negotiation Assistant")
    st.markdown("Ask questions about your lease or get negotiation strategies.")
    
    # Simple Chat Interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about high APR, hidden fees, etc..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                response = requests.post(f"{API_URL}/chat/", json={"message": prompt})
                if response.status_code == 200:
                    bot_reply = response.json().get("response")
                    st.markdown(bot_reply)
                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                else:
                    st.error("Error from Chat API")
            except Exception as e:
                st.error(f"Connection Error: {e}")

elif tool_option == "VIN Check":
    st.header("🔍 VIN Vehicle History")
    vin_input = st.text_input("Enter VIN Number")
    
    if st.button("Check VIN"):
        st.info("Fetching MOCK VIN Data...")
        # Direct call to service logic replica OR add endpoint if needed.
        # For Demo, just showing mock data directly here or could hit an endpoint if we made one.
        # We didn't explicitly make a standalone VIN endpoint, but analysis returns it.
        # Let's just mock it here for the UI demo as per the Analysis response structure.
        st.json({
            "Make": "Toyota",
            "Model": "Camry",
            "Year": 2024,
            "RecallCount": 0,
            "SafetyRating": "5 Stars"
        })

