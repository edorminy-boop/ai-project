import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="AI Bid Analyzer", layout="wide")

st.title("🏗️ AI Bid Tab Analyzer")
st.markdown("Upload your bid comparison sheet (CSV or Excel) to identify value and discrepancies.")

# --- 1. DATA UPLOAD ---
# Updated to allow both formats
uploaded_file = st.file_uploader("Upload Bid Tab", type=["csv", "xlsx"])

if uploaded_file:
    # 2. FILE HANDLING LOGIC
    if uploaded_file.name.endswith('.csv'):
        raw_df = pd.read_csv(uploaded_file)
    else:
        # For Excel, we check for sheets
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_name = st.selectbox("Select Sheet", excel_file.sheet_names)
        raw_df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
    
    # --- 3. CLEANING & PRE-PROCESSING ---
    # Forward fill the Bidder column (fixes the grouped structure)
    if 'Bidder' in raw_df.columns:
        raw_df['Bidder'] = raw_df['Bidder'].ffill()
    else:
        st.error("Could not find a column named 'Bidder'. Please check your file headers.")
        st.stop()
    
    # Identify unique bidders
    vendors = raw_df['Bidder'].unique().tolist()
    
    # --- 4. PIVOTING FOR COMPARISON ---
    # Rows = Items, Columns = Bidders, Values = Unit Price
    try:
        bid_tab = raw_df.pivot_table(
            index='Item Description', 
            columns='Bidder', 
            values='Unit Price', 
            aggfunc='first'
        )
        
        # --- 5. OVERALL TOTALS (BEST VALUE) ---
        st.header("1. Overall Bid Summary")
        
        # Calculate totals from the original Total Price column
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
                title="Total Bid Comparison", 
                labels={'y':'Total Cost', 'Bidder':'Company'},
                color=totals.index,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            st.plotly_chart(fig_total, use_container_width=True)

        st.divider()

        # --- 6. STATISTICAL AUDIT ---
        st.header("2. Line Item Variance & Suspect Bids")
        
        # Calculations
        bid_tab['Mean'] = bid_tab[vendors].mean(axis=1)
        bid_tab['Median'] = bid_tab[vendors].median(axis=1)
        bid_tab['Std_Dev'] = bid_tab[vendors].std(axis=1)

        # Flagging Logic (1.5 Standard Deviations)
        def detect_outliers(row):
            outliers = []
            for v in vendors:
                if row['Std_Dev'] > 0:
                    z_score = abs(row[v] - row['Mean']) / row['Std_Dev']
                    if z_score > 1.5:
                        outliers.append(v)
            return ", ".join(outliers) if outliers else "None"

        bid_tab['Suspect Bidders'] = bid_tab.apply(detect_outliers, axis=1)

        # Display Comparison Table
        st.write("### Unit Price Comparison Matrix")
        st.dataframe(
            bid_tab.style.highlight_min(subset=vendors, axis=1, color='#b7e4c7')
                        .highlight_max(subset=vendors, axis=1, color='#ffccd5')
                        .format(precision=2)
        )

        # Heatmap
        st.subheader("Price Intensity Heatmap")
        fig_heat = px.imshow(
            bid_tab[vendors], 
            aspect="auto", 
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    except Exception as e:
        st.error(f"Error processing data: {e}")

else:
    st.info("👋 Please upload your Excel or CSV bid tab to begin analysis.")
