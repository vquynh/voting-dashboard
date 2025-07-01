import streamlit as st
import psycopg2
import pandas as pd
import os

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
st.title("📊 Voting Results Dashboard")

# Load data
df = load_data()

# Show latest update time
if not df.empty:
    latest_time = df['timestamp'].max().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"### 🕒 Latest Results (Updated: {latest_time})")

    # Get most recent vote per candidate
    latest_votes = df.loc[df.groupby('name')['timestamp'].idxmax()]

    # ✅ Sort by votes descending before any visualization
    latest_votes_sorted = latest_votes.sort_values(by='votes', ascending=False).copy()

    # 🔥 Ensure index order is preserved when plotting
    latest_votes_sorted.reset_index(drop=True, inplace=True)

    # Bar chart - sorted descending
    st.subheader("🏆 Current Rankings (Sorted Descending)")
    st.bar_chart(latest_votes_sorted.set_index('name')[['votes']].style.format("{:.2f}"))

    # Line chart - vote trends over time (still unsorted, that's OK)
    st.subheader("📈 Vote Trends Over Time")
    pivot_df = df.pivot(index='timestamp', columns='name', values='votes').fillna(0)
    st.line_chart(pivot_df)

    # Raw data table - sorted by vote descending
    st.subheader("📋 Raw Data (Sorted by Votes Descending)")
    st.dataframe(
        df.loc[df['name'].isin(latest_votes_sorted['name'])]
        .drop_duplicates(subset=['name'], keep='last')
        .sort_values(by='votes', ascending=False)
        .reset_index(drop=True)
        [['name', 'votes']]
        .style.format({"votes": "{:.2f}"})
    )

else:
    st.warning("⚠️ No data found yet. Make sure the scraper is running and sending data.")