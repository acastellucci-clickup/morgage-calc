import pandas as pd
import streamlit as st
import requests

# Function to fetch live rate
def fetch_current_rate(api_key):
    resp = requests.get(
        "https://api.api-ninjas.com/v1/mortgagerate",
        headers={"X-Api-Key": api_key}
    )
    if resp.status_code == 200:
        return resp.json().get("rate_30yr_fixed")
    return None

# Sidebar inputs
st.sidebar.header("Adjustable Variables")
property_tax_rate = st.sidebar.number_input("Annual Property Tax Rate (%)", value=1.2, step=0.1) / 100
insurance_rate = st.sidebar.number_input("Annual Home Insurance Rate (%)", value=0.35, step=0.05) / 100
loan_term_years = st.sidebar.selectbox("Loan Term (Years)", [15, 30], index=1)

# Mortgage API integration
api_key = st.secrets.get("MORTGAGE_API_KEY", None)
live_rate = fetch_current_rate(api_key) if api_key else None

st.subheader("Current 30-Year Fixed Mortgage Rate")
if live_rate:
    st.write(f"Today's 30-year fixed rate: **{live_rate:.2f}%**")
    default_rate = live_rate / 100
else:
    st.warning("Could not retrieve live rate — enter manually.")
    default_rate = None

interest_prompt = st.number_input(
    "Annual Interest Rate (%)",
    value=(live_rate if live_rate else 6.6),
    step=0.01
) / 100

# Ranges
home_prices = range(500_000, 1_500_001, 100_000)
down_payments = range(100_000, 351_000, 50_000)

# Mortgage calculation
def monthly_payment(principal, annual_rate, years):
    monthly_rate = annual_rate / 12
    n_payments = years * 12
    if monthly_rate == 0:
        return principal / n_payments
    return principal * (monthly_rate * (1 + monthly_rate) ** n_payments) / ((1 + monthly_rate) ** n_payments - 1)

# Build grid
grid = {}
for down in down_payments:
    row = []
    for price in home_prices:
        loan_amount = max(price - down, 0)
        mortgage = monthly_payment(loan_amount, interest_prompt, loan_term_years)
        taxes = (price * property_tax_rate) / 12
        insurance = (price * insurance_rate) / 12
        total = mortgage + taxes + insurance
        row.append(round(total, 0))
    grid[f"Down {down/1000:.0f}k"] = row

df = pd.DataFrame(grid, index=[f"${p/1000:.0f}k" for p in home_prices]).T

st.write("### Expected Monthly Housing Costs")
st.dataframe(df)

# Download option
csv = df.to_csv().encode("utf-8")
st.download_button(
    label="Download table as CSV",
    data=csv,
    file_name="housing_costs.csv",
    mime="text/csv",
)
