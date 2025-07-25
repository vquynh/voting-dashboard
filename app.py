from flask import Flask, request, jsonify
import psycopg2
import os
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)


# Load DB URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "your_supabase_connection_string")

def init_db():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS votes_debut (
                    id SERIAL PRIMARY KEY,
                    timestamp TEXT,
                    name TEXT,
                    votes DECIMAL(10, 2)
                )
            ''')
        conn.commit()

@app.route('/api/submit-votes', methods=['POST'])
def receive_votes():
    data = request.get_json()
    if not data or 'results' not in data:
        return jsonify({"error": "Invalid data"}), 400

    timestamp = data.get("timestamp", datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat())
    
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            for candidate in data['results']:
                cur.execute('''
                    INSERT INTO votes_debut (timestamp, name, votes)
                    VALUES (%s, %s, %s)
                ''', (timestamp, candidate['name'], candidate['votes']))
            conn.commit()

    if len(data['results'])!=0:
        return jsonify({
        "message": "Data saved successfully",
        "total_candidates": len(data['results']),
        "timestamp": timestamp
    }), 200
    else:
        return jsonify({
        "message": "No data to be saved"
    }), 204    
    

if __name__ == '__main__':
    init_db()
    app.run(debug=True)