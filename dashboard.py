import streamlit as st
import psycopg2
import pandas as pd
import os
import altair as alt
#  Literal["black", "silver", "gray", "white", "maroon", "red", "purple", "fuchsia", "green", "lime", "olive", "yellow", "navy", "blue", "teal", "aqua", "orange", "aliceblue", "antiquewhite", "aquamarine", "azure", "beige", "bisque", "blanchedalmond", "blueviolet", "brown", "burlywood", "cadetblue", "chartreuse", "chocolate", "coral", "cornflowerblue", "cornsilk", "crimson", "cyan", "darkblue", "darkcyan", "darkgoldenrod", "darkgray", "darkgreen", "darkgrey", "darkkhaki", "darkmagenta", "darkolivegreen", "darkorange", "darkorchid", "darkred", "darksalmon", "darkseagreen", "darkslateblue", "darkslategray", "darkslategrey", "darkturquoise", "darkviolet", "deeppink", "deepskyblue", "dimgray", "dimgrey", "dodgerblue", "firebrick", "floralwhite", "forestgreen", "gainsboro", "ghostwhite", "gold", "goldenrod", "greenyellow", "grey", "honeydew", "hotpink", "indianred", "indigo", "ivory", "khaki", "lavender", "lavenderblush", "lawngreen", "lemonchiffon", "lightblue", "lightcoral", "lightcyan", "lightgoldenrodyellow", "lightgray", "lightgreen", "lightgrey", "lightpink", "lightsalmon", "lightseagreen", "lightskyblue", "lightslategray", "lightslategrey", "lightsteelblue", "lightyellow", "limegreen", "linen", "magenta", "mediumaquamarine", "mediumblue", "mediumorchid", "mediumpurple", "mediumseagreen", "mediumslateblue", "mediumspringgreen", "mediumturquoise", "mediumvioletred", "midnightblue", "mintcream", "mistyrose", "moccasin", "navajowhite", "oldlace", "olivedrab", "orangered", "orchid", "palegoldenrod", "palegreen", "paleturquoise", "palevioletred", "papayawhip", "peachpuff", "peru", "pink", "plum", "powderblue", "rosybrown", "royalblue", "saddlebrown", "salmon", "sandybrown", "seagreen", "seashell", "sienna", "skyblue", "slateblue", "slategray", "slategrey", "snow", "springgreen", "steelblue", "tan", "thistle", "tomato", "turquoise", "violet", "wheat", "whitesmoke", "yellowgreen", "rebeccapurple"]
name_color_map = {
    "Lê Duy Lân": "#1f77b4",    # Blue
    "Lê Phạm Minh Quân": "#ff7f0e",      # Orange
    "Nguyễn Thanh Phúc Nguyên": "#2ca02c",  # Green
    "Hồ Đông Quan": "#b21218",    # Red
    "Nguyễn Văn Liêm": "#9467bd",      # Purple
    "Đặng Đức Duy": "#8c564b",    # Brown
    "Nguyễn Lâm Anh": "#fbb5bd",    # Pink
    "Phạm Văn Tâm": "#7f7f7f",    # Gray
    "Thái Lê Minh Hiếu": "#bcbd22",     # Yellow-Green
    "Nguyễn Phi Long": "#17becf",     # Cyan
    "Bạch Hồng Cường": "#fb7f60",  # Light Red
    "Nguyễn Hữu Sơn": "silver",
    "Lê Bin Thế Vĩ": "#98df8a",   # Light Green
    "Tạ Hoàng Long": "yellow",    # Light Red
    "Nguyễn Văn Khang": "#c5b0d5",    # Light Purple
    "Đỗ Minh Tân": "#c49c94",    # Light Brown
}

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
    latest_time = df['timestamp'].max()
    latest_timestamp = latest_time.strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"#### 🕒 Kết quả mới nhất (cập nhật lúc: {latest_timestamp})")

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
    st.subheader("🏆 Xếp hạng hiện tại")

    bar_chart = alt.Chart(latest_votes_sorted).mark_bar(
        tooltip=True
    ).encode(
        x=alt.X('name:N', sort='-y',
            axis=alt.Axis(
            labelAngle=-45,      # ← Rotate labels 45 degrees
            labelLimit=200,      # ← Allow longer labels
            labelOverlap=False,   # ← Prevent overlapping
            title=None,
            )),
        y=alt.Y('votes:Q', title='Tỉ lệ bình chọn (%)'),
        color=alt.condition(
            alt.datum.rank <= 3,
            alt.value('#28a745'),  # Green for top 3
            alt.value('#4e79a7') ,  # Default blue
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
    sorted_names = latest_votes_sorted['name'].tolist()
    colors_by_names = [name_color_map.get(name, '#4e79a7') for name in sorted_names]  # Default to blue if not found

    # Sort and prepare data
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
    df_chart = df.sort_values(by='timestamp')

    # Build the chart
    line_chart = alt.Chart(df_chart).mark_line(
        point=False,
        interpolate='catmull-rom'  # ← Smooth interpolation
    ).encode(
        x=alt.X('timestamp:T', title='Thời gian'),
        y=alt.Y('votes:Q', title='Tỉ lệ bình chọn (%)'),
        color=alt.Color('name:N', title='Tân binh',scale=alt.Scale(domain=sorted_names, range=colors_by_names),
            sort=None,
            legend=alt.Legend(
                orient='bottom',         # ← Move legend to the right
                direction= 'vertical',  # ← Horizontal layout
                labelLimit = 200,
                title=None,
                # ← No title for the legend
            )),
        tooltip=[
            alt.Tooltip('timestamp:T', title='Thời gian', format='%Y-%m-%d %H:%M:%S'),
            alt.Tooltip('name:N', title='Tân binh'),
            alt.Tooltip('votes:Q', title='Tỉ lệ bình chọn (%)', format='.2f')
        ]
    ).properties(
        height=1000,
        width="container"
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