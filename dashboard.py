import streamlit as st
import psycopg2
import pandas as pd
import os
import altair as alt
from zoneinfo import ZoneInfo

# Set wide layout
st.set_page_config(layout="wide")

# Load DATABASE_URL from environment variables
DB_URL = os.getenv("DB_URL")

if not DB_URL:
    st.error("❌ Database URL not set. Please check your environment variables.")
    st.stop()

@st.cache_data(ttl=60)  # Refresh every 60 seconds
def load_data():
    try:
        conn = psycopg2.connect(DB_URL)
        query = '''
            SELECT timestamp, name, votes
            FROM votes
            ORDER BY timestamp DESC
        '''
        df = pd.read_sql(query, conn)
        conn.close()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        st.error(f"❌ Database connection error: {e}")
        return pd.DataFrame()

# Page Title
st.title("📊 Bình chọn Tân Binh Toàn Năng")

# Load data
df = load_data()

# Show latest update time
if not df.empty:
    latest_time = df['timestamp'].max().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"#### 🕒 Kết quả mới nhất (cập nhật lúc: {latest_time})")

    # Get most recent vote per candidate
    latest_votes = df.loc[df.groupby('name')['timestamp'].idxmax()]

    # Sort by votes descending
    latest_votes_sorted = latest_votes.sort_values(by='votes', ascending=False).copy()
    latest_votes_sorted.reset_index(drop=True, inplace=True)

    # Add Rank column
    latest_votes_sorted['rank'] = latest_votes_sorted.index + 1

    # Define top 3 highlight function
    def highlight_top_3(row):
        if row.name < 3:
            return ['background-color: #d4edda'] * len(row)  # Light green
        else:
            return [''] * len(row)

    # 🔮 Altair Bar Chart
    st.subheader("🏆 Thứ hạng hiện tại")

    bar_chart = alt.Chart(latest_votes_sorted).mark_bar(
        tooltip=True
    ).encode(
        x=alt.X('name:N', sort='-y', title='Tân binh',
            axis=alt.Axis(
            labelAngle=-45,      # ← Rotate labels 45 degrees
            labelLimit=200,      # ← Allow longer labels
            labelOverlap=False   # ← Prevent overlapping
        )),
        y=alt.Y('votes:Q', title='Tỉ lệ bình chọn (%)'),
        color=alt.condition(
            alt.datum.rank <= 3,
            alt.value('#28a745'),  # Green for top 3
            alt.value('#4e79a7')   # Default blue
        ),
        tooltip=[
            alt.Tooltip('name:N', title='Tân binh'),
            alt.Tooltip('votes:Q', title='Tỉ lệ bình chọn (%)', format='.2f'),
            alt.Tooltip('rank:O', title='Thứ hạng')
        ]
    ).properties(
        height=500,
        width="container"  # Optional: auto-width to match page layout
    )

    st.altair_chart(bar_chart, use_container_width=True)

    # 📈 Altair Line Chart with Legend Sorted by Vote Score and UTC Timestamps
    st.subheader("📈 Tỉ lệ bình chọn theo thời gian")

    # Step 1: Get latest vote per candidate and sort by vote descending
    latest_votes = df.loc[df.groupby('name')['timestamp'].idxmax()]
    latest_votes_sorted = latest_votes.sort_values(by='votes', ascending=False)
    sorted_names = list(latest_votes_sorted['name'])

    # Step 2: Make sure timestamp is treated as "naive"
    df_chart = df.copy()
    df_chart['timestamp'] = df_chart['timestamp'].dt.tz_localize(None)

    # Step 3: Build the chart with custom color scale domain
    # Function to extract initials
    def get_initials(name):
        return ''.join([part[0] for part in name.split() if part.strip()][:4])  # Take first 2 letters

    # Add a new 'initials' column
    latest_votes_sorted['initials'] = latest_votes_sorted['name'].apply(get_initials)

    # Merge initials back into main DataFrame for charting
    df_chart = df.merge(
        latest_votes_sorted[['name', 'initials']],
        on='name',
        how='left'
    )

    # Use initials for legend and sorting
    sorted_names = list(latest_votes_sorted['initials'])

    line_chart = alt.Chart(df_chart).mark_line(point=True).encode(
        x=alt.X('timestamp:T', title='Thời gian'),
        y=alt.Y('votes:Q', title='Tỉ lệ bình chọn (%)'),
        color=alt.Color(
            'initials:N',
            title='Tân binh',
            scale=alt.Scale(domain=sorted_names),
            sort=None,
            legend=alt.Legend(
                orient='right',         # ← Move legend to the right
                direction='vertical',   # ↑ Vertical layout for more space
            )
        ),
        tooltip=[
            alt.Tooltip('timestamp:T', title='Thời gian', format='%Y-%m-%d %H:%M:%S'),
            alt.Tooltip('name:N', title='Tân binh'),
            alt.Tooltip('votes:Q', title='Tỉ lệ bình chọn (%)', format='.2f')
        ]
    ).properties(
        height=500,
        width="container",  # Optional: auto-width to match page layout
    ).interactive()

    st.altair_chart(line_chart, use_container_width=True)

   # Prepare DataFrame for display and export
    st.subheader("📋 Toàn bộ dữ liệu bình chọn")
    sorted_df = df.sort_values(by='timestamp', ascending=False)[['timestamp', 'name', 'votes']]
    sorted_df['votes'] = sorted_df['votes'].map('{:.2f}'.format)
    sorted_df['timestamp'] = sorted_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Show styled DataFrame
    st.dataframe(sorted_df.rename(columns={'votes': 'Tỉ lệ bình chọn (%)','name': 'Tân binh', 'timestamp': 'Thời gian'}), hide_index=True, use_container_width=True)

    # Add CSV Export Button
    @st.cache_data
    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')

    csv = convert_df_to_csv(sorted_df)

    st.download_button(
        label="⬇️ Lưu dữ liệu dưới định dạng CSV",
        data=csv,
        file_name='voting_results_export.csv',
        mime='text/csv'
    )

else:
    st.warning("⚠️ No data found yet. Make sure the scraper is running and sending data.")