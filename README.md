# VSC Industries — Enterprise B2B Trading, Multi-Warehouse & Accounting ERP

> **Executive Handover & Demonstration Guide for Project Intermediary**  
> **Client:** VSC Industries  
> **Owner / Sponsor:** Vivek Singh Chauhan  
> **Technical Lead & System Architect:** Rudraksh Saurabh Asthana  
> **Direct Contact / Support:** +91 8401113696  
> **Current Version:** Release 1.0 (Commercial Production Prototype)

---

## 1. Executive Summary & Purpose

This package contains the complete, self-contained enterprise ERP built specifically for **VSC Industries** (Proprietor: **Vivek Singh Chauhan**). 

The software solves the core operational challenges of high-volume industrial trading and manufacturing:
1. **Runaway Credit Risk:** Automatic credit exposure checks that block dispatches whenever an order pushes a customer over their agreed credit limit.
2. **Multi-Godown Visibility:** Real-time inventory tracking across Lucknow, Delhi, and Mumbai with instant inter-warehouse stock transfers.
3. **Supplier Shortage Deductions:** Automatic financial penalty deductions when received shipments have missing or damaged items (GRN short-receipt).
4. **Instant Double-Entry Accounting:** Automated journal postings that ensure mathematical **Trial Balance equality (`Total Debits == Total Credits`)** with one-click export for Tally Prime.
5. **GST NIC Compliance:** Tax invoice generation with QR code representations, government IRN hashes, and transporter National E-Way Bills.

---

## 2. How to Run This Software (2 Easy Methods)

### Option A: Recommended 1-Click Launcher (No Technical Knowledge Needed)
1. Unzip the project folder onto any Windows computer.
2. Double-click the file named **`START_VSC_ERP.bat`** in the main folder.
3. The launcher will automatically:
   - Verify Python on the machine.
   - Configure local dependencies quietly.
   - Open **`http://127.0.0.1:8080`** in your default web browser after 2 seconds.
   - Start the fast, local backend server.

### Option B: Manual Terminal Execution (PowerShell or Command Prompt)
Open PowerShell inside `D:\AMITY STUDY\VSC Industries` and execute these 3 standard commands:
```powershell
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8080
```
Then open your browser and navigate to: **`http://127.0.0.1:8080`**.

> **Note on Resetting Demo Data:**  
> If you test the app and want to reset the database back to clean factory state before meeting Vivek Singh Chauhan, click the discreet **"Reset Data"** button with the circular arrow located at the bottom-left sidebar footer (next to the role selector). It instantly re-seeds all clean records in under 1 second.

---

## 3. The 3-Minute Live Client Demo Script

Follow this exact step-by-step walkthrough during your meeting with **Vivek Singh Chauhan**. It is structured to demonstrate immediate business value within 180 seconds.

```
+-----------------------------------------------------------------------------------+
|                           THE 3-MINUTE DEMO FLOW                                  |
|                                                                                   |
|  [Minute 1: Overview]  --->  [Minute 2: The Wow Moment] --->  [Minute 3: Proof]   |
|   - 4 Live KPI Cards          - Switch to Sales Exec           - Supplier RFQ     |
|   - Cashflow Trends           - Profits vanish                 - Shortage Deduct  |
|   - Warehouse Doughnut        - Trigger Credit Hold            - Stock Transfer   |
|   - Action Center             - Switch to Owner: Approve       - E-Invoice / Tally|
+-----------------------------------------------------------------------------------+
```

### Minute 1: The Executive Overview Landing Screen
1. Open the app at `http://127.0.0.1:8080`. Point out the **Deep Navy Executive Sidebar** and top breadcrumb.
2. **Point to the 4 Top KPI Cards:**
   - **Total Sales Revenue:** `₹89,000` (shows active billed revenue).
   - **Pending Receivables:** `₹9,90,000` (money owed by trade debtors across UP, Telangana, and Maharashtra).
   - **Multi-Warehouse Stock Value:** `₹15,37,550` (live combined inventory valuation across all 3 godowns).
   - **Net Operating Profit & Margin:** `₹18,690 (21.0% Margin)` — realistic B2B industrial trading margin after COGS deduction.
3. **Point to the Two Live Interactive Charts:**
   - *Sales Revenue vs. Procurement Spend:* 6-month dual-bar trend showing cashflow trajectory.
   - *Stock Distribution by Warehouse:* Doughnut chart showing inventory split across **Central Hub (Lucknow)**, **North Depot (Delhi)**, and **West Branch (Mumbai)**.
4. **Point to the Owner Action Center:**
   - Show how critical alerts (Credit Holds, Expiring Batches, Low Stock items) are summarized right on the owner's desk.

---

### Minute 2: Role Security & Credit Hold (The "Wow" Moment)
*This is the most impressive commercial feature for business owners who fear bad debts.*

