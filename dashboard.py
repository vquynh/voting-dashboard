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

    # Pivot data to show names over time
    pivot_df = df.pivot(index='timestamp', columns='name', values='votes').fillna(0)

    # Line chart - vote trends over time
    st.subheader("📈 Vote Trends Over Time")
    st.line_chart(pivot_df)

    # Bar chart - current vote counts
    st.subheader("📊 Current Vote Totals")
    latest_votes = df.loc[df.groupby('name')['timestamp'].idxmax()][['name', 'votes']]
    st.bar_chart(latest_votes.set_index('name'))

    # Raw data table
    st.subheader("📋 Raw Data")
    st.dataframe(df.sort_values(by='timestamp', ascending=False))

else:
    st.warning("⚠️ No data found yet. Make sure the scraper is running and sending data.")