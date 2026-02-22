from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)
# -----------------------------------
# Database Initialization
# -----------------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS waste_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            waste_type TEXT,
            quantity REAL,
            date TEXT,
            category TEXT,
            spike_status TEXT,
            recommendation TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()



def classify_waste(waste_type):
    recyclable = ["plastic", "metal", "paper"]
    hazardous = ["chemical", "battery"]

    if waste_type.lower() in recyclable:
        return "Recyclable"
    elif waste_type.lower() in hazardous:
        return "Hazardous"
    else:
        return "General Waste"



def check_spike(quantity):
    if quantity > 100:
        return "⚠ Hazardous Spike Detected"
    return "Normal"



def recommend(category):
    if category == "Recyclable":
        return "Send to recycling partner"
    elif category == "Hazardous":
        return "Immediate inspection required"
    else:
        return "Reduce waste generation process"


# -----------------------------------
# Home Route
# -----------------------------------
@app.route("/")
def home():
    return "EcoLoop AI Backend Running!"


# -----------------------------------
# Upload Waste API
# -----------------------------------
@app.route("/upload-waste", methods=["POST"])
def upload_waste():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    required_fields = [ "waste_type", "quantity", "date"]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400


    waste_type = data["waste_type"]
    quantity = data["quantity"]
    date = data["date"]

    # Apply AI Logic
    category = classify_waste(waste_type)
    spike_status = check_spike(quantity)
    recommendation = recommend(category)

    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO waste_records 
            ( waste_type, quantity, date, category, spike_status, recommendation)
            VALUES ( ?, ?, ?, ?, ?, ?)
        """, ( waste_type, quantity, date, category, spike_status, recommendation))

        conn.commit()
        conn.close()

        return jsonify({
            "message": "Waste data saved successfully!",
            "category": category,
            "spike_status": spike_status,
            "recommendation": recommendation
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/dashboard-data", methods=["GET"])
def dashboard_data():
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT waste_type, SUM(quantity)
            FROM waste_records
            GROUP BY waste_type
        """)

        data = cursor.fetchall()
        conn.close()

        result = [
            {"waste_type": row[0], "total_quantity": row[1]}
            for row in data
        ]

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------
# Run App
# -----------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)