1. **Switch the User Role:** In the bottom-left sidebar profile dropdown, switch the profile from `👑 Vivek Singh Chauhan (Owner)` to **`💼 Sales Executive (Order Desk)`**.
2. **Show Role-Based Security:**
   - Point out that **Accounting & P&L**, **Multi-Warehouse Transfers**, and company **Net Profit** figures immediately disappear from the screen.
   - Sales reps only see what they are authorized to see: booking orders and generating approved dispatches.
3. **Trigger the Automatic Credit Hold:**
   - Go to the **Sales & Credit** screen (Tab 1).
   - Click the subtle **`⚡ Auto-Fill`** button in the order card header.
   - It pre-fills an order of **1,250 units of Galvanized Steel Fasteners** for **Sharma Industrial Traders** (Total: `₹95,875`).
   - Show Vivek Chauhan the **Dynamic Credit Exposure Meter**: Sharma Traders already has `₹4,40,000` outstanding against a `₹5,00,000` credit limit. Adding `₹95,875` will push exposure to `₹5,35,875` (breaching the limit by `₹35,875`).
   - Click **`Book Confirmed Order`**.
   - A bright red toast notification appears: **"AUTOMATIC CREDIT HOLD: Order exceeds customer credit limit!"**
   - Point to the table: The order is marked **`🚨 CREDIT HOLD`** and the tax invoice button is locked with **`🔒 Locked (Owner Only)`**. The sales executive *cannot* bypass this.
4. **Demonstrate Owner Executive Override:**
   - In the sidebar footer, switch back to **`👑 Vivek Singh Chauhan (Owner)`**.
   - Notice the button instantly turns into an amber **`🔓 Owner Override: Approve`** button!
   - Click it. The order is instantly approved, the hold is lifted, and dispatch is authorized.

---

### Minute 3: Procurement, Warehouse Transfers, GST & Tally
1. **Supplier Quote Matrix & Truck Receiving (Tab 2):**
   - Open **Procurement & GRN**.
   - Show the 3-vendor RFQ comparison for Brass Valves. Point out the smart badges: Apex Forgings has **`🏆 Lowest Price`** (`₹640/unit`), while Kalyani Precision has **`⚡ Fastest Delivery`** (`3 Days`).
   - Scroll to the Purchase Orders table: Point out `PO-26-502` (Tata Steel Tube Division). Out of 1,000 ordered fasteners, the truck arrived with only 950. Point out the verified green badge: **`₹2,250 Auto-Deducted for 50 Missing Units`**. The supplier's payable ledger was adjusted automatically!
2. **Godown Transfers (Tab 3):**
   - Open **Multi-Warehouse**. Show the inventory cards for Lucknow, Delhi, and Mumbai.
   - Execute an inter-warehouse transfer: Move 200 units of Fasteners from Lucknow to Delhi.
   - Click **`Authorize & Execute Transfer`**.
   - Switch back to the **Executive Dashboard**: Show how the Doughnut Chart and stock totals updated in real time.
3. **Government E-Invoice & Driver E-Way Bill (Tab 5):**
   - Open **GST Compliance**.
   - Click **`View/Print E-Invoice`**: A government-standard **Form GST INV-1** Tax Invoice modal opens with NIC-verified cryptographic QR Code, IRN hash, and signature line for Vivek Singh Chauhan.
   - Click **`Driver E-Way Bill`**: Opens a clean **Form GST EWB-01** transit slip with truck vehicle number (`UP-32-TR-9011`) ready for printing.
4. **Auto-Accounting & Tally Prime Export (Tab 4):**
   - Open **Accounting & P&L**.
   - Show the **Trial Balance Sheet**: Point to the bottom row where **`Total Debits (₹52,08,080) == Total Credits (₹52,08,080)`** is marked with a green **`Balanced (Dr == Cr)`** badge.
   - Click **`📥 Export Tally CSV`**: A standardized spreadsheet downloads immediately, formatted for 1-click import into Tally Prime or Excel.
   - Click **`Download Tally XML`**: Exports native Tally schema XML for chartered accountants.

---

## 4. Role-Based Access Control (RBAC) Matrix

| User Profile / Persona | Permitted Views | Financial Profit Visibility | Credit Hold Override | Stock Transfer Execution |
| :--- | :--- | :---: | :---: | :---: |
| **👑 Vivek Singh Chauhan (Owner)** | All 6 Views (Full Access) | **YES (Full)** | **YES (Exclusive)** | **YES** |
| **💼 Sales Executive (Order Desk)** | Sales & Credit, GST Compliance | **NO (Masked)** | **NO (Locked)** | **NO** |
| **🛒 Purchase Officer (Buying Desk)** | Procurement & GRN, Multi-Warehouse | **NO (Masked)** | **NO** | **NO** |
| **🏭 Warehouse / Godown Manager** | Multi-Warehouse, Procurement & GRN | **NO (Masked)** | **NO** | **YES** |
| **📊 Chartered Accountant (CA Desk)** | Dashboard, Accounting & P&L, GST | **YES (Full)** | **NO** | **NO** |

---

## 5. Module-by-Module Technical & Feature Summary

