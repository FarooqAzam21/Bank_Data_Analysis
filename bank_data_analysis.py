import streamlit as st
import pandas as pd

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Accounting App", layout="wide")

# ---------- HEADER ----------
st.markdown(
    """
    <style>
    .main-title {
        font-size: 36px;
        font-weight: 700;
        text-align: center;
        color: #2E86C1;
    }
    .sub-header {
        font-size: 22px;
        font-weight: 600;
        margin-top: 20px;
        color: #117864;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<h1 class='main-title'>💼 Accounting App — Gen 1</h1>", unsafe_allow_html=True)
st.write("### Upload your transaction CSV to generate Profit & Loss and Schedule C Tax Reports")

st.divider()

# ---------- FILE UPLOAD ----------
uploaded = st.file_uploader("📂 Upload transactions CSV file", type=["csv"])
if not uploaded:
    st.info("Please upload your `sample_transactions.csv` file to start.")
    st.stop()

df = pd.read_csv(uploaded)
st.markdown("<h3 class='sub-header'>📋 Preview of Uploaded Data</h3>", unsafe_allow_html=True)
st.dataframe(df.head(10), use_container_width=True)

st.divider()

# ---------- CATEGORIZATION RULES ----------
rules = [
    {"merchant_contains": "Starbucks", "category": "Meals"},
    {"merchant_contains": "Amazon", "category": "Office Supplies"},
    {"merchant_contains": "Uber", "category": "Travel"},
    {"merchant_contains": "PayPal", "category": "Software Subscription"},
    {"merchant_contains": "Upwork", "category": "Client Payment"},
    {"merchant_contains": "Netflix", "category": "Entertainment"},
    {"merchant_contains": "Walmart", "category": "Groceries"},
    {"merchant_contains": "Shell", "category": "Fuel"},
    {"merchant_contains": "FedEx", "category": "Shipping"},
    {"merchant_contains": "Google", "category": "Advertising"},
    {"merchant_contains": "Canva", "category": "Design Tool"},
    {"merchant_contains": "Zoom", "category": "Communication"},
    {"merchant_contains": "Shopify", "category": "E-commerce Fees"},
]

def apply_rules(row):
    for r in rules:
        if r["merchant_contains"].lower() in str(row["merchant_name"]).lower():
            return r["category"]
    return "Uncategorized"

df["category"] = df.apply(apply_rules, axis=1)
df["signed_amount"] = df.apply(lambda x: x["amount"] if x["direction"] == "in" else -x["amount"], axis=1)

# ---------- P&L REPORT ----------
st.markdown("<h3 class='sub-header'>📊 Profit & Loss Report (by Category)</h3>", unsafe_allow_html=True)

pnl = df.groupby("category").agg(
    Total_Income=("signed_amount", lambda x: x[x > 0].sum()),
    Total_Expense=("signed_amount", lambda x: -x[x < 0].sum()),
    Net_Amount=("signed_amount", "sum"),
).reset_index()

pnl.fillna(0, inplace=True)
st.dataframe(pnl, use_container_width=True)

# ---------- TAX VIEW ----------
st.markdown("<h3 class='sub-header'>💰 Schedule C (Tax View)</h3>", unsafe_allow_html=True)

mapping = pd.read_csv("tax_mapping_schedule_c.csv")
tax_view = pnl.merge(mapping, on="category", how="left")

def deductible(row):
    amt = row["Net_Amount"]
    return amt * (row["deductibility_pct"] / 100) if amt < 0 else amt

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
        "⬇️ Download P&L Report",
        pnl.to_csv(index=False).encode("utf-8"),
        "pnl_report.csv",
        "text/csv"
    )
with col2:
    st.download_button(
        "⬇️ Download Schedule C Report",
        tax_report.to_csv(index=False).encode("utf-8"),
        "schedule_c_report.csv",
        "text/csv"
    )

st.success("✅ Reports generated successfully!")

# ---------- FOOTER ----------
st.markdown("<br><hr><center>Streamlit Accounting App Gen 1</center>", unsafe_allow_html=True)
