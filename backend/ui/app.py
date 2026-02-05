import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/analyze-contract"

st.set_page_config(
    page_title="Car Lease Contract AI",
    layout="centered"
)

st.title("🚗 Car Lease / Loan Contract Analyzer")
st.caption("Upload a contract PDF to analyze pricing fairness and negotiation insights.")

st.divider()

uploaded_file = st.file_uploader(
    "📄 Upload Lease / Loan Contract (PDF only)",
    type=["pdf"]
)

if uploaded_file is not None:
    st.info("⏳ Analyzing contract, please wait...")

    files = {
        "file": (uploaded_file.name, uploaded_file, "application/pdf")
    }

    try:
        response = requests.post(API_URL, files=files)

        if response.status_code != 200:
            st.error("❌ Backend error. Make sure FastAPI is running.")
        else:
            result = response.json()

            if result.get("status") != "success":
                st.error("❌ Analysis failed.")
            else:
                st.success("✅ Analysis completed successfully")

                # ---------------- CONTRACT DETAILS ----------------
                st.subheader("📄 Contract Summary")
                st.json(result.get("contract_analysis"))

                # ---------------- VEHICLE DETAILS ----------------
                st.subheader("🚘 Vehicle Details")
                vehicle = result.get("vehicle_details")

                if vehicle:
                    st.json(vehicle)
                else:
                    st.warning("Vehicle details not available")

                # ---------------- FAIRNESS SCORE ----------------
                st.subheader("⚖️ Fairness Score")
                fairness = result.get("fairness", {})
                score = fairness.get("score")

                if score == "unknown":
                    st.warning("Fairness score could not be determined due to missing pricing data.")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Score (out of 100)", score)
                    with col2:
                        if score >= 80:
                            st.success("🟢 Deal looks fair")
                        elif score >= 60:
                            st.warning("🟡 Deal is average")
                        else:
                            st.error("🔴 Deal may be unfavorable")

                if fairness.get("reasons"):
                    st.write("**Key Factors:**")
                    for reason in fairness["reasons"]:
                        st.write(f"- {reason}")

                # ---------------- NEGOTIATION ADVICE ----------------
                st.subheader("💬 Negotiation Advice")

                st.text_area(
                    "AI-Generated Suggestions",
                    result.get("negotiation_advice"),
                    height=400
                )

    except Exception as e:
        st.error(f"❌ Error connecting to backend: {e}")
