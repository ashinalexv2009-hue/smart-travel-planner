from flask import Flask, render_template, request
import mysql.connector
import os
from math import radians, sin, cos, sqrt, atan2
app = Flask(__name__)

# ==========================================================
# DATABASE
# ==========================================================

def connect_database():

    try:

        conn = mysql.connector.connect(
            host=os.environ.get("MYSQL_HOST", "localhost"),
            user=os.environ.get("MYSQL_USER", "root"),
            password=os.environ.get("MYSQL_PASSWORD"),
            database=os.environ.get("MYSQL_DATABASE", "smart_travel"),
            port=int(os.environ.get("MYSQL_PORT", "3306"))
        )

        return conn

    except mysql.connector.Error:

        return None


# ==========================================================
# INDIAN CITY COORDINATES
# ==========================================================

INDIAN_CITIES = {

    "kochi": (9.9312, 76.2673),
    "thrissur": (10.5276, 76.2144),
    "trivandrum": (8.5241, 76.9366),
    "thiruvananthapuram": (8.5241, 76.9366),
    "kozhikode": (11.2588, 75.7804),
    "kannur": (11.8745, 75.3704),
    "kollam": (8.8932, 76.6141),
    "alappuzha": (9.4981, 76.3388),
    "kottayam": (9.5916, 76.5222),
    "palakkad": (10.7867, 76.6548),

    "mumbai": (19.0760, 72.8777),
    "delhi": (28.6139, 77.2090),
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "chennai": (13.0827, 80.2707),
    "hyderabad": (17.3850, 78.4867),
    "pune": (18.5204, 73.8567),
    "jaipur": (26.9124, 75.7873),
    "agra": (27.1767, 78.0081),
    "ahmedabad": (23.0225, 72.5714),
    "surat": (21.1702, 72.8311),
    "lucknow": (26.8467, 80.9462),
    "patna": (25.5941, 85.1376),
    "kolkata": (22.5726, 88.3639),
    "bhopal": (23.2599, 77.4126),
    "indore": (22.7196, 75.8577),
    "nagpur": (21.1458, 79.0882),
    "chandigarh": (30.7333, 76.7794),
    "amritsar": (31.6340, 74.8723),
    "varanasi": (25.3176, 82.9739),
    "dehradun": (30.3165, 78.0322),
    "rishikesh": (30.0869, 78.2676),
    "shimla": (31.1048, 77.1734),
    "manali": (32.2396, 77.1887),
    "srinagar": (34.0837, 74.7973),
    "mysore": (12.2958, 76.6394),
    "mysuru": (12.2958, 76.6394),
    "pondicherry": (11.9416, 79.8083),
    "darjeeling": (27.0410, 88.2663),
    "goa": (15.4909, 73.8278),
    "panaji": (15.4909, 73.8278)
}


# ==========================================================
# CALCULATE DISTANCE
# ==========================================================

def calculate_distance(start_city, destination):

    start_key = start_city.strip().lower()
    destination_key = destination.strip().lower()

    if start_key in INDIAN_CITIES:

        lat1, lon1 = INDIAN_CITIES[start_key]

    else:

        return None


    if destination_key in INDIAN_CITIES:

        lat2, lon2 = INDIAN_CITIES[destination_key]

    else:

        conn = connect_database()

        if conn is None:
            return None

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT latitude, longitude
            FROM cities
            WHERE LOWER(city) = LOWER(%s)
            """,
            (destination,)
        )

        end = cursor.fetchone()

        cursor.close()
        conn.close()

        if end is None:
            return None

        lat2, lon2 = end


    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))

    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))


    dlat = lat2 - lat1
    dlon = lon2 - lon1


    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )


    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )


    radius = 6371

    return radius * c


# ==========================================================
# HOME
# ==========================================================

@app.route("/")
def home():

    return render_template("index.html")


# ==========================================================
# PLAN PAGE
# ==========================================================

@app.route("/plan")
def plan():

    return render_template("plan.html")


# ==========================================================
# EXPLORE PAGE
# ==========================================================

@app.route("/explore")
def explore():

    conn = connect_database()

    if conn is None:
        return "Database connection failed."

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT city, attraction, hotel_cost
        FROM destinations
        ORDER BY city
    """)

    destinations = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "explore.html",
        destinations=destinations
    )

# ==========================================================
# SEARCH DESTINATION
# ==========================================================

@app.route("/search")
def search():

    query = request.args.get("q", "").strip()

    conn = connect_database()

    if conn is None:
        return "Database connection failed."

    cursor = conn.cursor(dictionary=True)

    if query:

        cursor.execute("""
            SELECT city, attraction, hotel_cost
            FROM destinations
            WHERE LOWER(city) LIKE LOWER(%s)
            ORDER BY city
        """, ("%" + query + "%",))

    else:

        cursor.execute("""
            SELECT city, attraction, hotel_cost
            FROM destinations
            ORDER BY city
        """)

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "search.html",
        results=results,
        query=query
    )

# ==========================================================
# DESTINATION DETAILS
# ==========================================================

@app.route("/destination/<city>")
def destination_details(city):

    conn = connect_database()

    if conn is None:
        return "Database connection failed."

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT city, attraction, hotel_cost
        FROM destinations
        WHERE LOWER(city) = LOWER(%s)
    """, (city,))

    destination = cursor.fetchone()

    cursor.close()
    conn.close()

    if destination is None:
        return "Destination not found."

    return render_template(
        "destination.html",
        destination=destination
    )

# ==========================================================
# CALCULATE TRIP
# ==========================================================

@app.route("/calculate", methods=["POST"])
def calculate():

    start_city = request.form["start_city"]

    destination = request.form["destination"]

    travelers = int(request.form["travelers"])

    days = int(request.form["days"])


    # Find distance

    distance = calculate_distance(
        start_city,
        destination
    )


    if distance is None:

        return "Starting city not found."


    # ======================================================
    # TRAVEL COST
    # ======================================================

    cost_per_km = 1.5

    round_trip_distance = distance * 2

    travel = round_trip_distance * cost_per_km

    total_travel = travel * travelers


    # ======================================================
    # HOTEL COST
    # ======================================================

    conn = connect_database()

    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT hotel_cost
        FROM destinations
        WHERE LOWER(city) = LOWER(%s)
        """,
        (destination,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()


    if result is None:

        return "Destination not found."


    hotel = result["hotel_cost"]

    total_hotel = hotel * days


    # ======================================================
    # TOTAL
    # ======================================================

    total = total_travel + total_hotel


    return render_template(
        "result.html",
        start_city=start_city,
        destination=destination,
        travelers=travelers,
        days=days,
        distance=round(distance, 1),
        travel_cost=round(total_travel),
        hotel_cost=round(total_hotel),
        total=round(total)
    )


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    app.run(debug=True)
