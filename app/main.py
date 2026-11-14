import os
import time
import random
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    desc,
    func
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# -----------------------------------------------------------------------------
# DATABASE SETUP (SQLite)
# -----------------------------------------------------------------------------
DB_FILE = Path(__file__).resolve().parent.parent / "vsc_erp.db"
DATABASE_URL = f"sqlite:///{DB_FILE.as_posix()}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------------------------------------------------------
# SQLALCHEMY MODELS
# -----------------------------------------------------------------------------
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True)
    name = Column(String(200), nullable=False)
    gstin = Column(String(20), nullable=False)
    state = Column(String(100), nullable=False)
    price_tier = Column(String(50), default="Wholesale")  # Wholesale, Dealer, Retail
    credit_limit = Column(Float, default=500000.0)
    current_outstanding = Column(Float, default=0.0)


class SalesOrder(Base):
    __tablename__ = "sales_orders"

    id = Column(Integer, primary_key=True, index=True)
    doc_no = Column(String(50), unique=True, index=True)
    customer_id = Column(Integer, nullable=False)
    customer_name = Column(String(200), nullable=False)
    customer_gstin = Column(String(20), nullable=False)
    price_tier = Column(String(50), nullable=False)
    product_name = Column(String(200), nullable=False)
    hsn_code = Column(String(20), nullable=False)
    warehouse_name = Column(String(100), nullable=False)
    qty = Column(Float, default=1.0)
    unit_price = Column(Float, default=0.0)
    base_amount = Column(Float, default=0.0)
    tax_type = Column(String(50), default="CGST+SGST 18%")
    gst_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    stage = Column(String(50), default="Quotation")  # Quotation, Confirmed Order, Invoiced
    credit_status = Column(String(100), default="Approved")  # Approved, Credit Hold - Exceeds Limit, Owner Overridden
    delivery_status = Column(String(50), default="Order Placed")  # Order Placed, Packed, Dispatched, Delivered
    vehicle_no = Column(String(50), default="UP-32-TR-4421")
    irn_no = Column(String(100), default="")
    eway_bill_no = Column(String(100), default="")
    created_at = Column(String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))


class RFQComparison(Base):
    __tablename__ = "rfq_comparisons"

    id = Column(Integer, primary_key=True, index=True)
    rfq_no = Column(String(50), index=True)
    product_name = Column(String(200), nullable=False)
    qty_required = Column(Float, default=100.0)
    supplier_name = Column(String(200), nullable=False)
    supplier_gstin = Column(String(20), nullable=False)
    quoted_rate = Column(Float, default=0.0)
    lead_time_days = Column(Integer, default=7)
    payment_terms = Column(String(100), default="30 Days Credit")
    status = Column(String(50), default="Pending Comparison")  # Pending Comparison, Awarded PO


class PurchaseOrderGRN(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_no = Column(String(50), unique=True, index=True)
    supplier_name = Column(String(200), nullable=False)
    warehouse_name = Column(String(100), nullable=False)
    product_name = Column(String(200), nullable=False)
    ordered_qty = Column(Float, default=0.0)
    received_qty = Column(Float, default=0.0)
    shortage_qty = Column(Float, default=0.0)
    unit_rate = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    status = Column(String(100), default="PO Approved")  # PO Approved, GRN Discrepancy / Shortage, GRN Matched & Stocked
    created_at = Column(String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))


class InventoryBatch(Base):
    __tablename__ = "inventory_batches"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), index=True)
    product_name = Column(String(200), nullable=False)
    hsn_code = Column(String(20), nullable=False)
    warehouse_name = Column(String(100), nullable=False)
    batch_no = Column(String(50), nullable=False)
    expiry_date = Column(String(50), nullable=False)
    qty_on_hand = Column(Float, default=0.0)
    reorder_level = Column(Float, default=100.0)
    unit_cost = Column(Float, default=0.0)
    wholesale_price = Column(Float, default=0.0)
    dealer_price = Column(Float, default=0.0)
    retail_price = Column(Float, default=0.0)


