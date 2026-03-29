"""Quick pipeline test — upload → generate → poll → verify."""
import time
import requests

BASE = "http://localhost:8000"
EXCEL = r"F:\New-Folder\BillGeneratorHistorical\test_input_files\SAMPLE BILL INPUT- NO EXTRA ITEMS.xlsx"

# 1. Upload
with open(EXCEL, "rb") as f:
    r = requests.post(f"{BASE}/bills/upload", files={"file": f})
assert r.status_code == 200, f"Upload failed: {r.text}"
upload = r.json()
print(f"Upload OK  total={upload['totalAmount']}  items={len(upload['billItems'])}")

# 2. Generate
gen_req = {
    "fileId": upload["fileId"],
    "titleData": upload["titleData"],
    "billItems": upload["billItems"],
    "extraItems": upload["extraItems"],
    "options": {
        "generatePdf": False,
        "generateHtml": True,
        "templateVersion": "v1",
        "premiumPercent": 22.22,
        "premiumType": "above",
        "previousBillAmount": 0.0,
    },
}
r2 = requests.post(f"{BASE}/bills/generate", json=gen_req)
assert r2.status_code == 200, f"Generate failed: {r2.text}"
job = r2.json()
job_id = job["jobId"]
print(f"Generate OK  jobId={job_id}")

# 3. Poll
for attempt in range(12):
    time.sleep(2)
    r3 = requests.get(f"{BASE}/bills/jobs/{job_id}")
    status = r3.json()
    print(f"  [{attempt+1}] status={status['status']}  progress={status['progress']}  {status['message']}")
    if status["status"] in ("complete", "error"):
        break

# 4. Results
print(f"\nFinal status: {status['status']}")
if status.get("error"):
    print(f"ERROR: {status['error']}")
else:
    print(f"Documents ({len(status['documents'])}):")
    for d in status["documents"]:
        print(f"  {d['name']:40s} {d['format']:5s} {d['size']:>8} bytes")
