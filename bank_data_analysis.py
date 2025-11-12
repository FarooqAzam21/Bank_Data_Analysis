import streamlit as st
import pandas as pd

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Accounting App", layout="wide")

# ---------- HEADER ----------
st.markdown(
    """
    <style>
    .main-title {
        font-size: 32px;
        font-weight: 700;
        text-align: center;
        color: #2E86C1;
    }
    .sub-header {
        font-size: 20px;
        font-weight: 600;
        margin-top: 14px;
        color: #117864;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<h1 class='main-title'>💼 Accounting App — Universal Bank CSV Version</h1>", unsafe_allow_html=True)
st.write("Upload your bank statement CSV — app will auto-detect columns and generate Profit & Loss + Tax Report.")
st.divider()

# ---------- FILE UPLOAD ----------
uploaded = st.file_uploader("📂 Upload your Bank Statement CSV file", type=["csv"])
if not uploaded:
    st.info("Please upload your bank statement file to start.")
    st.stop()

# Try to read CSV safely
try:
    df = pd.read_csv(uploaded)
except Exception:
    df = pd.read_csv(uploaded, encoding="latin1")

st.markdown("<h3 class='sub-header'>📋 Preview of Uploaded Data</h3>", unsafe_allow_html=True)
st.dataframe(df.head(10), use_container_width=True)
st.divider()

# ---------- COLUMN HANDLING ----------
df.columns = [c.strip() for c in df.columns]  # remove spaces

# Detect merchant name
if "merchant_name" not in df.columns:
    possible_names = ["Description", "Particulars", "Details", "Narration"]
    match = next((c for c in df.columns if c in possible_names), None)
    df["merchant_name"] = df[match] if match else df.iloc[:, 0].astype(str)

# Detect numeric columns (amount, balance, deposits, withdrawals)
df_numeric = df.copy()

for col in df.columns:
    df_numeric[col] = (
        df[col]
        .astype(str)
        .str.replace(",", "")
        .str.replace("CR", "", case=False)
        .str.replace("DR", "", case=False)
        .str.strip()
    )

# Try common bank fields
amount_col = None
credit_col = None
debit_col = None

for col in df.columns:
    col_lower = col.lower()
    if any(x in col_lower for x in ["amount", "balance", "credit", "deposit"]):
        credit_col = col
    if any(x in col_lower for x in ["debit", "withdrawal", "spent"]):
        debit_col = col

# Compute amount (credit - debit) logic
if credit_col and debit_col:
    df[credit_col] = pd.to_numeric(df_numeric[credit_col], errors="coerce").fillna(0)
    df[debit_col] = pd.to_numeric(df_numeric[debit_col], errors="coerce").fillna(0)
    df["amount"] = df[credit_col] - df[debit_col]
elif credit_col:
    df["amount"] = pd.to_numeric(df_numeric[credit_col], errors="coerce").fillna(0)
elif debit_col:
    df["amount"] = -pd.to_numeric(df_numeric[debit_col], errors="coerce").fillna(0)
else:
    st.error("❌ Could not detect amount/balance columns. Make sure your CSV has Balance, Amount, Deposit, or Withdrawal columns.")
    st.stop()

# Create direction (in/out)
if "direction" not in df.columns:
    if "Deposits" in df.columns or "Deposit" in df.columns:
        dep_col = "Deposits" if "Deposits" in df.columns else "Deposit"
        df["direction"] = df[dep_col].apply(lambda x: "in" if pd.notna(x) and float(str(x).replace(',', '').strip() or 0) > 0 else "out")
    elif "Withdrawals" in df.columns:
        df["direction"] = df["Withdrawals"].apply(lambda x: "out" if pd.notna(x) and float(str(x).replace(',', '').strip() or 0) > 0 else "in")
    else:
        df["direction"] = df["amount"].apply(lambda x: "in" if x > 0 else "out")

# ---------- CATEGORIZATION RULES ----------
rules = [
    # Meals / Food
    {"merchant_contains": "Starbucks", "category": "Meals"},
    {"merchant_contains": "McDonald", "category": "Meals"},
    {"merchant_contains": "KFC", "category": "Meals"},
    {"merchant_contains": "Pizza", "category": "Meals"},
    
    # Office / Work Related
    {"merchant_contains": "Amazon", "category": "Office Supplies"},
    {"merchant_contains": "Daraz", "category": "Office Supplies"},
    {"merchant_contains": "Upwork", "category": "Client Payment"},
    {"merchant_contains": "PayPal", "category": "Software Subscription"},
    {"merchant_contains": "Shopify", "category": "E-commerce Fees"},
    {"merchant_contains": "Google", "category": "Advertising"},
    {"merchant_contains": "Canva", "category": "Design Tool"},
    {"merchant_contains": "Zoom", "category": "Communication"},
    
    # Transportation / Travel
    {"merchant_contains": "Uber", "category": "Travel"},
    {"merchant_contains": "Careem", "category": "Travel"},
    {"merchant_contains": "Shell", "category": "Fuel"},
    {"merchant_contains": "PSO", "category": "Fuel"},
    {"merchant_contains": "Total", "category": "Fuel"},
    {"merchant_contains": "FedEx", "category": "Shipping"},
    
    # Utilities / Bills
    {"merchant_contains": "K-Electric", "category": "Electricity Bill"},
    {"merchant_contains": "LESCO", "category": "Electricity Bill"},
    {"merchant_contains": "MEPCO", "category": "Electricity Bill"},
    {"merchant_contains": "SNGPL", "category": "Gas Bill"},
    {"merchant_contains": "PTCL", "category": "Internet & Landline"},
    {"merchant_contains": "Jazz", "category": "Mobile Bill"},
    {"merchant_contains": "Zong", "category": "Mobile Bill"},
    {"merchant_contains": "Ufone", "category": "Mobile Bill"},
    {"merchant_contains": "Telenor", "category": "Mobile Bill"},
    
    # Subscriptions / Entertainment
    {"merchant_contains": "Netflix", "category": "Entertainment"},
    {"merchant_contains": "Spotify", "category": "Entertainment"},
    {"merchant_contains": "YouTube", "category": "Entertainment"},
    
    # Banking / Fees
    {"merchant_contains": "Bank", "category": "Bank Charges"},
    {"merchant_contains": "ATM", "category": "Bank Charges"},
    {"merchant_contains": "Fee", "category": "Service Fee"},
    {"merchant_contains": "Charge", "category": "Service Fee"},
    
    # Shopping / Groceries
    {"merchant_contains": "Walmart", "category": "Groceries"},
    {"merchant_contains": "Carrefour", "category": "Groceries"},
    {"merchant_contains": "Imtiaz", "category": "Groceries"},
    {"merchant_contains": "Metro", "category": "Groceries"},
    {"merchant_contains": "Al Fatah", "category": "Groceries"},
    
    # Income
    {"merchant_contains": "Salary", "category": "Salary Income"},
    {"merchant_contains": "Bonus", "category": "Salary Income"},
    {"merchant_contains": "Interest", "category": "Interest Income"},
    {"merchant_contains": "Profit", "category": "Business Income"},
    
    # Other
    {"merchant_contains": "Donation", "category": "Charity"},
    {"merchant_contains": "Hospital", "category": "Medical Expense"},
    {"merchant_contains": "Pharmacy", "category": "Medical Expense"},
]

def apply_rules(row):
    for r in rules:
        if r["merchant_contains"].lower() in str(row["merchant_name"]).lower():
            return r["category"]
    return "Uncategorized"

df["category"] = df.apply(apply_rules, axis=1)

# ---------- P&L REPORT ----------
st.markdown("<h3 class='sub-header'>📊 Profit & Loss Report (by Category)</h3>", unsafe_allow_html=True)
df["signed_amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

pnl = df.groupby("category").agg(
    Total_Income=("signed_amount", lambda x: x[x > 0].sum()),
    Total_Expense=("signed_amount", lambda x: -x[x < 0].sum()),
    Net_Amount=("signed_amount", "sum"),
).reset_index()

st.dataframe(pnl, use_container_width=True)

# ---------- TAX VIEW ----------
st.markdown("<h3 class='sub-header'>💰 Schedule C (Tax View)</h3>", unsafe_allow_html=True)

try:
    mapping = pd.read_csv("tax_mapping_schedule_c.csv")
except FileNotFoundError:
    st.warning("⚠ Tax mapping file not found. Make sure 'tax_mapping_schedule_c.csv' is in the same folder.")
    st.stop()

tax_view = pnl.merge(mapping, on="category", how="left")

def deductible(row):
    amt = row["Net_Amount"]
    pct = row.get("deductibility_pct", 100)
    return amt * (pct / 100) if amt < 0 else amt

tax_view["Deductible Amount"] = tax_view.apply(deductible, axis=1)

tax_report = tax_view.groupby(
    ["tax_line_code", "tax_line_name", "deductibility_pct"]
)["Deductible Amount"].sum().reset_index()

tax_report.rename(columns={"Deductible Amount": "Total Deductible ($)"}, inplace=True)
st.dataframe(tax_report, use_container_width=True)

# ---------- DOWNLOAD BUTTONS ----------
col1, col2 = st.columns(2)
with col1:
    st.download_button(
        "⬇ Download P&L Report",
        pnl.to_csv(index=False).encode("utf-8"),
        "pnl_report.csv",
        "text/csv"
    )
with col2:
    st.download_button(
        "⬇ Download Schedule C Report",
        tax_report.to_csv(index=False).encode("utf-8"),
        "schedule_c_report.csv",
        "text/csv"
    )

st.success("✅ Reports generated successfully!")

st.markdown("<br><hr><center>Streamlit Accounting App (Universal CSV)</center>", unsafe_allow_html=True)