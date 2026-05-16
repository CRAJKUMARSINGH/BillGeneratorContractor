# 📋 SaaS Bill Platform: User Manual & Deploy Guide

Welcome to the **Vanguard NASA-Level SaaS Bill Generation Platform (2026-2027)**. This system is designed for high-precision civil engineering bill processing, OCR extraction, and statutory compliance.

---

## 🚀 Quick Start (Local Deployment)

### 1. Prerequisites
- **Docker & Docker Compose** (Recommended)
- Python 3.12+
- Node.js 20+
- Tesseract OCR (Optional, for better OCR reliability)

### 2. Launch via Docker
```bash
docker-compose up --build
```
The app will be available at `http://localhost:5173`.

### 3. Manual Startup
**Backend**:
```bash
cd backend
pip install -r requirements.txt
python app.py
```
**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

---

## 🛠️ How to Use

### 1. Upload & Extract
- Drag and drop your **Measurement Book (MB)** or **Quantity Slip** images/PDFs into the dashboard.
- The **NASA-Level OCR Engine** will extract Bill Items (S.No, Description, Rate, Quantity).

### 2. Edit & Review
- Correct any anomalies in the **Interactive Spreadsheet**.
- The system highlights **Part-Rates** and **Anomaly Warnings** automatically.

### 3. Generate & Finalize
- Hit **Generate Bill**.
- The system orchestrates calculations (statutory rounding half-up) and renders 5+ documents:
  - **First Page (CB/MB)**
  - **Deviation Statement**
  - **Note Sheet**
  - **Extra Items (if detected)**
  - **Certificate II & III**

---

## 🛡️ Structural Integrity (Grok Audit)
- **Data Hashing**: Every bill is cryptographically signed.
- **Service Layer**: Business logic is decoupled from API for 100% stability.
- **Math Parity**: 1:1 parity with Government PWD rules.

---

## 👨‍💻 Maintenance
- **Logs**: Located in `backend/logs/`.
- **Database**: SQLite (default), PostgreSQL (production-ready).
- **Cleanup**: To purge temporary outputs, run `make clean`.

© 2026 Vanguard AI Corp. | NASA-Level Precision 🌑🚀
