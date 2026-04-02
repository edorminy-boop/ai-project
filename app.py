import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="AI Bid Analyzer", layout="wide")

st.title("🏗️ AI Bid Tab Analyzer")
st.markdown("Automated comparison for grouped bidder data.")

# --- 1. DATA UPLOAD & CLEANING ---
uploaded_file = st.file_uploader("Upload your 'sample bid tab' CSV", type=["csv"])

if uploaded_file:
    # Load the raw data
    raw_df = pd.read_csv(uploaded_file)
    
    # CRITICAL STEP: Forward fill the Bidder column 
    # (Since your file only lists the name once per section)
    raw_df['Bidder'] = raw_df['Bidder'].ffill()
    
    # Identify unique bidders and items
    vendors = raw_df['Bidder'].unique().tolist()
    
    # --- 2. PIVOTING FOR COMPARISON ---
    # We create a table where rows = Items and columns = Bidders
    # We will use 'Unit Price' for the detailed line item analysis
    bid_tab = raw_df.pivot_table(
        index='Item Description', 
        columns='Bidder', 
        values='Unit Price', 
        aggfunc='first'
    )
    
    # --- 3. OVERALL TOTALS (BEST VALUE) ---
    st.header("1. Best Value Analysis")
    
    # Calculate totals from the original Total Price column
    totals = raw_df.groupby('Bidder')['Total Price'].sum().sort_values()
    best_vendor = totals.idxmin()
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Lowest Overall Bidder", best_vendor, f"${totals.min():,.2f}")
        st.write("### Total Bid Amounts")
        st.dataframe(totals.rename("Grand Total").map("${:,.2f}".format))
        
    with col2:
        fig_total = px.bar(
            totals, x=totals.index, y=totals.values, 
            title="Total Bid Comparison", 
            labels={'y':'Total Cost', 'Bidder':'Company'},
            color=totals.index,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_total, use_container_width=True)

    st.divider()

    # --- 4. LINE ITEM VARIANCE & STATS ---
    st.header("2. Line Item & Discrepancy Audit")
    
    # Add Statistical Calculations
    bid_tab['Mean'] = bid_tab[vendors].mean(axis=1)
    bid_tab['Median'] = bid_tab[vendors].median(axis=1)
    bid_tab['Std_Dev'] = bid_tab[vendors].std(axis=1)

    # Logic to flag "Suspect" prices (more than 1.5 Std Dev from Mean)
    def detect_outliers(row):
        outliers = []
        for v in vendors:
            if row['Std_Dev'] > 0:
                z_score = abs(row[v] - row['Mean']) / row['Std_Dev']
                if z_score > 1.5:
                    outliers.append(v)
        return ", ".join(outliers) if outliers else "None"

    bid_tab['Suspect Bids'] = bid_tab.apply(detect_outliers, axis=1)

    # Display the Comparison Table
    st.write("### Bid Comparison Matrix (Unit Prices)")
    st.dataframe(
        bid_tab.style.highlight_min(subset=vendors, axis=1, color='#b7e4c7')
                    .highlight_max(subset=vendors, axis=1, color='#ffccd5')
                    .format(precision=2)
    )

    # Visualizing individual item variance
    st.subheader("Price Intensity Heatmap")
    st.caption("Darker colors indicate higher unit prices for that specific item.")
    fig_heat = px.imshow(
        bid_tab[vendors], 
        aspect="auto", 
        color_continuous_scale='Viridis'
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # --- 5. DRILL DOWN ---
    st.divider()
    st.header("3. Item Drill Down")
    selected_item = st.selectbox("Select an item to view price distribution:", bid_tab.index)
    
    item_data = bid_tab.loc[selected_item, vendors].reset_index()
    item_data.columns = ['Bidder', 'Unit Price']
    
    fig_drill = px.scatter(
        item_data, x='Bidder', y='Unit Price', size='Unit Price', color='Bidder',
        title=f"Price Spread: {selected_item}", height=400
    )
    st.plotly_chart(fig_drill, use_container_width=True)

else:
    st.info("👋 Upload your CSV file to generate the analysis report.")
