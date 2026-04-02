import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="AI Bid Analyzer", layout="wide")

st.title("🏗️ AI Bid Tab Analyzer")

uploaded_file = st.file_uploader("Upload Bid Tab", type=["csv", "xlsx"])

if uploaded_file:
    # 1. Load Data
    raw_df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # 2. Identify Columns (Dynamically)
    # User selects which column is which
    cols = raw_df.columns.tolist()
    bidder_col = st.selectbox("Which column contains Bidder Names?", cols, index=0)
    desc_col = st.selectbox("Which column contains Line Item Descriptions?", cols, index=1)
    price_col = st.selectbox("Which column contains the Unit Price/Total?", cols, index=2)

    # 3. PIVOT THE DATA (The Critical Step)
    # This transforms the data so Bidders are columns and Descriptions are unique rows
    try:
        df = raw_df.pivot_table(index=desc_col, columns=bidder_col, values=price_col, aggfunc='first')
        vendors = df.columns.tolist()
        
        st.success(f"Analyzed {len(vendors)} unique bidders across {len(df)} line items.")
        
        # --- SECTION 1: BEST VALUE ---
        st.header("1. Overall Bid Summary")
        totals = df.sum().sort_values()
        
        c1, c2 = st.columns([1, 2])
        c1.metric("Lowest Overall Bidder", totals.idxmin(), f"${totals.min():,.2f}")
        c1.dataframe(totals.rename("Total").map("${:,.2f}".format))
        
        fig_total = px.bar(totals, x=totals.index, y=totals.values, title="Total Cost Comparison", color=totals.index)
        c2.plotly_chart(fig_total, use_container_width=True)

        # --- SECTION 2: LINE ITEM VARIANCE ---
        st.header("2. Line Item Audit")
        
        # Statistical Calculations
        df['Mean'] = df[vendors].mean(axis=1)
        df['Median'] = df[vendors].median(axis=1)
        df['Std_Dev'] = df[vendors].std(axis=1)
        
        # Flag suspect bids (1.5 Standard Deviations from Mean)
        def get_flags(row):
            flags = [v for v in vendors if row['Std_Dev'] > 0 and abs(row[v] - row['Mean']) > (1.5 * row['Std_Dev'])]
            return ", ".join(flags) if flags else "Consistent"

        df['Suspect Bidders'] = df.apply(get_flags, axis=1)
        
        st.write("### Data Table (Formatted)")
        st.dataframe(df.style.highlight_min(subset=vendors, axis=1, color='lightgreen').format(precision=2))

        # Heatmap for visualizing discrepancies
        st.subheader("Price Variance Heatmap")
        fig_heat = px.imshow(df[vendors], aspect="auto", color_continuous_scale='Viridis', title="Darker colors indicate higher relative costs")
        st.plotly_chart(fig_heat, use_container_width=True)

    except Exception as e:
        st.error(f"Error pivoting data: {e}. Ensure there are no empty price cells.")
