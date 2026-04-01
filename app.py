import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Page Config
st.set_page_config(page_title="AI Bid Analyzer", layout="wide")

st.title("🏗️ AI Bid Tab Analyzer")
st.markdown("Upload a bid comparison sheet to analyze value, variances, and discrepancies.")

# 1. File Upload
uploaded_file = st.file_uploader("Upload Bid Tab (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    # Load data
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    # Identify Vendors (Assumes first 2-3 columns are Description/Qty/Unit)
    # We identify numeric columns as potential vendor price columns
    all_cols = df.columns.tolist()
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Let user confirm which columns are the Vendors
    vendors = st.multiselect("Select Vendor Columns", numeric_cols, default=numeric_cols)
    description_col = st.selectbox("Select Line Item Description Column", all_cols, index=0)

    if vendors and description_col:
        # --- SECTION 1: BEST VALUE ANALYSIS ---
        st.header("1. Overall Bid Summary")
        
        totals = df[vendors].sum().sort_values()
        best_vendor = totals.idxmin()
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Best Value (Lowest Total)", best_vendor)
            st.write("**Total Bid Comparison**")
            st.dataframe(totals.rename("Total Bid Amount").map("${:,.2f}".format))
            
        with col2:
            fig_total = px.bar(totals, x=totals.index, y=totals.values, 
                               title="Total Bid Comparison", 
                               labels={'y':'Total Cost', 'index':'Vendor'},
                               color=totals.index)
            st.plotly_chart(fig_total, use_container_width=True)

        st.divider()

        # --- SECTION 2: LINE ITEM VARIANCE ---
        st.header("2. Line Item Detail & Variance")
        
        # Calculate Variance Data
        detail_df = df[[description_col] + vendors].copy()
        detail_df['Average'] = detail_df[vendors].mean(axis=1)
        
        # Display the table with conditional formatting
        st.write("### Line Item Comparison Table")
        st.dataframe(detail_df.style.highlight_min(subset=vendors, axis=1, color='lightgreen'))

        # Visualizing variance for a specific item
        selected_item = st.selectbox("Drill down into specific Line Item:", df[description_col].unique())
        item_row = detail_df[detail_df[description_col] == selected_item]
        
        # Plotly Variance Chart
        item_vals = item_row[vendors].T
        item_vals.columns = ['Price']
        fig_var = px.bar(item_vals, x=item_vals.index, y='Price', 
                         title=f"Price Spread for: {selected_item}",
                         color='Price', color_continuous_scale='RdYlGn_r')
        st.plotly_chart(fig_var, use_container_width=True)

        st.divider()

        # --- SECTION 3: STATISTICAL AUDIT (THE 'AI' LOGIC) ---
        st.header("3. Suspect Bid & Discrepancy Audit")
        
        audit_df = df[[description_col]].copy()
        audit_df['Mean'] = df[vendors].mean(axis=1)
        audit_df['Median'] = df[vendors].median(axis=1)
        audit_df['Std_Dev'] = df[vendors].std(axis=1)
        
        # Detection Logic: Flag values > 1.5 Std Dev from Mean
        def find_outliers(row):
            outliers = []
            for v in vendors:
                # Z-score calculation: (Value - Mean) / StdDev
                if row['Std_Dev'] > 0:
                    z_score = abs(row[v] - row['Mean']) / row['Std_Dev']
                    if z_score > 1.5:
                        outliers.append(f"{v} (Z:{z_score:.2f})")
            return ", ".join(outliers) if outliers else "Clean"

        audit_df = pd.concat([audit_df, df[vendors]], axis=1)
        audit_df['Suspect Flags'] = audit_df.apply(find_outliers, axis=1)
        
        # Display Anomalies
        st.subheader("Statistical Outlier Detection")
        st.info("Flags identify vendors significantly distant (1.5σ+) from the line item average.")
        st.dataframe(audit_df[[description_col, 'Mean', 'Median', 'Suspect Flags']])

        # Heatmap of Prices
        st.subheader("Price Intensity Heatmap")
        fig_heat = px.imshow(df[vendors], y=df[description_col], x=vendors, 
                             labels=dict(color="Price"),
                             color_continuous_scale='Viridis')
        st.plotly_chart(fig_heat, use_container_width=True)

else:
    st.info("Please upload a CSV or Excel file to begin.")
