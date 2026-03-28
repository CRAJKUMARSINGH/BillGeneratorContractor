#!/usr/bin/env python3
"""
STREAMLIT APP INTEGRATION — Gemini Vision OCR Tab
==================================================
Drop this file into the app as a module.
Adds a "Gemini Vision" option to the OCR method selector in the Streamlit UI.

Usage in app.py:
    from ocr_gemini_tab import render_gemini_ocr_tab
    render_gemini_ocr_tab()
"""

import os
import json
import time
import streamlit as st
from pathlib import Path
from typing import List, Dict

# ── Import Gemini Vision parser ───────────────────────────────────────────────
try:
    from modules.gemini_vision_parser import GeminiVisionParser
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def render_gemini_ocr_tab():
    """
    Renders the Gemini Vision OCR section in Streamlit.
    Call this inside a st.tab() or directly in your app.
    """
    st.subheader("🤖 AI-Powered OCR (Gemini Vision)")

    # ── API key configuration ─────────────────────────────────────────────────
    col1, col2 = st.columns([3, 1])
    with col1:
        api_key = st.text_input(
            "Gemini API Key",
            value=os.getenv("GEMINI_API_KEY", ""),
            type="password",
            help=(
                "Free API key from https://aistudio.google.com/app/apikey\n"
                "Or set env var: GEMINI_API_KEY=your_key"
            ),
        )
    with col2:
        st.markdown(
            '<br><a href="https://aistudio.google.com/app/apikey" target="_blank">'
            '🔗 Get Free Key</a>',
            unsafe_allow_html=True,
        )

    if not api_key:
        st.info(
            "💡 **Get a FREE Gemini API key** at [aistudio.google.com](https://aistudio.google.com/app/apikey)"
            "\n\n"
            "Free tier: **1500 requests/day** — more than enough for all your work orders."
        )
        return

    # ── Image upload ──────────────────────────────────────────────────────────
    st.markdown("#### Upload Work Order Images")
    uploaded_files = st.file_uploader(
        "Upload all 5 work order images (JPEG/PNG)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Upload all pages of your work order. Gemini will read ALL pages.",
    )

    if not uploaded_files:
        st.warning("Please upload at least one work order image.")
        return

    st.success(f"✅ {len(uploaded_files)} image(s) uploaded")

    # Show thumbnails
    cols = st.columns(min(len(uploaded_files), 5))
    for i, file in enumerate(uploaded_files):
        with cols[i % 5]:
            st.image(file, caption=f"Page {i+1}", use_column_width=True)

    # ── Extract button ────────────────────────────────────────────────────────
    if st.button("🔍 Extract Items from Images", type="primary"):
        # Save uploaded files to temp dir
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Save each file
            for file in uploaded_files:
                file_path = tmp_path / file.name
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())

            # Run extraction
            with st.spinner("🤖 Gemini Vision is reading your work order..."):
                try:
                    parser = GeminiVisionParser(api_key=api_key)

                    if not parser.available:
                        st.error("❌ Gemini Vision could not be initialized. Check your API key.")
                        return

                    progress = st.progress(0)
                    status = st.empty()

                    # Process each image
                    all_items: List[Dict] = []
                    header_data: Dict = {}

                    image_files = sorted(tmp_path.glob("*.jpg")) + sorted(tmp_path.glob("*.jpeg")) + sorted(tmp_path.glob("*.png"))

                    for i, img_path in enumerate(image_files):
                        status.text(f"Processing image {i+1}/{len(image_files)}: {img_path.name}")

                        if i == 0:
                            header_data = parser.extract_header_from_image(img_path)

                        items = parser.extract_items_from_image(img_path)
                        all_items.extend(items)
                        progress.progress((i + 1) / len(image_files))

                        if i < len(image_files) - 1:
                            time.sleep(0.5)  # Rate limiting

                    # Merge duplicates
                    merged = parser._merge_items(all_items)

                    status.text("✅ Extraction complete!")
                    progress.progress(1.0)

                    # ── Store in session state ────────────────────────────────
                    st.session_state["extracted_items"] = merged
                    st.session_state["header_data"] = header_data
                    st.session_state["ocr_method"] = "gemini_vision"

                except Exception as e:
                    st.error(f"❌ Extraction failed: {e}")
                    return

    # ── Show results if available ─────────────────────────────────────────────
    if "extracted_items" in st.session_state and st.session_state.get("ocr_method") == "gemini_vision":
        items = st.session_state["extracted_items"]
        header = st.session_state.get("header_data", {})

        st.markdown("---")
        st.success(f"✅ **{len(items)} items extracted** from work order images")

        # Header info
        if header:
            with st.expander("📋 Work Order Header (click to expand)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Work Order No:**", header.get("work_order_no", "—"))
                    st.write("**Contractor:**", header.get("contractor_name", "—"))
                    st.write("**Work Name:**", header.get("work_name", "—"))
                with col2:
                    st.write("**Agreement No:**", header.get("agreement_no", "—"))
                    st.write("**Amount:**", header.get("work_order_amount", "—"))
                    st.write("**Date:**", header.get("date", "—"))

        # Items table
        st.markdown("#### 📊 Extracted Items (editable)")
        st.info("💡 You can edit any field directly in the table below before generating the bill.")

        import pandas as pd
        df = pd.DataFrame(items)[["code", "description", "unit", "quantity", "rate", "confidence"]]
        df.columns = ["BSR Code", "Description", "Unit", "Qty", "Rate (Rs.)", "Confidence"]

        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "BSR Code": st.column_config.TextColumn("BSR Code", width=80),
                "Description": st.column_config.TextColumn("Description", width=300),
                "Unit": st.column_config.TextColumn("Unit", width=80),
                "Qty": st.column_config.NumberColumn("Qty", format="%.2f"),
                "Rate (Rs.)": st.column_config.NumberColumn("Rate (Rs.)", format="₹%.2f"),
                "Confidence": st.column_config.SelectboxColumn(
                    "Confidence", options=["high", "medium", "low", "database"]
                ),
            },
        )

        # Save edited data back to session
        if st.button("💾 Confirm & Proceed to Quantity Entry"):
            updated_items = edited_df.to_dict("records")
            st.session_state["work_order_items"] = [
                {
                    "code": r["BSR Code"],
                    "description": r["Description"],
                    "unit": r["Unit"],
                    "quantity": r["Qty"],
                    "rate": r["Rate (Rs.)"],
                    "confidence": r["Confidence"],
                }
                for r in updated_items
            ]
            st.success("✅ Work order data saved! Proceed to the 'Enter Quantities' tab.")
            st.balloons()


# ── Render confidence badge ────────────────────────────────────────────────────
def confidence_badge(conf: str) -> str:
    colors = {"high": "🟢", "medium": "🟡", "low": "🔴", "database": "🔵"}
    return colors.get(conf, "⚪")
