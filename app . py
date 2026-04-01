import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Set Page Config
st.set_page_config(page_title="AI Bid Tab Analyzer", layout="wide")

st.title("🏗️ AI Bid Tab Analysis Tool")
st.markdown("Upload your consolidated bid tab Excel file to generate instant reports.")

# --- SIDEBAR / UPLOAD ---
with st.sidebar:
    st.header("Upload Data")
    uploaded_file = st.file_uploader("Choose a Bid Tab file", type=["xlsx", "csv"])
    st.info("Ensure your file has columns: 'Bidder', 'Item Description', 'Quantity', 'Unit Price', and 'Total Price'.")

if uploaded_file:
    # Load Data
    try:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        
        # Data Cleaning: Ensure numeric types
        df['Unit Price'] = pd.to_numeric(df['Unit Price'], errors='coerce')
        df['Total Price'] = pd.to_numeric(df['Total Price'], errors='coerce')

        # --- TABS FOR THE 3 REPORTS ---
        report1, report2, report3 = st.tabs([
            "💰 1. Best Value Analysis", 
            "⚠️ 2. Discrepancy Report", 
            "📊 3. Average Cost Report"
        ])

        # --- REPORT 1: BEST VALUE BID ---
        with report1:
            st.header("Project Value Summary")
            # Calculate Total Project Cost per Bidder
            best_value = df.groupby('Bidder')['Total Price'].sum().reset_index()
            best_value = best_value.sort_values(by='Total Price')
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric("Lowest Bidder", best_value.iloc[0]['Bidder'])
                st.dataframe(best_value.style.format({"Total Price": "${:,.2f}"}))
            
            with col2:
                fig1 = px.bar(best_value, x='Bidder', y='Total Price', 
                             title="Overall Cost Comparison", 
                             color='Total Price', color_continuous_scale='Greens')
                st.plotly_chart(fig1, use_container_width=True)

        # --- REPORT 2: DISCREPANCIES ---
        with report2:
            st.header("Line Item Variance & Discrepancies")
            st.write("This report highlights items where bidders have significant price differences.")
            
            # Pivot table to see items side-by-side
            pivot_df = df.pivot(index='Item Description', columns='Bidder', values='Unit Price')
            
            # Calculate Coefficient of Variation (CV) to find the most "disputed" items
            pivot_df['Average'] = pivot_df.mean(axis=1)
            pivot_df['Std Dev'] = pivot_df.std(axis=1)
            pivot_df['Variance %'] = (pivot_df['Std Dev'] / pivot_df['Average']) * 100
            
            # Show interactive table with highlighting for high variance (>30%)
            st.subheader("Tabulated Discrepancies")
            st.dataframe(pivot_df.style.background_gradient(subset=['Variance %'], cmap='Reds'))

            # Graphical Report: Box Plot showing spread of unit prices
            st.subheader("Price Distribution per Item")
            fig2 = px.box(df, x="Item Description", y="Unit Price", color="Item Description", 
                         title="Market Spread per Line Item")
            st.plotly_chart(fig2, use_container_width=True)

        # --- REPORT 3: AVERAGE COST PER LINE ITEM ---
        with report3:
            st.header("Market Average Evaluation")
            st.write("The 'Collective Intelligence' price for every item in the scope.")
            
            avg_report = df.groupby('Item Description').agg({
                'Unit Price': ['mean', 'median', 'min', 'max']
            }).reset_index()
            
            # Flatten multi-index columns
            avg_report.columns = ['Item Description', 'Avg Price', 'Median Price', 'Min Price', 'Max Price']
            
            st.table(avg_report.style.format({
                "Avg Price": "${:,.2f}", "Median Price": "${:,.2f}", 
                "Min Price": "${:,.2f}", "Max Price": "${:,.2f}"
            }))

    except Exception as e:
        st.error(f"Error processing file: {e}")

else:
    st.warning("Please upload a file to begin the analysis.")
