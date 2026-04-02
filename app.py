import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Page Configuration
st.set_page_config(page_title="AI Bid Analyzer", layout="wide")

st.title("🏗️ AI Best Value Bid Analyzer")
st.markdown("Upload your bid comparison sheet to analyze cost, consistency, and suspect pricing.")

# --- 1. DATA UPLOAD & HANDLING ---
uploaded_file = st.file_uploader("Upload Bid Tab", type=["csv", "xlsx"])

if uploaded_file:
    # Read the file based on extension
    if uploaded_file.name.endswith('.csv'):
        raw_df = pd.read_csv(uploaded_file)
    else:
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_name = st.selectbox("Select Sheet", excel_file.sheet_names)
        raw_df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
    
    # --- 2. DATA CLEANING ---
    # Forward fill the Bidder column (fixes the grouped structure in your file)
    if 'Bidder' in raw_df.columns:
        raw_df['Bidder'] = raw_df['Bidder'].ffill()
    else:
        st.error("Error: Could not find a 'Bidder' column. Please check your file headers.")
        st.stop()
    
    vendors = raw_df['Bidder'].unique().tolist()
    
    try:
        # Create a pivot for line-item comparison (Unit Price)
        bid_tab = raw_df.pivot_table(
            index='Item Description', 
            columns='Bidder', 
            values='Unit Price', 
            aggfunc='first'
        )

        # --- 3. OVERALL BID SUMMARY ---
        st.header("1. Overall Bid Summary")
        
        # Calculate Grand Totals from the original "Total Price" column
        totals = raw_df.groupby('Bidder')['Total Price'].sum().sort_values()
        best_vendor = totals.idxmin()
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Lowest Overall Bidder", best_vendor, f"${totals.min():,.2f}")
            st.write("### Grand Totals")
            st.dataframe(totals.rename("Total Bid").map("${:,.2f}".format))
            
        with col2:
            fig_total = px.bar(
                totals, x=totals.index, y=totals.values, 
                title="Grand Total Comparison", 
                labels={'y':'Total Cost', 'Bidder':'Company'},
                color=totals.index,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            st.plotly_chart(fig_total, use_container_width=True)

        st.divider()

        # --- 4. BEST VALUE SCORECARD ---
        st.header("2. Best Value Scorecard")
        
        # Calculations for Scorecard Metrics
        bid_tab['Mean'] = bid_tab[vendors].mean(axis=1)
        bid_tab['Median'] = bid_tab[vendors].median(axis=1)
        bid_tab['Std_Dev'] = bid_tab[vendors].std(axis=1)

        scorecard_data = []
        for v in vendors:
            # 1. Count how many items this vendor is the lowest on
            low_count = (bid_tab[vendors].idxmin(axis=1) == v).sum()
