import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# NASA-Grade Styling
st.set_page_config(page_title="Vanguard SaaS Analytics", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .stMetric { background-color: #1e293b; padding: 20px; border-radius: 15px; border: 1px solid #334155; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌑 VANGUARD SYSTEM ANALYTICS")
st.subheader("Grok-Persona Production Monitoring | 2026-2027")

# Mock Data for Intelligence Display
col1, col2, col3, col4 = st.columns(4)
col1.metric("Compliance Rate", "100%", "0% Drift")
col2.metric("Avg. Processing Time", "4.2s", "-1.2s", delta_color="inverse")
col3.metric("Audit integrity", "SHA-256", "Active")
col4.metric("Active Jobs", "128", "+12")

st.divider()

# Recent Job Activity
st.write("### 🛡️ Recent PWD Bill Generations")
df = pd.DataFrame({
    "Job ID": ["JO-2026-X77", "JO-2026-Y88", "JO-2026-Z99", "JO-2026-A11"],
    "Status": ["Complete", "Complete", "Processing", "Complete"],
    "Total Amount": [558100.00, 292500.00, 1250000.00, 42000.00],
    "Hash Verified": [True, True, True, True]
})
st.table(df)

# ROI Visualization
st.write("### 📈 Operational Efficiency (Manual vs AI)")
chart_data = pd.DataFrame({
    "Method": ["Manual Data Entry", "Vanguard OCR"],
    "Hours per Bill": [14.0, 0.4]
})
fig = px.bar(chart_data, x="Method", y="Hours per Bill", color="Method", template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

st.info("💡 Vanguard Engine is currently running in 'Grok-Persona' mode with full statutory parity.")
