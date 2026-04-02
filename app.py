import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="AI Bid Analyzer", layout="wide")

st.title("🏗️ AI Best Value Bid Analyzer")

# --- 1. DATA UPLOAD ---
uploaded_file = st.file_uploader("Upload Bid Tab", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        raw_df = pd.read_csv(uploaded_file)
    else:
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_name = st.selectbox("Select Sheet", excel_file.sheet_names)
        raw_df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
    
    # Forward fill Bidders
    raw_df['Bidder'] = raw_df['Bidder'].ffill()
    vendors = raw_df['Bidder'].unique().tolist()
    
    try:
        # Create Comparison Matrix
        bid_tab = raw_df.pivot_table(
            index='Item Description', 
            columns='Bidder', 
            values='Unit Price', 
            aggfunc='first'
        )
        
        # --- 2. OVERALL TOTALS ---
        st.header("1. Total Cost Comparison")
        totals = raw_df.groupby('Bidder')['Total Price'].sum().sort_values()
        
        fig_total = px.bar(
            totals, x=totals.index, y=totals.values, 
            text_auto='.2s', title="Total Project Cost by Bidder",
            color=totals.values, color_continuous_scale='RdYlGn_r'
        )
        st.plotly_chart(fig_total, use_container_width=True)

        st.divider()

        # --- 3. BEST VALUE COMPARISON (Replacement for Heatmap) ---
        st.header("2. Best Value Scorecard")
        st.info("This analysis scores vendors based on price position and bid reliability.")

        # Calculate Stats
        bid_tab['Mean'] = bid_tab[vendors].mean(axis=1)
        bid_tab['Std_Dev'] = bid_tab[vendors].std(axis=1)

        # Build Scorecard Data
        scorecard = []
        for v in vendors:
            # 1. Total Price
            v_total = totals[v]
            
            # 2. Find how many times this vendor was the lowest on a line item
            low_count = (bid_tab[vendors].idxmin(axis=1) == v).sum()
            
            # 3. Find how many "Suspect" items (more than 1.5 Std Dev from mean)
            suspect_count = 0
            for idx, row in bid_tab.iterrows():
                if row['Std_Dev'] > 0:
                    z_score = abs(row[v] - row['Mean']) / row['Std_Dev']
                    if z_score > 1.5:
                        suspect_count += 1
            
            scorecard.append({
                "Bidder": v,
                "Total Bid": v_total,
                "Lowest Price Items": low_count,
                "Suspect High/Low Items": suspect_count,
                "Market Alignment %": round((1 - (suspect_count / len(bid_tab))) * 100, 1)
            })

        score_df = pd.DataFrame(scorecard).set_index("Bidder").sort_values("Total Bid")

        # Display the Best Value Table
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("### Value Rankings")
            st.dataframe(
                score_df.style.highlight_min(subset=['Total Bid', 'Suspect High/Low Items'], color='#b7e4c7')
                            .highlight_max(subset=['Lowest Price Items', 'Market Alignment %'], color='#b7e4c7')
                            .format({"Total Bid": "${:,.2f}", "Market Alignment %": "{:.1f}%"})
            )
        
        with col2:
            st.write("### Quick Metrics")
            st.metric("Top Value Candidate", score_df.index[0])
            st.metric("Most Consistent Bidder", score_df['Market Alignment %'].idxmax())

        st.divider()

        # --- 4. LINE ITEM VARIANCE ---
        st.header("3. Line Item Discrepancies")
        
        # Add "Variance from Average" column for a specific vendor
        selected_v = st.selectbox("View Variance for Vendor:", vendors)
        bid_tab['Variance %'] = ((bid_tab[selected_v] - bid_tab['Mean']) / bid_tab['Mean']) * 100
        
        fig_var = px.bar(
            bid_tab.reset_index(), 
            x='Item Description', y='Variance %',
            title=f"Price Variance from Average: {selected_v}",
            color='Variance %', color_continuous_scale='RdBu_r', range_color=[-50, 50]
        )
        st.plotly_chart(fig_var, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.info("Please upload your Bid Tab to generate the Best Value report.")
