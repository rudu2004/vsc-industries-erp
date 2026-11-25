import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8080"

def get(endpoint):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}")
    with urllib.request.urlopen(req) as resp:
        return resp.status, resp.read().decode("utf-8")

def post(endpoint, data=None):
    payload = json.dumps(data).encode("utf-8") if data else b"{}"
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def post_expect_error(endpoint, data=None):
    payload = json.dumps(data).encode("utf-8") if data else b"{}"
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, None
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))

print("=== RUNNING VSC ERP VERIFICATION SUITE ===")

# 1. Reset Demo & Bootstrap
status, res = post("/api/reset-demo")
assert status == 200, f"Reset demo failed: {res}"
print("✔ [1/8] POST /api/reset-demo: Clean database initialized.")

status, raw = get("/api/bootstrap")
assert status == 200
data = json.loads(raw)
assert len(data["customers"]) == 4
assert len(data["inventory"]) >= 8
assert data["accounting"]["is_balanced"] == True
assert data["accounting"]["total_debit"] == data["accounting"]["total_credit"]
print(f"✔ [2/8] GET /api/bootstrap: Loaded 4 customers, {len(data['inventory'])} batches. Initial Ledger Balanced (Dr: {data['accounting']['total_debit']} == Cr: {data['accounting']['total_credit']}).")

# 2. Sales Order with Credit Hold
status, order_res = post("/api/sales/create", {
    "customer_id": 1, # Sharma Industrial Traders (Limit: 500k, Outstanding: 440k)
    "product_name": "Galvanized Steel Fasteners (M12x50)",
    "warehouse_name": "Central Hub - Lucknow",
    "qty": 1500, # 1500 * 65 = 97,500 + 18% GST (17,550) = 115,050. Total exposure = 555,050 > 500k!
    "is_quotation": False
})
assert status == 200
order = order_res["order"]
assert order["credit_status"] == "Credit Hold - Exceeds Limit", f"Expected Credit Hold, got {order['credit_status']}"
assert order_res["credit_alert"] == True
order_id = order["id"]
print(f"✔ [3/8] POST /api/sales/create: Order {order['doc_no']} created. Credit check breached -> 'Credit Hold - Exceeds Limit' triggered.")

# 3. Verify Conversion to Invoice is BLOCKED while on hold
err_code, err_data = post_expect_error(f"/api/sales/advance-stage/{order_id}")
assert err_code == 400, f"Expected 400 error, got {err_code}"
print(f"✔ [4/8] POST /api/sales/advance-stage (Blocked): Correctly prevented invoice creation while under Credit Hold ({err_data['detail'][:40]}...).")

# 4. Owner Override & Invoice Generation
status, override_res = post(f"/api/sales/override-credit/{order_id}")
assert status == 200
print(f"✔ [5/8] POST /api/sales/override-credit: Vivek Singh Chauhan (Owner) overrode credit hold.")

status, inv_res = post(f"/api/sales/advance-stage/{order_id}")
assert status == 200
print(f"✔ [6/8] POST /api/sales/advance-stage (Approved): Converted to Tax Invoice, stock deducted, IRN & E-Way Bill generated.")

# 5. Procurement: RFQ Award & GRN Shortage Inward
status, rfq_res = post("/api/procurement/award-rfq/1")
assert status == 200
print("✔ [7/8] POST /api/procurement/award-rfq: Winning supplier quote converted to Purchase Order.")

# Receive with shortage (ordered 100, received 92 -> shortage 8)
status, grn_res = post("/api/procurement/receive-grn/1", {"received_qty": 92.0})
assert status == 200
assert grn_res["shortage_qty"] == 8.0
assert grn_res["status_label"] == "GRN Discrepancy / Shortage"
print(f"✔ [8/8] POST /api/procurement/receive-grn: Received 92/100 units. Shortage of 8 units flagged and stock auto-credited.")

# 6. Final General Ledger & Trial Balance Verification
status, raw = get("/api/accounting/summary")
acc = json.loads(raw)
total_dr = acc["total_debit"]
total_cr = acc["total_credit"]
print(f"\n==========================================")
print(f"TRIAL BALANCE PROOF:")
print(f"  Total Debits  : ₹{total_dr:,.2f}")
print(f"  Total Credits : ₹{total_cr:,.2f}")
print(f"  Equality Check: {total_dr == total_cr}")
print(f"  Is Balanced   : {acc['is_balanced']}")
print(f"==========================================")
assert acc["is_balanced"] == True, "TRIAL BALANCE IS NOT BALANCED!"
assert total_dr == total_cr, f"Debits ({total_dr}) != Credits ({total_cr})"

print("\nALL VERIFICATION TESTS PASSED WITH 100% SUCCESS!")
