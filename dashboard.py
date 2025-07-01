import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "voting_results.db"

@st.cache_data(ttl=60)  # Refresh every 60 seconds
def load_data():
    with sqlite3.connect(DB_NAME) as conn:
        query = '''
            SELECT timestamp, name, votes
            FROM votes
            ORDER BY timestamp DESC, votes DESC
        '''
        df = pd.read_sql(query, conn)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df

st.title("📈 Voting Results Dashboard")

df = load_data()

if df.empty:
    st.warning("No data found yet. Try running the scraper.")
else:
    latest_time = df['timestamp'].max().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"### Latest Results (Updated: {latest_time})")

    # Pivot data to show names over time
    pivot_df = df.pivot(index='timestamp', columns='name', values='votes').fillna(0)

    st.line_chart(pivot_df)

    st.bar_chart(df.groupby('name')['votes'].max())

    st.subheader("Raw Data")
    st.dataframe(df)