class StockTransfer(Base):
    __tablename__ = "stock_transfers"

    id = Column(Integer, primary_key=True, index=True)
    transfer_no = Column(String(50), unique=True, index=True)
    product_name = Column(String(200), nullable=False)
    batch_no = Column(String(50), nullable=False)
    source_warehouse = Column(String(100), nullable=False)
    target_warehouse = Column(String(100), nullable=False)
    qty = Column(Float, default=0.0)
    transferred_at = Column(String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    status = Column(String(50), default="Completed")


class GeneralLedger(Base):
    __tablename__ = "general_ledger"

    id = Column(Integer, primary_key=True, index=True)
    voucher_no = Column(String(50), index=True)
    entry_date = Column(String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    reference_doc = Column(String(50), nullable=False)
    narration = Column(String(300), nullable=False)
    account_head = Column(String(100), nullable=False)
    account_type = Column(String(50), nullable=False)  # Asset, Liability, Revenue, Expense, Equity
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)


# -----------------------------------------------------------------------------
# PYDANTIC SCHEMAS
# -----------------------------------------------------------------------------
class SalesOrderCreate(BaseModel):
    customer_id: int
    product_name: str
    warehouse_name: str
    qty: float
    is_quotation: bool = False


class StockTransferCreate(BaseModel):
    sku: str
    batch_no: str
    source_warehouse: str
    target_warehouse: str
    qty: float


class ReceiveGRNRequest(BaseModel):
    received_qty: float


# -----------------------------------------------------------------------------
# FASTAPI APP DEFINITION
# -----------------------------------------------------------------------------
app = FastAPI(
    title="VSC Industries ERP",
    description="Enterprise B2B Trading, Multi-Warehouse & Auto-Accounting System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# DATABASE SEEDING LOGIC
# -----------------------------------------------------------------------------
def seed_database(db: Session):
    # Clear tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # 1. Seed Customers
    customers = [
        Customer(
            code="CUST-101",
            name="Sharma Industrial Traders",
            gstin="09AABCS1429B1Z1",
            state="Uttar Pradesh",
            price_tier="Wholesale",
            credit_limit=500000.0,
            current_outstanding=440000.0,  # Near 5L limit -> a 95k order triggers CREDIT HOLD
        ),
        Customer(
            code="CUST-102",
            name="Deccan Infra Supplies",
            gstin="36AABCD8821C1Z5",
            state="Telangana",
            price_tier="Dealer",
            credit_limit=800000.0,
            current_outstanding=210000.0,
        ),
        Customer(
            code="CUST-103",
            name="Metro Hardware Corp",
            gstin="27AABCM9910D1Z2",
            state="Maharashtra",
            price_tier="Wholesale",
            credit_limit=1000000.0,
            current_outstanding=150000.0,
        ),
        Customer(
            code="CUST-104",
            name="Awadh Retail Mart",
            gstin="09AABCA4412E1Z9",
            state="Uttar Pradesh",
            price_tier="Retail",
            credit_limit=200000.0,
            current_outstanding=190000.0,
        ),
    ]
    db.add_all(customers)
    db.commit()

    # 2. Seed Multi-Warehouse Inventory Batches
    batches = [
        InventoryBatch(
            sku="SKU-IND-01",
            product_name="Galvanized Steel Fasteners (M12x50)",
            hsn_code="73181500",
            warehouse_name="Central Hub - Lucknow",
            batch_no="LOT-2026-A1",
            expiry_date="2028-12-31",
            qty_on_hand=4200.0,
            reorder_level=1000.0,
            unit_cost=45.0,
            wholesale_price=65.0,
            dealer_price=72.0,
            retail_price=85.0,
        ),
        InventoryBatch(
            sku="SKU-IND-01",
            product_name="Galvanized Steel Fasteners (M12x50)",
            hsn_code="73181500",
            warehouse_name="North Depot - Delhi",
            batch_no="LOT-2026-A2",
            expiry_date="2028-12-31",
            qty_on_hand=1500.0,
            reorder_level=800.0,
            unit_cost=45.0,
            wholesale_price=65.0,
            dealer_price=72.0,
            retail_price=85.0,
        ),
        InventoryBatch(
            sku="SKU-IND-01",
            product_name="Galvanized Steel Fasteners (M12x50)",
            hsn_code="73181500",
            warehouse_name="West Branch - Mumbai",
            batch_no="LOT-2026-A3",
            expiry_date="2028-12-31",
            qty_on_hand=2800.0,
            reorder_level=1000.0,
            unit_cost=45.0,
            wholesale_price=65.0,
            dealer_price=72.0,
            retail_price=85.0,
        ),
        InventoryBatch(
            sku="SKU-IND-02",
            product_name="Industrial Epoxy Resin 5L Pack",
            hsn_code="39073010",
            warehouse_name="Central Hub - Lucknow",
            batch_no="LOT-2026-E1",
            expiry_date="2026-12-15",  # Expiring soon (< 45 days)
            qty_on_hand=180.0,
            reorder_level=250.0,  # Below reorder level!
            unit_cost=1250.0,
            wholesale_price=1650.0,
            dealer_price=1780.0,
            retail_price=1950.0,
        ),
        InventoryBatch(
            sku="SKU-IND-02",
            product_name="Industrial Epoxy Resin 5L Pack",
            hsn_code="39073010",
            warehouse_name="North Depot - Delhi",
            batch_no="LOT-2026-E2",
            expiry_date="2027-04-30",
            qty_on_hand=85.0,  # Critical low stock!
            reorder_level=150.0,
            unit_cost=1250.0,
            wholesale_price=1650.0,
            dealer_price=1780.0,
            retail_price=1950.0,
        ),
        InventoryBatch(
            sku="SKU-IND-03",
            product_name="Heavy Duty Brass Valves (2 Inch)",
            hsn_code="84818030",
            warehouse_name="Central Hub - Lucknow",
            batch_no="LOT-2026-V1",
            expiry_date="2030-01-01",
            qty_on_hand=620.0,
            reorder_level=200.0,
            unit_cost=680.0,
            wholesale_price=890.0,
            dealer_price=950.0,
            retail_price=1100.0,
        ),
        InventoryBatch(
            sku="SKU-IND-03",
            product_name="Heavy Duty Brass Valves (2 Inch)",
            hsn_code="84818030",
            warehouse_name="West Branch - Mumbai",
            batch_no="LOT-2026-V2",
            expiry_date="2030-01-01",
            qty_on_hand=340.0,
            reorder_level=150.0,
            unit_cost=680.0,
            wholesale_price=890.0,
            dealer_price=950.0,
            retail_price=1100.0,
        ),
        InventoryBatch(
            sku="SKU-IND-04",
            product_name="Armored Copper Cable (4 Core 16sqmm)",
            hsn_code="85444990",
            warehouse_name="North Depot - Delhi",
            batch_no="LOT-2026-C1",
            expiry_date="2032-12-31",
            qty_on_hand=450.0,
            reorder_level=200.0,
            unit_cost=380.0,
            wholesale_price=520.0,
            dealer_price=560.0,
            retail_price=640.0,
        ),
    ]
    db.add_all(batches)
    db.commit()

    # 3. Seed RFQ Comparison Matrix (3 competing suppliers for Brass Valves)
    rfqs = [
        RFQComparison(
            rfq_no="RFQ-26-01",
            product_name="Heavy Duty Brass Valves (2 Inch)",
            qty_required=200.0,
            supplier_name="Apex Forgings Pvt Ltd",
            supplier_gstin="06AABCA1234F1Z8",
            quoted_rate=640.0,
            lead_time_days=7,
            payment_terms="30 Days Credit",
            status="Pending Comparison",
        ),
        RFQComparison(
            rfq_no="RFQ-26-01",
            product_name="Heavy Duty Brass Valves (2 Inch)",
            qty_required=200.0,
            supplier_name="Kalyani Precision Valves",
            supplier_gstin="27AABCK5678G1Z2",
            quoted_rate=690.0,
            lead_time_days=3,  # Fastest delivery
            payment_terms="45 Days Credit",
            status="Pending Comparison",
        ),
        RFQComparison(
            rfq_no="RFQ-26-01",
            product_name="Heavy Duty Brass Valves (2 Inch)",
            qty_required=200.0,
            supplier_name="Bharat Metallic Works",
            supplier_gstin="09AABCB9012H1Z6",
            quoted_rate=710.0,
            lead_time_days=12,
            payment_terms="Advance",
            status="Pending Comparison",
        ),
    ]
    db.add_all(rfqs)
    db.commit()

    # 4. Seed Purchase Orders & GRNs
    pos = [
        PurchaseOrderGRN(
            po_no="PO-26-501",
            supplier_name="Apex Forgings Pvt Ltd",
            warehouse_name="Central Hub - Lucknow",
            product_name="Heavy Duty Brass Valves (2 Inch)",
            ordered_qty=100.0,
            received_qty=0.0,
            shortage_qty=0.0,
            unit_rate=640.0,
            total_amount=64000.0,
            status="PO Approved",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        ),
        PurchaseOrderGRN(
            po_no="PO-26-502",
            supplier_name="Tata Steel Tube Division",
            warehouse_name="Central Hub - Lucknow",
            product_name="Galvanized Steel Fasteners (M12x50)",
            ordered_qty=1000.0,
            received_qty=950.0,
            shortage_qty=50.0,
            unit_rate=45.0,
            total_amount=45000.0,
            status="GRN Discrepancy / Shortage",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        ),
    ]
    db.add_all(pos)
    db.commit()

    # 5. Seed Initial Sales Orders (Order-to-Cash Pipeline)
    orders = [
        SalesOrder(
            doc_no="SO-26-101",
            customer_id=1,
            customer_name="Sharma Industrial Traders",
            customer_gstin="09AABCS1429B1Z1",
            price_tier="Wholesale",
            product_name="Galvanized Steel Fasteners (M12x50)",
            hsn_code="73181500",
            warehouse_name="Central Hub - Lucknow",
            qty=1200.0,
            unit_price=65.0,
            base_amount=78000.0,
            tax_type="CGST+SGST 18%",
            gst_amount=14040.0,
            total_amount=92040.0,
            stage="Confirmed Order",
            credit_status="Credit Hold - Exceeds Limit",  # 440k + 92k = 532k > 500k limit!
            delivery_status="Order Placed",
            vehicle_no="UP-32-TR-9011",
            irn_no="",
            eway_bill_no="",
        ),
        SalesOrder(
            doc_no="INV-26-102",
            customer_id=2,
            customer_name="Deccan Infra Supplies",
            customer_gstin="36AABCD8821C1Z5",
            price_tier="Dealer",
            product_name="Industrial Epoxy Resin 5L Pack",
            hsn_code="39073010",
            warehouse_name="Central Hub - Lucknow",
            qty=50.0,
            unit_price=1780.0,
            base_amount=89000.0,
            tax_type="IGST 18%",
            gst_amount=16020.0,
            total_amount=105020.0,
            stage="Invoiced",
            credit_status="Approved",
            delivery_status="Dispatched",
            vehicle_no="UP-32-BT-8891",
            irn_no=hashlib.sha256(b"VSC-INV-26-102-20261114").hexdigest(),
            eway_bill_no="EWB-3910-8812",
        ),
        SalesOrder(
            doc_no="QT-26-103",
            customer_id=3,
            customer_name="Metro Hardware Corp",
            customer_gstin="27AABCM9910D1Z2",
            price_tier="Wholesale",
            product_name="Heavy Duty Brass Valves (2 Inch)",
            hsn_code="84818030",
            warehouse_name="West Branch - Mumbai",
            qty=150.0,
            unit_price=890.0,
            base_amount=133500.0,
            tax_type="CGST+SGST 18%",
            gst_amount=24030.0,
            total_amount=157530.0,
            stage="Quotation",
            credit_status="Approved",
            delivery_status="Order Placed",
            vehicle_no="MH-04-AZ-2219",
            irn_no="",
            eway_bill_no="",
        ),
    ]
    db.add_all(orders)
    db.commit()

    # 6. Seed General Ledger (Strict Double Entry: Total Debits == Total Credits)
    ledger_entries = [
        # Opening balances (Trial balance equality)
        GeneralLedger(
            voucher_no="JV-OPEN-01",
            entry_date=datetime.now().strftime("%Y-%m-%d 09:00"),
            reference_doc="OPENING-BAL",
            narration="Opening Stock Valuation across 3 Warehouses",
            account_head="Inventory Asset",
            account_type="Asset",
            debit=2500000.0,
            credit=0.0,
        ),
        GeneralLedger(
            voucher_no="JV-OPEN-02",
            entry_date=datetime.now().strftime("%Y-%m-%d 09:00"),
            reference_doc="OPENING-BAL",
            narration="Opening Bank & Liquid Cash Reserves - HDFC Bank",
            account_head="Bank / Cash Account",
            account_type="Asset",
            debit=1500000.0,
            credit=0.0,
        ),
        GeneralLedger(
            voucher_no="JV-OPEN-03",
            entry_date=datetime.now().strftime("%Y-%m-%d 09:00"),
            reference_doc="OPENING-BAL",
            narration="Trade Debtors Opening Balance (Total Customer Outstandings)",
            account_head="Accounts Receivable (Debtors)",
            account_type="Asset",
            debit=990000.0,  # 440k + 210k + 150k + 190k = 990,000!
            credit=0.0,
        ),
        GeneralLedger(
            voucher_no="JV-OPEN-04",
            entry_date=datetime.now().strftime("%Y-%m-%d 09:00"),
            reference_doc="OPENING-BAL",
            narration="Trade Creditors Opening Liabilities (Supplier Payables)",
            account_head="Accounts Payable (Creditors)",
            account_type="Liability",
            debit=0.0,
            credit=990000.0,
        ),
        GeneralLedger(
            voucher_no="JV-OPEN-05",
            entry_date=datetime.now().strftime("%Y-%m-%d 09:00"),
            reference_doc="OPENING-BAL",
            narration="Owner Equity / Capital - Vivek Singh Chauhan",
            account_head="Owner Capital / Equity",
            account_type="Equity",
            debit=0.0,
            credit=4000000.0,
        ),
        # Total Opening Dr = 25L + 15L + 9.9L = 49.9L. Total Opening Cr = 9.9L + 40L = 49.9L. (BALANCED!)

        # Journal Entry for Seeded Invoiced Order: INV-26-102 (Total 1,05,020)
        GeneralLedger(
            voucher_no="JV-INV-102-1",
            entry_date=datetime.now().strftime("%Y-%m-%d 11:30"),
            reference_doc="INV-26-102",
            narration="Invoice issued to Deccan Infra Supplies (Total Billed)",
            account_head="Accounts Receivable (Debtors)",
            account_type="Asset",
            debit=105020.0,
            credit=0.0,
        ),
        GeneralLedger(
            voucher_no="JV-INV-102-2",
            entry_date=datetime.now().strftime("%Y-%m-%d 11:30"),
            reference_doc="INV-26-102",
            narration="Taxable Sales Revenue recognized on INV-26-102",
            account_head="Sales Revenue",
            account_type="Revenue",
            debit=0.0,
            credit=89000.0,
        ),
        GeneralLedger(
            voucher_no="JV-INV-102-3",
            entry_date=datetime.now().strftime("%Y-%m-%d 11:30"),
            reference_doc="INV-26-102",
            narration="IGST 18% Output Liability collected on Interstate Sale",
            account_head="GST Output Tax Payable",
            account_type="Liability",
            debit=0.0,
            credit=16020.0,
        ),

        # Journal Entry for Seeded GRN: PO-26-502 (950 units received @ 45 = 42,750)
        GeneralLedger(
            voucher_no="JV-GRN-502-1",
            entry_date=datetime.now().strftime("%Y-%m-%d 12:45"),
            reference_doc="PO-26-502",
            narration="GRN Stock Inward for Fasteners (950 Units)",
            account_head="Inventory Asset",
            account_type="Asset",
            debit=42750.0,
            credit=0.0,
        ),
        GeneralLedger(
            voucher_no="JV-GRN-502-2",
            entry_date=datetime.now().strftime("%Y-%m-%d 12:45"),
            reference_doc="PO-26-502",
            narration="Liability to Tata Steel Tube Division for Received Goods",
            account_head="Accounts Payable (Creditors)",
            account_type="Liability",
            debit=0.0,
            credit=42750.0,
        ),
    ]
    db.add_all(ledger_entries)
    db.commit()


@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        # Check if database exists and has customers; if not, seed
        Base.metadata.create_all(bind=engine)
        if db.query(Customer).count() == 0:
            seed_database(db)
    finally:
        db.close()


# -----------------------------------------------------------------------------
# REST ENDPOINTS
# -----------------------------------------------------------------------------
@app.post("/api/reset-demo")
def reset_demo(db: Session = Depends(get_db)):
    """Drops, recreates, and re-seeds all clean demonstration data."""
    seed_database(db)
    return {"status": "success", "message": "Demo data refreshed successfully with balanced Trial Balance."}


@app.get("/api/bootstrap")
def get_bootstrap_data(db: Session = Depends(get_db)):
    """Returns the complete state required for the single-page ERP UI."""
    customers = db.query(Customer).all()
    inventory = db.query(InventoryBatch).all()
    orders = db.query(SalesOrder).order_by(desc(SalesOrder.id)).all()
    rfqs = db.query(RFQComparison).all()
    pos = db.query(PurchaseOrderGRN).order_by(desc(PurchaseOrderGRN.id)).all()
    transfers = db.query(StockTransfer).order_by(desc(StockTransfer.id)).all()

    # Accounting summary
    accounting = get_accounting_summary(db)

    # Compute KPI badges
    credit_holds_count = db.query(SalesOrder).filter(SalesOrder.credit_status == "Credit Hold - Exceeds Limit").count()
    low_stock_count = db.query(InventoryBatch).filter(InventoryBatch.qty_on_hand <= InventoryBatch.reorder_level).count()
    open_pos_count = db.query(PurchaseOrderGRN).filter(PurchaseOrderGRN.status.in_(["PO Approved", "GRN Discrepancy / Shortage"])).count()

    return {
        "company": {
            "name": "VSC Industries",
            "owner": "Vivek Singh Chauhan (Owner)",
            "prepared_by": "Rudraksh Saurabh Asthana (Technical Lead | +91 8401113696)",
            "gstin": "09AAECV1924K1Z3",
            "state": "Uttar Pradesh",
            "address": "Plot 42-B, Transport Nagar Industrial Area, Lucknow, UP - 226012",
        },
        "kpis": {
            "credit_holds": credit_holds_count,
            "low_stock_alerts": low_stock_count,
            "open_pos": open_pos_count,
            "is_ledger_balanced": accounting["is_balanced"],
            "total_revenue": accounting["pnl"]["total_revenue"],
        },
        "customers": customers,
        "inventory": inventory,
        "sales_orders": orders,
        "rfqs": rfqs,
        "purchase_orders": pos,
        "stock_transfers": transfers,
        "accounting": accounting,
    }


# --- SALES & CREDIT MANAGEMENT ---
@app.post("/api/sales/create")
def create_sales_order(payload: SalesOrderCreate, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    batch = db.query(InventoryBatch).filter(
        InventoryBatch.product_name == payload.product_name,
        InventoryBatch.warehouse_name == payload.warehouse_name
    ).first()

    if not batch:
        # Fallback to any batch of that product for pricing
        batch = db.query(InventoryBatch).filter(InventoryBatch.product_name == payload.product_name).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Product not found in inventory catalog")

    # Determine tiered price
    if customer.price_tier == "Wholesale":
        unit_price = batch.wholesale_price
    elif customer.price_tier == "Dealer":
        unit_price = batch.dealer_price
    else:
        unit_price = batch.retail_price

    base_amount = round(payload.qty * unit_price, 2)

    # GST determination: Same state (UP) = CGST+SGST, Interstate = IGST
    if customer.state.lower() in ["uttar pradesh", "up"]:
        tax_type = "CGST+SGST 18%"
    else:
        tax_type = "IGST 18%"

    gst_amount = round(base_amount * 0.18, 2)
    total_amount = round(base_amount + gst_amount, 2)

    # Credit Check logic: customer.current_outstanding + total_amount > customer.credit_limit
    exposure = customer.current_outstanding + total_amount
    if exposure > customer.credit_limit:
        credit_status = "Credit Hold - Exceeds Limit"
    else:
        credit_status = "Approved"

    count = db.query(SalesOrder).count() + 101
    prefix = "QT-26" if payload.is_quotation else "SO-26"
    doc_no = f"{prefix}-{count}"
    stage = "Quotation" if payload.is_quotation else "Confirmed Order"

    order = SalesOrder(
        doc_no=doc_no,
        customer_id=customer.id,
        customer_name=customer.name,
        customer_gstin=customer.gstin,
        price_tier=customer.price_tier,
        product_name=batch.product_name,
        hsn_code=batch.hsn_code,
        warehouse_name=payload.warehouse_name,
        qty=payload.qty,
        unit_price=unit_price,
        base_amount=base_amount,
        tax_type=tax_type,
        gst_amount=gst_amount,
        total_amount=total_amount,
        stage=stage,
        credit_status=credit_status,
        delivery_status="Order Placed",
        vehicle_no=f"UP-32-TR-{random.randint(1000, 9999)}",
        irn_no="",
        eway_bill_no="",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return {
        "status": "success",
        "order": order,
        "credit_alert": credit_status == "Credit Hold - Exceeds Limit",
        "exposure": exposure,
        "credit_limit": customer.credit_limit
    }


@app.post("/api/sales/override-credit/{order_id}")
def override_credit_hold(order_id: int, db: Session = Depends(get_db)):
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.credit_status = "Owner Overridden"
    db.commit()
    return {"status": "success", "message": f"Credit hold overridden by Vivek Singh Chauhan for {order.doc_no}."}


@app.post("/api/sales/advance-stage/{order_id}")
def advance_sales_stage(order_id: int, db: Session = Depends(get_db)):
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.stage == "Quotation":
        order.stage = "Confirmed Order"
        if order.doc_no.startswith("QT-"):
            order.doc_no = order.doc_no.replace("QT-", "SO-")
        db.commit()
        return {"status": "success", "message": f"{order.doc_no} converted to Confirmed Order."}

    elif order.stage == "Confirmed Order":
        # 1. Re-validate credit limit before invoicing
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        if order.credit_status != "Owner Overridden":
            if (customer.current_outstanding + order.total_amount) > customer.credit_limit:
                order.credit_status = "Credit Hold - Exceeds Limit"
                db.commit()
                raise HTTPException(
                    status_code=400,
                    detail=f"Conversion Blocked: Total exposure exceeds credit limit of ₹{customer.credit_limit:,.2f}. Vivek Singh Chauhan (Owner) must override first."
                )

        # 2. Check and deduct Stock from matching warehouse inventory
        batch = db.query(InventoryBatch).filter(
            InventoryBatch.product_name == order.product_name,
            InventoryBatch.warehouse_name == order.warehouse_name
        ).first()

        if not batch or batch.qty_on_hand < order.qty:
            avail = batch.qty_on_hand if batch else 0.0
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient inventory at {order.warehouse_name}. Requested: {order.qty}, Available: {avail}."
            )

        batch.qty_on_hand = round(batch.qty_on_hand - order.qty, 2)

        # 3. Add total_amount to customer's current outstanding
        customer.current_outstanding = round(customer.current_outstanding + order.total_amount, 2)

        # 3. Generate Tax Invoice numbers
        inv_no = f"INV-26-{100 + order.id}"
        order.doc_no = inv_no
        order.stage = "Invoiced"
        order.irn_no = hashlib.sha256(f"VSC-{inv_no}-{time.time()}".encode()).hexdigest()
        order.eway_bill_no = f"EWB-3910-{random.randint(1000, 9999)}"

        # 4. Automatically Post Double-Entry General Ledger (Dr == Cr)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        ledger_debit = GeneralLedger(
            voucher_no=f"JV-{inv_no}-DR",
            entry_date=now_str,
            reference_doc=inv_no,
            narration=f"Receivable booked for {order.customer_name} against {inv_no}",
            account_head="Accounts Receivable (Debtors)",
            account_type="Asset",
            debit=order.total_amount,
            credit=0.0,
        )
        ledger_rev = GeneralLedger(
            voucher_no=f"JV-{inv_no}-CR1",
            entry_date=now_str,
            reference_doc=inv_no,
            narration=f"Revenue recognized for {order.product_name} ({order.qty} units)",
            account_head="Sales Revenue",
            account_type="Revenue",
            debit=0.0,
            credit=order.base_amount,
        )
        ledger_tax = GeneralLedger(
            voucher_no=f"JV-{inv_no}-CR2",
            entry_date=now_str,
            reference_doc=inv_no,
            narration=f"{order.tax_type} output liability on {inv_no}",
            account_head="GST Output Tax Payable",
            account_type="Liability",
            debit=0.0,
            credit=order.gst_amount,
        )
        db.add_all([ledger_debit, ledger_rev, ledger_tax])
        db.commit()

        return {
            "status": "success",
            "message": f"Tax Invoice {inv_no} created! Stock deducted, E-Invoice IRN & E-Way Bill generated, and General Ledger posted automatically."
        }
    else:
        return {"status": "info", "message": "Order is already Invoiced."}


@app.post("/api/sales/advance-delivery/{order_id}")
def advance_delivery(order_id: int, db: Session = Depends(get_db)):
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.stage != "Invoiced":
        raise HTTPException(
            status_code=400,
            detail=f"Delivery Blocked: Order {order.doc_no} is currently at '{order.stage}' stage. Only Invoiced orders with approved credit can be dispatched."
        )

    stages = ["Order Placed", "Packed", "Dispatched", "Delivered"]
    current_idx = stages.index(order.delivery_status) if order.delivery_status in stages else 0
    if current_idx < len(stages) - 1:
        order.delivery_status = stages[current_idx + 1]
        db.commit()
        return {"status": "success", "new_delivery_status": order.delivery_status}
    return {"status": "info", "message": "Already at Delivered stage"}


# --- PROCUREMENT, RFQ & GRN ---
@app.post("/api/procurement/award-rfq/{rfq_id}")
def award_rfq(rfq_id: int, db: Session = Depends(get_db)):
    rfq = db.query(RFQComparison).filter(RFQComparison.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")

    rfq.status = "Awarded PO"
    total_amount = round(rfq.qty_required * rfq.quoted_rate, 2)
    po_count = db.query(PurchaseOrderGRN).count() + 501
    po_no = f"PO-26-{po_count}"

    po = PurchaseOrderGRN(
        po_no=po_no,
        supplier_name=rfq.supplier_name,
        warehouse_name="Central Hub - Lucknow",
        product_name=rfq.product_name,
        ordered_qty=rfq.qty_required,
        received_qty=0.0,
        shortage_qty=0.0,
        unit_rate=rfq.quoted_rate,
        total_amount=total_amount,
        status="PO Approved",
    )
    db.add(po)
    db.commit()
    return {"status": "success", "message": f"RFQ awarded! Purchase Order {po_no} created for {rfq.supplier_name}."}


@app.post("/api/procurement/receive-grn/{po_id}")
def receive_grn(po_id: int, payload: ReceiveGRNRequest, db: Session = Depends(get_db)):
    po = db.query(PurchaseOrderGRN).filter(PurchaseOrderGRN.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    po.received_qty = payload.received_qty
    shortage = max(0.0, round(po.ordered_qty - payload.received_qty, 2))
    po.shortage_qty = shortage

    if shortage > 0:
        po.status = "GRN Discrepancy / Shortage"
    else:
        po.status = "GRN Matched & Stocked"

    # 1. Update inventory batch with received qty
    batch = db.query(InventoryBatch).filter(
        InventoryBatch.product_name == po.product_name,
        InventoryBatch.warehouse_name == po.warehouse_name
    ).first()

    if batch:
        batch.qty_on_hand += payload.received_qty
    else:
        # Create new batch if none exists in that warehouse
        new_batch = InventoryBatch(
            sku="SKU-NEW-01",
            product_name=po.product_name,
            hsn_code="84818030",
            warehouse_name=po.warehouse_name,
            batch_no=f"LOT-{datetime.now().strftime('%Y%m%d')}",
            expiry_date="2029-12-31",
            qty_on_hand=payload.received_qty,
            reorder_level=50.0,
            unit_cost=po.unit_rate,
            wholesale_price=round(po.unit_rate * 1.3, 2),
            dealer_price=round(po.unit_rate * 1.4, 2),
            retail_price=round(po.unit_rate * 1.6, 2),
        )
        db.add(new_batch)

    # 2. Post to General Ledger for the actual received goods value (Dr == Cr)
    received_value = round(payload.received_qty * po.unit_rate, 2)
    if received_value > 0:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        gl_dr = GeneralLedger(
            voucher_no=f"JV-GRN-{po.id}-DR",
            entry_date=now_str,
            reference_doc=po.po_no,
            narration=f"Stock Inward asset value received from {po.supplier_name}",
            account_head="Inventory Asset",
            account_type="Asset",
            debit=received_value,
            credit=0.0,
        )
        gl_cr = GeneralLedger(
            voucher_no=f"JV-GRN-{po.id}-CR",
            entry_date=now_str,
            reference_doc=po.po_no,
            narration=f"Trade liability to {po.supplier_name} for received items",
            account_head="Accounts Payable (Creditors)",
            account_type="Liability",
            debit=0.0,
            credit=received_value,
        )
        db.add_all([gl_dr, gl_cr])

    db.commit()
    return {
        "status": "success",
        "po_no": po.po_no,
        "received_qty": po.received_qty,
        "shortage_qty": po.shortage_qty,
        "status_label": po.status,
        "message": f"GRN processed for {po.po_no}. Stock updated and Accounting Ledger posted."
    }


# --- INVENTORY & WAREHOUSE TRANSFER ---
@app.post("/api/inventory/transfer")
def transfer_stock(payload: StockTransferCreate, db: Session = Depends(get_db)):
    if payload.source_warehouse == payload.target_warehouse:
        raise HTTPException(status_code=400, detail="Source and Target warehouses cannot be identical")

    src_batch = db.query(InventoryBatch).filter(
        InventoryBatch.batch_no == payload.batch_no,
        InventoryBatch.warehouse_name == payload.source_warehouse
    ).first()

    if not src_batch:
        raise HTTPException(status_code=404, detail="Source batch not found in the selected warehouse")

    if src_batch.qty_on_hand < payload.qty:
        raise HTTPException(status_code=400, detail=f"Insufficient stock in source warehouse (Available: {src_batch.qty_on_hand})")

    # Deduct from source
    src_batch.qty_on_hand = round(src_batch.qty_on_hand - payload.qty, 2)

    # Add to target batch (or create one)
    tgt_batch = db.query(InventoryBatch).filter(
        InventoryBatch.batch_no == payload.batch_no,
        InventoryBatch.warehouse_name == payload.target_warehouse
    ).first()

    if tgt_batch:
        tgt_batch.qty_on_hand = round(tgt_batch.qty_on_hand + payload.qty, 2)
    else:
        tgt_batch = InventoryBatch(
            sku=src_batch.sku,
            product_name=src_batch.product_name,
            hsn_code=src_batch.hsn_code,
            warehouse_name=payload.target_warehouse,
            batch_no=src_batch.batch_no,
            expiry_date=src_batch.expiry_date,
            qty_on_hand=payload.qty,
            reorder_level=src_batch.reorder_level,
            unit_cost=src_batch.unit_cost,
            wholesale_price=src_batch.wholesale_price,
            dealer_price=src_batch.dealer_price,
            retail_price=src_batch.retail_price,
        )
        db.add(tgt_batch)

    count = db.query(StockTransfer).count() + 1
    trf = StockTransfer(
        transfer_no=f"TRF-26-{count:03d}",
        product_name=src_batch.product_name,
        batch_no=src_batch.batch_no,
        source_warehouse=payload.source_warehouse,
        target_warehouse=payload.target_warehouse,
        qty=payload.qty,
        status="Completed",
    )
    db.add(trf)
    db.commit()

    return {
        "status": "success",
        "transfer_no": trf.transfer_no,
        "message": f"Successfully transferred {payload.qty} units from {payload.source_warehouse} to {payload.target_warehouse}."
    }


# --- ACCOUNTING & GENERAL LEDGER ---
def get_accounting_summary(db: Session) -> Dict[str, Any]:
    entries = db.query(GeneralLedger).order_by(desc(GeneralLedger.id)).all()

    # Aggregate by account_head
    heads: Dict[str, Dict[str, Any]] = {}
    total_debit = 0.0
    total_credit = 0.0

    for e in entries:
        h = e.account_head
        if h not in heads:
            heads[h] = {
                "account_head": h,
                "account_type": e.account_type,
                "debit": 0.0,
                "credit": 0.0,
            }
        heads[h]["debit"] += e.debit
        heads[h]["credit"] += e.credit
        total_debit += e.debit
        total_credit += e.credit

    trial_balance = []
    for h, data in heads.items():
        dr = round(data["debit"], 2)
        cr = round(data["credit"], 2)
        net = round(dr - cr, 2)
        trial_balance.append({
            "account_head": h,
            "account_type": data["account_type"],
            "debit": dr,
            "credit": cr,
            "net_balance": net,
        })

    # Sort trial balance consistently
    type_order = {"Asset": 1, "Liability": 2, "Equity": 3, "Revenue": 4, "Expense": 5}
    trial_balance.sort(key=lambda x: (type_order.get(x["account_type"], 9), x["account_head"]))

    total_debit = round(total_debit, 2)
    total_credit = round(total_credit, 2)
    is_balanced = (total_debit == total_credit)

    # Calculate P&L metrics
    sales_rev = heads.get("Sales Revenue", {}).get("credit", 0.0)
    cogs = heads.get("Cost of Goods Sold", {}).get("debit", 0.0)
    gross_profit = round(sales_rev - cogs, 2)
    margin_pct = round((gross_profit / sales_rev * 100), 1) if sales_rev > 0 else 0.0

    return {
        "ledger_entries": entries,
        "trial_balance": trial_balance,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": is_balanced,
        "pnl": {
            "total_revenue": round(sales_rev, 2),
            "cogs": round(cogs, 2),
            "gross_profit": gross_profit,
            "net_margin_pct": margin_pct,
        }
    }


@app.get("/api/accounting/summary")
def accounting_summary_endpoint(db: Session = Depends(get_db)):
    return get_accounting_summary(db)


@app.get("/api/accounting/export-tally")
def export_tally_xml(db: Session = Depends(get_db)):
    """Exports General Ledger in clean Tally-compliant XML structure."""
    entries = db.query(GeneralLedger).order_by(GeneralLedger.id).all()
    xml_lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<ENVELOPE>',
        '  <HEADER>',
        '    <TALLYREQUEST>Import Data</TALLYREQUEST>',
        '  </HEADER>',
        '  <BODY>',
        '    <IMPORTDATA>',
        '      <REQUESTDESC>',
        '        <REPORTNAME>Vouchers</REPORTNAME>',
        '        <STATICVARIABLES>',
        '          <SVCURRENTCOMPANY>VSC Industries</SVCURRENTCOMPANY>',
        '        </STATICVARIABLES>',
        '      </REQUESTDESC>',
        '      <REQUESTDATA>'
    ]

    for e in entries:
        xml_lines.extend([
            f'        <TALLYMESSAGE xmlns:UDF="TallyUDF">',
            f'          <VOUCHER VCHTYPE="Journal" ACTION="Create">',
            f'            <DATE>{e.entry_date[:10].replace("-", "")}</DATE>',
            f'            <NARRATION>{e.narration} (Ref: {e.reference_doc})</NARRATION>',
            f'            <VOUCHERNUMBER>{e.voucher_no}</VOUCHERNUMBER>',
            f'            <ALLLEDGERENTRIES.LIST>',
            f'              <LEDGERNAME>{e.account_head}</LEDGERNAME>',
            f'              <ISDEEMEDPOSITIVE>{"Yes" if e.debit > 0 else "No"}</ISDEEMEDPOSITIVE>',
            f'              <AMOUNT>{-e.debit if e.debit > 0 else e.credit}</AMOUNT>',
            f'            </ALLLEDGERENTRIES.LIST>',
            f'          </VOUCHER>',
            f'        </TALLYMESSAGE>'
        ])

    xml_lines.extend([
        '      </REQUESTDATA>',
        '    </IMPORTDATA>',
        '  </BODY>',
        '</ENVELOPE>'
    ])

    return Response(
        content="\n".join(xml_lines),
        media_type="application/xml",
        headers={"Content-Disposition": 'attachment; filename="VSC_GeneralLedger_Tally.xml"'}
    )


# --- GST & E-INVOICE COMPLIANCE ---
@app.get("/api/gst/e-invoice-json/{order_id}")
def get_einvoice_json(order_id: int, db: Session = Depends(get_db)):
    order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Official NIC E-Invoice JSON Schema format
    nic_payload = {
        "Version": "1.1",
        "TranDtls": {
            "TaxSch": "GST",
            "SupTyp": "B2B",
            "RegRev": "N",
            "EcmGstin": None,
            "IgstOnIntra": "N"
        },
        "DocDtls": {
            "Typ": "INV",
            "No": order.doc_no,
            "Dt": order.created_at[:10]
        },
        "SellerDtls": {
            "Gstin": "09AAECV1924K1Z3",
            "LglNm": "VSC Industries",
            "TrdNm": "VSC Industries Trading Division",
            "Addr1": "Plot 42-B, Transport Nagar Industrial Area",
            "Loc": "Lucknow",
            "Pin": 226012,
            "Stcd": "09"
        },
        "BuyerDtls": {
            "Gstin": order.customer_gstin,
            "LglNm": order.customer_name,
            "TrdNm": order.customer_name,
            "Pos": order.customer_gstin[:2] if len(order.customer_gstin) >= 2 else "09",
            "Addr1": "Commercial Complex, Main Road",
            "Loc": "Industrial City",
            "Pin": 208001,
            "Stcd": order.customer_gstin[:2] if len(order.customer_gstin) >= 2 else "09"
        },
        "ItemList": [
            {
                "SlNo": "1",
                "PrdDesc": order.product_name,
                "IsServc": "N",
                "HsnCd": order.hsn_code,
                "Qty": order.qty,
                "Unit": "NOS",
                "UnitPrice": order.unit_price,
                "TotAmt": order.base_amount,
                "AssAmt": order.base_amount,
                "GstRt": 18.0,
                "IgstAmt": order.gst_amount if "IGST" in order.tax_type else 0.0,
                "CgstAmt": round(order.gst_amount / 2, 2) if "CGST" in order.tax_type else 0.0,
                "SgstAmt": round(order.gst_amount / 2, 2) if "SGST" in order.tax_type else 0.0,
                "TotItemVal": order.total_amount
            }
        ],
        "ValDtls": {
            "AssVal": order.base_amount,
            "CgstVal": round(order.gst_amount / 2, 2) if "CGST" in order.tax_type else 0.0,
            "SgstVal": round(order.gst_amount / 2, 2) if "SGST" in order.tax_type else 0.0,
            "IgstVal": order.gst_amount if "IGST" in order.tax_type else 0.0,
            "TotInvVal": order.total_amount
        },
        "GovtPortalVerification": {
            "Irn": order.irn_no or "PENDING-GENERATION",
            "AckNo": random.randint(112000000000, 112999999999),
            "AckDt": order.created_at,
            "EwayBillNo": order.eway_bill_no or "NOT-GENERATED",
            "VehicleNo": order.vehicle_no
        }
    }
    return JSONResponse(
        content=nic_payload,
        headers={"Content-Disposition": f'attachment; filename="NIC_EInvoice_{order.doc_no}.json"'}
    )


# --- FRONTEND ROOT SERVING ---
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

@app.get("/")
def serve_index():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        return JSONResponse({"status": "Frontend not found", "path": str(index_path)}, status_code=404)
    return FileResponse(index_path)


# Mount static assets if any
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