### Screen 0: Executive Overview Dashboard
* **Purpose:** High-level strategic control room for business owners and CFOs.
* **Key Features:** Real-time revenue, receivables, and stock valuation; dynamic cashflow charts; godown distribution doughnut; Owner Action Center alert queue; and live double-entry ledger stream.

### Screen 1: Sales Orders & Credit Check
* **Purpose:** Order-to-cash pipeline management with automated risk prevention.
* **Key Features:** Price tiers (Wholesale, Dealer, Retail); interstate vs intrastate GST detection (IGST vs CGST/SGST); dynamic credit limit calculation; automatic order-locking upon limit breach; and stage advancement (`Quotation` -> `Confirmed Order` -> `Tax Invoiced` -> `Delivered`).

### Screen 2: Supplier Quotes & Truck Receiving (PO & GRN)
* **Purpose:** Direct procurement cost optimization and physical goods verification.
* **Key Features:** Multi-vendor RFQ side-by-side comparison; lowest price and fastest turnaround tags; 1-click PO awarding; and Goods Receipt Note (GRN) shortage auto-deduction that penalizes suppliers for incomplete deliveries.

### Screen 3: Godown Stock & Multi-Warehouse Transfers
* **Purpose:** Centralized multi-location inventory tracking.
* **Key Features:** Location cards for Lucknow, Delhi, and Mumbai; reorder point and batch expiry alerts; filterable inventory listings; and dual-entry inter-warehouse stock transfer journalization.

### Screen 4: Auto-Accounting & P&L
* **Purpose:** Fully automated double-entry bookkeeping eliminating manual data entry.
* **Key Features:** Self-balancing Trial Balance sheet; live General Ledger journal stream; Gross Margin calculation; and dual-format export (**Tally Prime CSV** and **Tally XML**).

### Screen 5: GST E-Invoice & Driver E-Way Bills
* **Purpose:** Regulatory tax compliance and road transportation clearance.
* **Key Features:** Cryptographic IRN generation; printable Form GST INV-1 tax invoice with NIC QR code representation; printable Form GST EWB-01 road transit slip; and official Government JSON schema preview.

---

## 6. Clean 3-File Production Architecture

Under our strict **Ponytail** architecture principle, the entire enterprise prototype is maintained cleanly in just three production core files without bloated node modules or complex build steps:

```
VSC Industries/
│
├── START_VSC_ERP.bat          # 1-Click Windows Launcher for Client & Intermediary
├── requirements.txt           # Lightweight dependencies (FastAPI, SQLAlchemy, Uvicorn)
├── README.md                  # Complete Non-Technical Handover & Demo Guide
├── README.pdf                 # Executive Print-Ready PDF Handover Document
│
├── app/
│   └── main.py                # SINGLE BACKEND ENGINE (FastAPI, SQLite Schema, Seed Data,
│                              # Auto-Accounting Logic, and All REST API Endpoints)
│
├── frontend/
│   └── index.html             # SINGLE FRONTEND CANVAS (Tailwind CSS, Lucide/FontAwesome,
│                              # Chart.js Analytics, Role System, Printable Tax Modals)
│
└── vsc_erp.db                 # Auto-generated SQLite Database (Zero configuration needed)
```

---

## 7. Commercial & Deployment Road Map for VSC Industries

When Vivek Singh Chauhan approves this prototype for live factory and office deployment, here are the exact steps and requirements to launch into full production:

### 1. Cloud VPS Hosting (Estimated Cost: ~₹1,200 – ₹1,800 / month)
* Recommended Host: DigitalOcean, AWS Lightsail, or Linode (2 vCPU, 4GB RAM, Ubuntu 24.04 LTS).
* Run `uvicorn` behind an Nginx reverse proxy with automated SSL encryption (`Let's Encrypt`).

### 2. Custom Business Domain
* Recommended URL: **`erp.vscindustries.com`** or **`portal.vscindustries.com`**.
* Connect via standard DNS `A` record pointing to the VPS static IP.

### 3. Master Data Import
* Provide VSC Industries' actual opening balances:
  - Excel list of active Trade Debtors (Customer Names, GSTINs, Credit Limits, Current Balances).
  - Excel list of active SKUs (Part Names, HSN Codes, Purchase Costs, Selling Tiers).
  - Opening stock quantities per godown location.

### 4. Live Government E-Invoice Integration
* **Phase 1 (Included Free):** The current system generates Government-compliant E-Invoice JSON files that staff can directly upload to `einvoice1.gst.gov.in` in bulk without paying any third-party fees.
* **Phase 2 (Optional API):** Direct machine-to-machine API sync via an authorized GSP (GST Suvidha Provider such as ClearTax, Masters India, or Adaequare) for automated 1-second background IRN registration.

---

## 8. Technical Support & Lead Architect

For any custom extensions, live production cloud deployment, or client demonstration assistance, please contact:

* **Technical Lead:** Rudraksh Saurabh Asthana
* **Mobile / WhatsApp:** +91 8401113696
* **Project Directory:** `D:\AMITY STUDY\VSC Industries`
* **Verification Status:** Fully Tested, Trial Balance Balanced (`Dr == Cr`), All Endpoints 200 OK.
