import streamlit as st
import pandas as pd

st.title("📊 WR Tracker Dashboard")

# ----------------------------------
# LOAD DATA
# ----------------------------------
@st.cache_data
def load_data():
    file_path = ("wr_tracker_full_dummy.xlsx")
    df = pd.read_excel(file_path)

    df.columns = df.columns.str.replace("\n", " ").str.strip()

    df["TCV"] = (
        df["TCV"].astype(str)
        .str.replace(",", "")
        .str.replace("₹", "")
        .str.strip()
    )
    df["TCV"] = pd.to_numeric(df["TCV"], errors="coerce").fillna(0)

    date_cols = [
        "Signed Date",
        "Start Date",
        "End Date",
        "Current Contract End Date",
        "Current PO End Date / Forecasted Date for PO Consumption",
    ]

    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


# ----------------------------------
# LOAD
# ----------------------------------
try:
    df = load_data()

    if "selected_wr" not in st.session_state:
        st.session_state.selected_wr = None

    # FILTERS
    st.sidebar.header("🔍 Filters")

    wr_list = sorted(df["WR Reference"].dropna().unique().tolist())
    selected_wr = st.sidebar.selectbox("Select WR", ["All"] + wr_list)

    if selected_wr != "All":
        opp_list = sorted(
            df[df["WR Reference"] == selected_wr]["Opp Name"]
            .dropna()
            .unique()
            .tolist()
        )
    else:
        opp_list = sorted(df["Opp Name"].dropna().unique().tolist())

    selected_opp = st.sidebar.selectbox("Select Opp Name", ["All"] + opp_list)

    status_options = df["Status"].dropna().unique()
    status_filter = st.sidebar.multiselect("Status", status_options, default=status_options)

    # ----------------------------------
    # DETAILS PAGE (ENHANCED UI)
    # ----------------------------------
    if st.session_state.selected_wr is not None:
        row = st.session_state.selected_wr

        st.markdown(f"## 📄 WR Details: {row['WR Reference']}")

        if st.button("⬅️ Back"):
            st.session_state.selected_wr = None
            st.rerun()

        col1, col2 = st.columns(2)

        def big_text(label, value):
            st.markdown(
                f"""
                <div style="margin-bottom:12px;">
                    <span style="font-size:15px; color:gray;">{label}</span><br>
                    <span style="font-size:20px; font-weight:600;">{value}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col1:
            big_text("Project", row["Transform / Project"])
            big_text("TCV", f"₹ {row['TCV']}")
            big_text("Start Date", row["Start Date"])
            big_text("End Date", row["End Date"])
            big_text("Risk", row["Risk to Delivery"])
            big_text("Next Steps", row["Next Steps"])

        with col2:
            big_text("IBM Owner", row["IBM Owner"])
            big_text("KD Owner", row["KD Programme level owner"])
            big_text("PM", row["KD PM on PCR"])
            big_text("Contract End", row["Current Contract End Date"])

        st.stop()

    # ----------------------------------
    # SUMMARY
    # ----------------------------------
    st.subheader("📌 Summary")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total WRs", len(df))
    col2.metric("Signed", df[df["Status"] == "Signed"].shape[0])
    col3.metric("Pending", df[df["Status"] != "Signed"].shape[0])
    col4.metric("On Hold", df[df["Status"] == "On Hold"].shape[0])

    # ----------------------------------
    # WR LIST (ENHANCED UI)
    # ----------------------------------
    st.subheader("📋 WR List")

    if selected_wr == "All" and selected_opp == "All":
        st.info("🔎 Please select WR or Opp Name")
    else:
        filtered_df = df.copy()

        if selected_wr != "All":
            filtered_df = filtered_df[filtered_df["WR Reference"] == selected_wr]

        if selected_opp != "All":
            filtered_df = filtered_df[filtered_df["Opp Name"] == selected_opp]

        if len(status_filter) != len(status_options):
            filtered_df = filtered_df[filtered_df["Status"].isin(status_filter)]

        if filtered_df.empty:
            st.warning("No matching WR found")
        else:
            st.markdown("### 👇 Click below to view WR details")

            for idx, row in filtered_df.iterrows():
                col1, col2 = st.columns([8, 2])

                col1.markdown(
                    f"""
                    <div style="
                        padding:10px;
                        border-radius:10px;
                        background-color:#f0f2f6;
                        margin-bottom:6px;
                        font-size:16px;
                        font-weight:500;">
                        {row['WR Reference']} | {row['Opp Name']} | {row['Status']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if col2.button("View", key=f"view_{idx}"):
                    st.session_state.selected_wr = row
                    st.rerun()

    st.markdown("---")

    # ----------------------------------
    # ALERTS
    # ----------------------------------
    st.subheader("⚠️ Contract Alerts")

    today = pd.Timestamp.today()

    expiring = df[
        (df["Current Contract End Date"].notna())
        & (df["Current Contract End Date"] >= today)
        & (df["Current Contract End Date"] <= today + pd.Timedelta(days=30))
    ]

    if not expiring.empty:
        st.markdown("### ⏳ Expiring Soon (Next 30 Days)")
        st.dataframe(expiring[["WR Reference", "Opp Name", "Current Contract End Date"]])
    else:
        st.info("No contracts expiring")

    st.markdown("---")

    # ----------------------------------
    # TABLE
    # ----------------------------------
    st.subheader("WR Detailed Table")

    table_search = st.text_input("🔎 Search")

    table_df = df.copy()

    if table_search:
        table_df = table_df[
            table_df["WR Reference"].astype(str).str.contains(table_search, case=False)
            | table_df["Opp Name"].astype(str).str.contains(table_search, case=False)
        ]

    st.dataframe(table_df, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
