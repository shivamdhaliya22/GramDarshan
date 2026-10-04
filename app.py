from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "gramdarshan_secret_key"

DATABASE = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():

    conn = get_db_connection()

    # ==============================
    # Villages Table
    # ==============================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS villages (
            village_id INTEGER PRIMARY KEY AUTOINCREMENT,
            village_name TEXT NOT NULL,
            location TEXT,
            population INTEGER,
            facilities TEXT
        )
    """)

    # ==============================
    # Users Table
    # ==============================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            village_id INTEGER,
            is_admin INTEGER DEFAULT 0,
            FOREIGN KEY (village_id)
            REFERENCES villages(village_id)
        )
    """)

    # ==============================
    # History Table
    # ==============================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            village_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            source TEXT,
            FOREIGN KEY (village_id)
            REFERENCES villages(village_id)
        )
    """)

    # ==============================
    # Heritage Places Table
    # ==============================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS heritage_places (
            heritage_id INTEGER PRIMARY KEY AUTOINCREMENT,
            village_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            location TEXT,
            photo TEXT,
            source TEXT,
            FOREIGN KEY (village_id)
            REFERENCES villages(village_id)
        )
    """)

    # ==============================
    # Schemes Table
    # ==============================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS schemes (
            scheme_id INTEGER PRIMARY KEY AUTOINCREMENT,
            village_id INTEGER,
            scheme_name TEXT NOT NULL,
            purpose TEXT,
            eligibility TEXT,
            benefits TEXT,
            FOREIGN KEY (village_id)
            REFERENCES villages(village_id)
        )
    """)

    # ==============================
    # Complaints Table
    # ==============================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            village_id INTEGER,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            photo TEXT,
            status TEXT DEFAULT 'Submitted',
            FOREIGN KEY (user_id)
            REFERENCES users(user_id),
            FOREIGN KEY (village_id)
            REFERENCES villages(village_id)
        )
    """)

    # ==============================
    # Notices Table
    # ==============================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            notice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            village_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT,
            FOREIGN KEY (village_id)
            REFERENCES villages(village_id)
        )
    """)

    # ==============================
    # Development Projects Table
    # ==============================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS development_projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            village_id INTEGER,
            project_name TEXT NOT NULL,
            location TEXT,
            description TEXT,
            status TEXT,
            FOREIGN KEY (village_id)
            REFERENCES villages(village_id)
        )
    """)

    # ==============================
    # Default Villages
    # ==============================

    village_count = conn.execute(
        "SELECT COUNT(*) FROM villages"
    ).fetchone()[0]

    if village_count == 0:

        villages = [
            (
                "Gangol",
                "Meerut, Uttar Pradesh",
                0,
                "School, Panchayat, Health Centre"
            ),
            (
                "Village 2",
                "Meerut, Uttar Pradesh",
                0,
                "School, Panchayat"
            ),
            (
                "Village 3",
                "Meerut, Uttar Pradesh",
                0,
                "School, Panchayat"
            )
        ]

        conn.executemany("""
            INSERT INTO villages
            (village_name, location, population, facilities)
            VALUES (?, ?, ?, ?)
        """, villages)

    # ==============================
    # Default Admin
    # ==============================

    admin_exists = conn.execute("""
        SELECT * FROM users
        WHERE email = ?
    """, ("admin@gramdarshan.com",)).fetchone()

    if not admin_exists:

        conn.execute("""
            INSERT INTO users
            (name, email, password, village_id, is_admin)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "GramDarshan Admin",
            "admin@gramdarshan.com",
            "admin123",
            1,
            1
        ))

    conn.commit()
    conn.close()


# ==============================
# Home
# ==============================

@app.route("/")
def home():

    conn = get_db_connection()

    villages = conn.execute("""
        SELECT * FROM villages
    """).fetchall()

    conn.close()

    return render_template(
        "home.html",
        villages=villages
    )


# ==============================
# Register
# ==============================

@app.route("/register", methods=["GET", "POST"])
def register():

    conn = get_db_connection()

    villages = conn.execute("""
        SELECT * FROM villages
    """).fetchall()

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        village_id = request.form["village_id"]

        try:

            conn.execute("""
                INSERT INTO users
                (name, email, password, village_id)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                email,
                password,
                village_id
            ))

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "register.html",
                villages=villages,
                error="Email already registered."
            )

    conn.close()

    return render_template(
        "register.html",
        villages=villages
    )


