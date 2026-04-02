import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Set the page to wide mode
st.set_page_config(page_title="AI Bid Analyzer", layout="wide")

st.title("🏗️ AI Best Value Bid Analyzer")
st.markdown("Upload your bid comparison sheet to analyze cost, consistency, and suspect pricing.")

# --- 1. DATA UPLOAD ---
uploaded_file = st.file_uploader("Upload Bid Tab", type=["csv", "xlsx"])

if uploaded_file:
    # A. Read the file
    if uploaded_file.name.endswith('.csv'):
        raw_df = pd.read_csv(uploaded_file)
    else:
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_name = st.selectbox("Select Sheet", excel_file.sheet_names)
        raw_df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
    
    # B. Forward fill the 'Bidder' column (fixes grouped structure)
    if 'Bidder' in raw_df.columns:
        raw_df['Bidder'] = raw_df['Bidder'].ffill()
    else:
        st.error("Error: Could not find a 'Bidder' column in your file.")
        st.stop()

    # Get list of unique bidders
    vendors = raw_df['Bidder'].unique().tolist()
    
    # C. Create Comparison Matrix (Unit Price)
    bid_tab = raw_df.pivot_table(
        index='Item Description', 
        columns='Bidder', 
        values='Unit Price', 
        aggfunc='first'
    )

    # --- 2. OVERALL BID SUMMARY (SECTION 1) ---
    st.header("1. Overall Bid Summary")
    
    # Calculate Grand Totals (Sum of 'Total Price' per bidder)
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

    # --- 3. BEST VALUE SCORECARD (SECTION 2) ---
    st.header("2. Best Value Scorecard")
    
    # Statistical Calculations
    bid_tab['Mean'] = bid_tab[vendors].mean(axis=1)
    bid_tab['Median'] = bid_tab[vendors].median(axis=1)
    bid_tab['Std_Dev'] = bid_tab[vendors].std(axis=1)

    scorecard_data = []
    for v in vendors:
        # Count items where this vendor has the absolute lowest price
        is_lowest = (bid_tab[vendors].idxmin(axis=1) == v).sum()
        
        # Count suspect bids (where Price is > 1.5 Standard Deviations from Mean)
        suspects = 0
        for idx, row in bid_tab.iterrows():
            if row['Std_Dev'] > 0:
                z_score = abs(row[v] - row['Mean']) / row['Std_Dev']
                if z_score > 1.5:
                    suspects += 1
        
        # Calculate Average Variance from Market Average
        avg_var = ((bid_tab[v] - bid_tab['Mean']) / bid_tab['Mean']).mean() * 100

        scorecard_data.append({
            "Bidder": v,
            "Total Bid": totals[v],
            "Items at Lowest Price": is_lowest,
            "Suspect Outliers": suspects,
            "Avg % vs Market": avg_var
        })

    score_df = pd.DataFrame(scorecard_data).set_index("Bidder").sort_values("Total Bid")

    st.write("### Value Rankings & Risk Metrics")
    styled_scorecard = (
        score_df.style
        .highlight_min(subset=['Total Bid', 'Suspect Outliers'], color='#b7e4c7')
        .highlight_max(subset=['Items at Lowest Price'], color='#b7e4c7')
        .format({"Total Bid": "${:,.2f}", "Avg % vs Market": "{:.2f}%"})
    )
    st.dataframe(styled_scorecard, use_container_width=True)

    st.divider()

    # --- 4. LINE ITEM STATISTICAL AUDIT (SECTION 3) ---
    st.header("3. Line Item Statistical Audit")
    
    # Identify which specific bidder is an outlier for each line item
    def find_suspects(row):
        flags = []
        for v in vendors:
            if row['Std_Dev'] > 0:
                if abs(row[v] - row['Mean']) / row['Std_Dev'] > 1.5:
                    flags.append(v)
        return ", ".join(flags) if flags else "Consistent"

    bid_tab['Suspect Bidders'] = bid_tab.apply(find_suspects, axis=1)

    st.write("### Detailed Line Item Comparison Matrix")
    styled_bid_tab = (
        bid_tab.style
        .highlight_min(subset=vendors, axis=1, color='#b7e4c7')
        .highlight_max(subset=vendors, axis=1, color='#ffccd5')
        .format(subset=['Mean', 'Median', 'Std_Dev'] + vendors, precision=2)
    )
    st.dataframe(styled_bid_tab, use_container_width=True)

    # Graphical Drill Down
    st.subheader("Price Variance Visualization")
    selected_item = st.selectbox("Select Item to Graph Variance:", bid_tab.index)
    
    item_vals = bid_tab.loc[selected_item, vendors].reset_index()
    item_vals.columns = ['Bidder', 'Price']
    
    fig_var = px.bar(
        item_vals, x='Bidder', y='Price', 
        color='Price', title=f"Price Spread: {selected_item}",
        color_continuous_scale='RdYlGn_r'
    )
    fig_var.add_hline(y=bid_tab.loc[selected_item, 'Mean'], line_dash="dot", 
                      annotation_text="Market Mean", annotation_position="top left")
    
    st.plotly_chart(fig_var, use_container_width=True)
