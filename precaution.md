# System Precautions & Setup

To get started with the updated Bill Generator system, please follow these essential steps:

## 1. Environment Configuration
- **Action**: Copy [`.env.example`](file:///e:/Rajkumar/BillGeneratorContractor/.env.example) to a new file named `.env`.
- **Details**: Add your real Google Gemini API keys and generate a secure `SECRET_KEY` (64-character random hex string recommended).
- **Warning**: Never commit your `.env` file to version control.

## 2. Background Worker Operation
- **Action**: Ensure the ARQ worker is running.
- **Run Command**: 
  ```powershell
  cd backend
  arq worker.WorkerSettings
  ```
- **Details**: This worker is required to handle all asynchronous bill generation tasks.

## 3. OCR Verification
- **Action**: Test the scanned document extraction.
- **Details**: Scanned document extraction now uses the standardized schema, making it much more reliable and consistent with the rest of the application.

---
Let me know if there's anything else you'd like to work on!