# ==============================
# Login
# ==============================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute("""
            SELECT * FROM users
            WHERE email = ?
            AND password = ?
        """, (
            email,
            password
        )).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["user_id"]
            session["name"] = user["name"]
            session["village_id"] = user["village_id"]
            session["is_admin"] = user["is_admin"]

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


# ==============================
# My Village
# ==============================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    village = conn.execute("""
        SELECT * FROM villages
        WHERE village_id = ?
    """, (
        session["village_id"],
    )).fetchone()

    conn.close()

    return render_template(
        "village.html",
        village=village
    )


# ==============================
# History & Heritage
# ==============================

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    village_id = session["village_id"]

    village = conn.execute("""
        SELECT * FROM villages
        WHERE village_id = ?
    """, (
        village_id,
    )).fetchone()

    history_records = conn.execute("""
        SELECT * FROM history
        WHERE village_id = ?
    """, (
        village_id,
    )).fetchall()

    heritage_places = conn.execute("""
        SELECT * FROM heritage_places
        WHERE village_id = ?
    """, (
        village_id,
    )).fetchall()

    conn.close()

    return render_template(
        "history.html",
        village=village,
        history_records=history_records,
        heritage_places=heritage_places
    )


# ==============================
# Government Schemes
# ==============================

@app.route("/schemes")
def schemes():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    village_id = session["village_id"]

    village = conn.execute("""
        SELECT * FROM villages
        WHERE village_id = ?
    """, (
        village_id,
    )).fetchone()

    schemes_list = conn.execute("""
        SELECT * FROM schemes
        WHERE village_id = ?
    """, (
        village_id,
    )).fetchall()

    conn.close()

    return render_template(
        "schemes.html",
        village=village,
        schemes=schemes_list
    )


# ==============================
# Complaints
# ==============================

@app.route("/complaints", methods=["GET", "POST"])
def complaints():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    if request.method == "POST":

        category = request.form["category"]
        description = request.form["description"]

        conn.execute("""
            INSERT INTO complaints
            (
                user_id,
                village_id,
                category,
                description,
                status
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            session["village_id"],
            category,
            description,
            "Submitted"
        ))

        conn.commit()

    complaints_list = conn.execute("""
        SELECT * FROM complaints
        WHERE user_id = ?
        ORDER BY complaint_id DESC
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "complaints.html",
        complaints=complaints_list
    )


# ==============================
# Notices
# ==============================

@app.route("/notices")
def notices():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    village_id = session["village_id"]

    village = conn.execute("""
        SELECT * FROM villages
        WHERE village_id = ?
    """, (
        village_id,
    )).fetchone()

    notices_list = conn.execute("""
        SELECT * FROM notices
        WHERE village_id = ?
        ORDER BY notice_id DESC
    """, (
        village_id,
    )).fetchall()

    conn.close()

    return render_template(
        "notices.html",
        village=village,
        notices=notices_list
    )


# ==============================
# Development
# ==============================

@app.route("/development")
def development():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    village_id = session["village_id"]

    village = conn.execute("""
        SELECT * FROM villages
        WHERE village_id = ?
    """, (
        village_id,
    )).fetchone()

    projects = conn.execute("""
        SELECT * FROM development_projects
        WHERE village_id = ?
        ORDER BY project_id DESC
    """, (
        village_id,
    )).fetchall()

    conn.close()

    return render_template(
        "development.html",
        village=village,
        projects=projects
    )


# ==============================
# Admin Dashboard
# ==============================

@app.route("/admin")
def admin():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    user = conn.execute("""
        SELECT * FROM users
        WHERE user_id = ?
    """, (
        session["user_id"],
    )).fetchone()

    if not user or user["is_admin"] != 1:

        conn.close()

        return "Access denied."

    villages = conn.execute("""
        SELECT * FROM villages
    """).fetchall()

    complaints = conn.execute("""
        SELECT complaints.*, users.name
        FROM complaints
        JOIN users
        ON complaints.user_id = users.user_id
        ORDER BY complaint_id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        villages=villages,
        complaints=complaints
    )


# ==============================
# Update Complaint Status
# ==============================

@app.route(
    "/admin/update-complaint/<int:complaint_id>",
    methods=["POST"]
)
def update_complaint(complaint_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    user = conn.execute("""
        SELECT * FROM users
        WHERE user_id = ?
    """, (
        session["user_id"],
    )).fetchone()

    if not user or user["is_admin"] != 1:

        conn.close()

        return "Access denied."

    status = request.form["status"]

    conn.execute("""
        UPDATE complaints
        SET status = ?
        WHERE complaint_id = ?
    """, (
        status,
        complaint_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ==============================
# Add Notice
# ==============================

@app.route("/admin/add-notice", methods=["POST"])
def add_notice():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    user = conn.execute("""
        SELECT * FROM users
        WHERE user_id = ?
    """, (
        session["user_id"],
    )).fetchone()

    if not user or user["is_admin"] != 1:

        conn.close()

        return "Access denied."

    village_id = request.form["village_id"]
    title = request.form["title"]
    description = request.form["description"]
    date = request.form["date"]

    conn.execute("""
        INSERT INTO notices
        (
            village_id,
            title,
            description,
            date
        )
        VALUES (?, ?, ?, ?)
    """, (
        village_id,
        title,
        description,
        date
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ==============================
# Add Government Scheme
# ==============================

@app.route("/admin/add-scheme", methods=["POST"])
def add_scheme():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    user = conn.execute("""
        SELECT * FROM users
        WHERE user_id = ?
    """, (
        session["user_id"],
    )).fetchone()

    if not user or user["is_admin"] != 1:

        conn.close()

        return "Access denied."

    village_id = request.form["village_id"]
    scheme_name = request.form["scheme_name"]
    purpose = request.form["purpose"]
    eligibility = request.form["eligibility"]
    benefits = request.form["benefits"]

    conn.execute("""
        INSERT INTO schemes
        (
            village_id,
            scheme_name,
            purpose,
            eligibility,
            benefits
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        village_id,
        scheme_name,
        purpose,
        eligibility,
        benefits
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ==============================
# Add Development Project
# ==============================

@app.route("/admin/add-development", methods=["POST"])
def add_development():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    user = conn.execute("""
        SELECT * FROM users
        WHERE user_id = ?
    """, (
        session["user_id"],
    )).fetchone()

    if not user or user["is_admin"] != 1:

        conn.close()

        return "Access denied."

    village_id = request.form["village_id"]
    project_name = request.form["project_name"]
    location = request.form["location"]
    description = request.form["description"]
    status = request.form["status"]

    conn.execute("""
        INSERT INTO development_projects
        (
            village_id,
            project_name,
            location,
            description,
            status
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        village_id,
        project_name,
        location,
        description,
        status
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ==============================
# Logout
# ==============================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# ==============================
# Initialize Database
# ==============================

# This runs when Flask starts locally
# and also when Gunicorn starts the app on Render.
init_database()


# ==============================
# Run Application
# ==============================

if __name__ == "__main__":

    app.run(debug=True)