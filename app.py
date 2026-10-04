from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "gramdarshan_secret_key_change_later"

DATABASE = "database.db"


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ==================================================
# DATABASE INITIALIZATION + SAFE MIGRATIONS
# ==================================================

def init_database():

    conn = get_db_connection()

    # --------------------------------------------------
    # VILLAGES
    # --------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS villages (
            village_id INTEGER PRIMARY KEY AUTOINCREMENT,
            village_name TEXT NOT NULL,
            location TEXT,
            population INTEGER,
            facilities TEXT
        )
    """)

    # --------------------------------------------------
    # USERS
    # --------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            village_id INTEGER,
            is_admin INTEGER DEFAULT 0,
            FOREIGN KEY (village_id) REFERENCES villages(village_id)
        )
    """)

    # --------------------------------------------------
    # HISTORY
    # --------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            village_id INTEGER,
            title TEXT,
            content TEXT,
            FOREIGN KEY (village_id) REFERENCES villages(village_id)
        )
    """)

    # --------------------------------------------------
    # HERITAGE PLACES
    # --------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS heritage_places (
            heritage_id INTEGER PRIMARY KEY AUTOINCREMENT,
            village_id INTEGER,
            name TEXT,
            description TEXT,
            FOREIGN KEY (village_id) REFERENCES villages(village_id)
        )
    """)

    # --------------------------------------------------
    # SCHEMES
    # --------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS schemes (
            scheme_id INTEGER PRIMARY KEY AUTOINCREMENT,
            village_id INTEGER,
            scheme_name TEXT,
            purpose TEXT,
            eligibility TEXT,
            benefits TEXT,
            FOREIGN KEY (village_id) REFERENCES villages(village_id)
        )
    """)

    # --------------------------------------------------
    # COMPLAINTS
    # --------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            village_id INTEGER,
            category TEXT,
            description TEXT,
            status TEXT DEFAULT 'Submitted',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (village_id) REFERENCES villages(village_id)
        )
    """)

    # --------------------------------------------------
    # NOTICES
    # --------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            notice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            village_id INTEGER,
            title TEXT,
            content TEXT,
            notice_date TEXT,
            FOREIGN KEY (village_id) REFERENCES villages(village_id)
        )
    """)

    # --------------------------------------------------
    # DEVELOPMENT PROJECTS
    # --------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS development_projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            village_id INTEGER,
            project_name TEXT NOT NULL,
            location TEXT,
            description TEXT,
            status TEXT
        )
    """)

    # ==================================================
    # SAFE MIGRATIONS
    # ==================================================

    # --------------------------------------------------
    # VILLAGES MIGRATION
    # --------------------------------------------------

    village_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(villages)"
        ).fetchall()
    ]

    village_migrations = {
        "district": "TEXT",
        "tehsil": "TEXT",
        "block": "TEXT",
        "panchayat": "TEXT",
        "pin_code": "TEXT",
        "area": "REAL",
        "households": "INTEGER DEFAULT 0",
        "estimated_population": "INTEGER DEFAULT 0",
        "description": "TEXT"
    }

    for column, column_type in village_migrations.items():

        if column not in village_columns:

            conn.execute(
                f"ALTER TABLE villages ADD COLUMN {column} {column_type}"
            )

    # --------------------------------------------------
    # SCHEMES MIGRATION
    # --------------------------------------------------

    scheme_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(schemes)"
        ).fetchall()
    ]

    if "source" not in scheme_columns:

        conn.execute(
            "ALTER TABLE schemes ADD COLUMN source TEXT"
        )

    # --------------------------------------------------
    # NOTICES MIGRATION
    # --------------------------------------------------

    notice_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(notices)"
        ).fetchall()
    ]

    if "content" not in notice_columns:

        conn.execute(
            "ALTER TABLE notices ADD COLUMN content TEXT"
        )

    if "notice_date" not in notice_columns:

        conn.execute(
            "ALTER TABLE notices ADD COLUMN notice_date TEXT"
        )

    # --------------------------------------------------
    # DEVELOPMENT MIGRATION
    # --------------------------------------------------

    development_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(development_projects)"
        ).fetchall()
    ]

    if "title" not in development_columns:

        conn.execute(
            "ALTER TABLE development_projects ADD COLUMN title TEXT"
        )

    if "location" not in development_columns:

        conn.execute(
            "ALTER TABLE development_projects ADD COLUMN location TEXT"
        )

    if "description" not in development_columns:

        conn.execute(
            "ALTER TABLE development_projects ADD COLUMN description TEXT"
        )

    if "status" not in development_columns:

        conn.execute(
            "ALTER TABLE development_projects ADD COLUMN status TEXT"
        )

    # --------------------------------------------------
    # SYNCHRONIZE OLD DEVELOPMENT DATA
    # --------------------------------------------------

    conn.execute("""
        UPDATE development_projects
        SET title = project_name
        WHERE
            (title IS NULL OR title = '')
            AND project_name IS NOT NULL
    """)

    conn.execute("""
        UPDATE development_projects
        SET project_name = title
        WHERE
            (project_name IS NULL OR project_name = '')
            AND title IS NOT NULL
            AND title != ''
    """)

    # ==================================================
    # DEFAULT VILLAGES
    # ==================================================

    village_count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM villages
    """).fetchone()["count"]

    if village_count == 0:

        conn.execute("""
            INSERT INTO villages
            (
                village_name,
                location,
                population,
                facilities,
                district,
                tehsil,
                block,
                panchayat,
                pin_code,
                area,
                households,
                estimated_population,
                description
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Gangol",
            "Meerut, Uttar Pradesh",
            7673,
            "School, Panchayat, Health Centre",
            "Meerut",
            "",
            "",
            "Gagaul",
            "245206",
            901.81,
            0,
            0,
            "Village information will be maintained through the GramDarshan admin dashboard."
        ))

        conn.execute("""
            INSERT INTO villages
            (
                village_name,
                location,
                population,
                facilities,
                district,
                description
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Village 2",
            "Meerut, Uttar Pradesh",
            0,
            "",
            "Meerut",
            "Village information will be added by the administrator."
        ))

        conn.execute("""
            INSERT INTO villages
            (
                village_name,
                location,
                population,
                facilities,
                district,
                description
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Village 3",
            "Meerut, Uttar Pradesh",
            0,
            "",
            "Meerut",
            "Village information will be added by the administrator."
        ))

    # ==================================================
    # DEFAULT ADMIN
    # ==================================================

    admin_count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM users
        WHERE is_admin = 1
    """).fetchone()["count"]

    if admin_count == 0:

        hashed_password = generate_password_hash("admin123")

        conn.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                village_id,
                is_admin
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            "GramDarshan Admin",
            "admin@gramdarshan.com",
            hashed_password,
            1,
            1
        ))

    conn.commit()
    conn.close()


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():

    conn = get_db_connection()

    villages = conn.execute("""
        SELECT *
        FROM villages
        ORDER BY village_id
    """).fetchall()

    conn.close()

    return render_template(
        "home.html",
        villages=villages
    )


# ==================================================
# REGISTER
# ==================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    conn = get_db_connection()

    villages = conn.execute("""
        SELECT *
        FROM villages
        ORDER BY village_name
    """).fetchall()

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        village_id = request.form["village_id"]

        existing_user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        if existing_user:

            conn.close()

            return render_template(
                "register.html",
                villages=villages,
                error="Email already registered."
            )

        hashed_password = generate_password_hash(password)

        conn.execute("""
            INSERT INTO users
            (
                name,
                email,
                password,
                village_id,
                is_admin
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            email,
            hashed_password,
            village_id,
            0
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    conn.close()

    return render_template(
        "register.html",
        villages=villages
    )


# ==================================================
# LOGIN
# ==================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["user_id"]
            session["user_name"] = user["name"]
            session["village_id"] = user["village_id"]
            session["is_admin"] = user["is_admin"]

            if user["is_admin"] == 1:

                return redirect(url_for("admin"))

            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


# ==================================================
# DASHBOARD / MY VILLAGE
# ==================================================

@app.route("/dashboard")
def dashboard():

    if not session.get("user_id"):

        return redirect(url_for("login"))

    village_id = session.get("village_id")

    conn = get_db_connection()

    village = conn.execute("""
        SELECT *
        FROM villages
        WHERE village_id = ?
    """, (village_id,)).fetchone()

    conn.close()

    return render_template(
        "village.html",
        village=village
    )


# ==================================================
# HISTORY
# ==================================================

@app.route("/history")
def history():

    if not session.get("user_id"):

        return redirect(url_for("login"))

    village_id = session.get("village_id")

    conn = get_db_connection()

    village = conn.execute("""
        SELECT *
        FROM villages
        WHERE village_id = ?
    """, (village_id,)).fetchone()

    history_items = conn.execute("""
        SELECT *
        FROM history
        WHERE village_id = ?
        ORDER BY history_id DESC
    """, (village_id,)).fetchall()

    heritage_places = conn.execute("""
        SELECT *
        FROM heritage_places
        WHERE village_id = ?
        ORDER BY heritage_id DESC
    """, (village_id,)).fetchall()

    conn.close()

    return render_template(
        "history.html",
        village=village,
        history=history_items,
        heritage_places=heritage_places
    )


# ==================================================
# GOVERNMENT SCHEMES
# ==================================================

@app.route("/schemes")
def schemes():

    if not session.get("user_id"):

        return redirect(url_for("login"))

    village_id = session.get("village_id")

    conn = get_db_connection()

    village = conn.execute("""
        SELECT *
        FROM villages
        WHERE village_id = ?
    """, (village_id,)).fetchone()

    schemes_list = conn.execute("""
        SELECT *
        FROM schemes
        WHERE village_id = ?
        ORDER BY scheme_id DESC
    """, (village_id,)).fetchall()

    conn.close()

    return render_template(
        "schemes.html",
        village=village,
        schemes=schemes_list
    )


# ==================================================
# COMPLAINTS
# ==================================================

@app.route("/complaints", methods=["GET", "POST"])
def complaints():

    if not session.get("user_id"):

        return redirect(url_for("login"))

    village_id = session.get("village_id")
    user_id = session.get("user_id")

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
            user_id,
            village_id,
            category,
            description,
            "Submitted"
        ))

        conn.commit()

    complaints_list = conn.execute("""
        SELECT *
        FROM complaints
        WHERE user_id = ?
        ORDER BY complaint_id DESC
    """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "complaints.html",
        complaints=complaints_list
    )


# ==================================================
# NOTICES
# ==================================================

@app.route("/notices")
def notices():

    if not session.get("user_id"):

        return redirect(url_for("login"))

    village_id = session.get("village_id")

    conn = get_db_connection()

    village = conn.execute("""
        SELECT *
        FROM villages
        WHERE village_id = ?
    """, (village_id,)).fetchone()

    notices_list = conn.execute("""
        SELECT *
        FROM notices
        WHERE village_id = ?
        ORDER BY notice_id DESC
    """, (village_id,)).fetchall()

    conn.close()

    return render_template(
        "notices.html",
        village=village,
        notices=notices_list
    )


# ==================================================
# DEVELOPMENT
# ==================================================

@app.route("/development")
def development():

    if not session.get("user_id"):

        return redirect(url_for("login"))

    village_id = session.get("village_id")

    conn = get_db_connection()

    village = conn.execute("""
        SELECT *
        FROM villages
        WHERE village_id = ?
    """, (village_id,)).fetchone()

    projects = conn.execute("""
        SELECT
            project_id,
            village_id,
            COALESCE(NULLIF(title, ''), project_name) AS title,
            project_name,
            location,
            description,
            status
        FROM development_projects
        WHERE village_id = ?
        ORDER BY project_id DESC
    """, (village_id,)).fetchall()

    conn.close()

    return render_template(
        "development.html",
        village=village,
        projects=projects
    )


# ==================================================
# ADMIN CHECK
# ==================================================

def is_admin():

    return session.get("is_admin") == 1


# ==================================================
# ADMIN DASHBOARD
# ==================================================

@app.route("/admin")
def admin():

    if not is_admin():

        return "Access denied."

    conn = get_db_connection()

    # --------------------------------------------------
    # VILLAGES
    # --------------------------------------------------

    villages = conn.execute("""
        SELECT *
        FROM villages
        ORDER BY village_id
    """).fetchall()

    # --------------------------------------------------
    # HISTORY
    # --------------------------------------------------

    history_items = conn.execute("""
        SELECT
            history.*,
            villages.village_name
        FROM history
        LEFT JOIN villages
        ON history.village_id = villages.village_id
        ORDER BY history.history_id DESC
    """).fetchall()

    # --------------------------------------------------
    # HERITAGE
    # --------------------------------------------------

    heritage_places = conn.execute("""
        SELECT
            heritage_places.*,
            villages.village_name
        FROM heritage_places
        LEFT JOIN villages
        ON heritage_places.village_id = villages.village_id
        ORDER BY heritage_places.heritage_id DESC
    """).fetchall()

    # --------------------------------------------------
    # SCHEMES
    # --------------------------------------------------

    schemes_list = conn.execute("""
        SELECT
            schemes.*,
            villages.village_name
        FROM schemes
        LEFT JOIN villages
        ON schemes.village_id = villages.village_id
        ORDER BY schemes.scheme_id DESC
    """).fetchall()

    # --------------------------------------------------
    # NOTICES
    # --------------------------------------------------

    notices_list = conn.execute("""
        SELECT
            notices.*,
            villages.village_name
        FROM notices
        LEFT JOIN villages
        ON notices.village_id = villages.village_id
        ORDER BY notices.notice_id DESC
    """).fetchall()

    # --------------------------------------------------
    # DEVELOPMENT
    # --------------------------------------------------

    projects = conn.execute("""
        SELECT
            development_projects.project_id,
            development_projects.village_id,
            COALESCE(
                NULLIF(development_projects.title, ''),
                development_projects.project_name
            ) AS title,
            development_projects.project_name,
            development_projects.location,
            development_projects.description,
            development_projects.status,
            villages.village_name
        FROM development_projects
        LEFT JOIN villages
        ON development_projects.village_id = villages.village_id
        ORDER BY development_projects.project_id DESC
    """).fetchall()

    # --------------------------------------------------
    # COMPLAINTS
    # --------------------------------------------------

    complaints_list = conn.execute("""
        SELECT
            complaints.*,
            users.name AS user_name,
            users.email,
            villages.village_name
        FROM complaints
        LEFT JOIN users
        ON complaints.user_id = users.user_id
        LEFT JOIN villages
        ON complaints.village_id = villages.village_id
        ORDER BY complaints.complaint_id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        villages=villages,
        history=history_items,
        heritage_places=heritage_places,
        schemes=schemes_list,
        notices=notices_list,
        projects=projects,
        complaints=complaints_list
    )


# ==================================================
# ADMIN - UPDATE VILLAGE
# ==================================================

@app.route(
    "/admin/update-village/<int:village_id>",
    methods=["POST"]
)
def update_village(village_id):

    if not is_admin():

        return "Access denied."

    conn = get_db_connection()

    village_name = request.form["village_name"]
    location = request.form.get("location", "")
    population = request.form.get("population", 0)
    facilities = request.form.get("facilities", "")

    district = request.form.get("district", "")
    tehsil = request.form.get("tehsil", "")
    block = request.form.get("block", "")
    panchayat = request.form.get("panchayat", "")
    pin_code = request.form.get("pin_code", "")
    area = request.form.get("area", 0)
    households = request.form.get("households", 0)

    estimated_population = request.form.get(
        "estimated_population",
        0
    )

    description = request.form.get(
        "description",
        ""
    )

    conn.execute("""
        UPDATE villages
        SET
            village_name = ?,
            location = ?,
            population = ?,
            facilities = ?,
            district = ?,
            tehsil = ?,
            block = ?,
            panchayat = ?,
            pin_code = ?,
            area = ?,
            households = ?,
            estimated_population = ?,
            description = ?
        WHERE village_id = ?
    """, (
        village_name,
        location,
        population,
        facilities,
        district,
        tehsil,
        block,
        panchayat,
        pin_code,
        area,
        households,
        estimated_population,
        description,
        village_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ==================================================
# ADMIN - ADD HISTORY
# ==================================================

@app.route(
    "/admin/add-history",
    methods=["POST"]
)
def add_history():

    if not is_admin():

        return "Access denied."

    village_id = request.form["village_id"]
    title = request.form["title"]
    content = request.form["content"]

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO history
        (
            village_id,
            title,
            content
        )
        VALUES (?, ?, ?)
    """, (
        village_id,
        title,
        content
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ==================================================
# ADMIN - DELETE HISTORY
# ==================================================

@app.route(
    "/admin/delete-history/<int:history_id>",
    methods=["POST"]
)
def delete_history(history_id):

    if not is_admin():

        return "Access denied."

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM history
        WHERE history_id = ?
    """, (history_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ==================================================
# ADMIN - ADD HERITAGE
# ==================================================

@app.route(
    "/admin/add-heritage",
    methods=["POST"]
)
def add_heritage():

    if not is_admin():

        return "Access denied."

    village_id = request.form["village_id"]
    name = request.form["name"]
    description = request.form["description"]

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO heritage_places
        (
            village_id,
            name,
            description
        )
        VALUES (?, ?, ?)
    """, (
        village_id,
        name,
        description
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ==================================================
# ADMIN - DELETE HERITAGE
# ==================================================

@app.route(
    "/admin/delete-heritage/<int:heritage_id>",
    methods=["POST"]
)
def delete_heritage(heritage_id):

    if not is_admin():

        return "Access denied."

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM heritage_places
        WHERE heritage_id = ?
    """, (heritage_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ==================================================
# ADMIN - ADD SCHEME
# ==================================================

@app.route(
    "/admin/add-scheme",
    methods=["POST"]
)
def add_scheme():

    if not is_admin():

        return "Access denied."

    village_id = request.form["village_id"]
    scheme_name = request.form["scheme_name"]

    purpose = request.form.get(
        "purpose",
        ""
    )

    eligibility = request.form.get(
        "eligibility",
        ""
    )

    benefits = request.form.get(
        "benefits",
        ""
    )

    source = request.form.get(
        "source",
        ""
    )

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO schemes
        (
            village_id,
            scheme_name,
            purpose,
            eligibility,
            benefits,
            source
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        village_id,
        scheme_name,
        purpose,
        eligibility,
        benefits,
        source
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ==================================================
# ADMIN - DELETE SCHEME
# ==================================================

@app.route(
    "/admin/delete-scheme/<int:scheme_id>",
    methods=["POST"]
)
def delete_scheme(scheme_id):

    if not is_admin():

        return "Access denied."

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM schemes
        WHERE scheme_id = ?
    """, (scheme_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ==================================================
# ADMIN - ADD NOTICE
# ==================================================

@app.route(
    "/admin/add-notice",
    methods=["POST"]
)
def add_notice():

    if not is_admin():

        return "Access denied."

    village_id = request.form["village_id"]
    title = request.form["title"]

    content = request.form.get(
        "content",
        ""
    )

    notice_date = request.form.get(
        "notice_date",
        ""
    )

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO notices
        (
            village_id,
            title,
            content,
            notice_date
        )
        VALUES (?, ?, ?, ?)
    """, (
        village_id,
        title,
        content,
        notice_date
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ==================================================
# ADMIN - DELETE NOTICE
# ==================================================

@app.route(
    "/admin/delete-notice/<int:notice_id>",
    methods=["POST"]
)
def delete_notice(notice_id):

    if not is_admin():

        return "Access denied."

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM notices
        WHERE notice_id = ?
    """, (notice_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ==================================================
# ADMIN - ADD DEVELOPMENT
# ==================================================

@app.route(
    "/admin/add-development",
    methods=["POST"]
)
def add_development():

    if not is_admin():

        return "Access denied."

    village_id = request.form["village_id"]

    title = request.form.get(
        "title",
        request.form.get(
            "project_name",
            ""
        )
    )

    location = request.form.get(
        "location",
        ""
    )

    description = request.form.get(
        "description",
        ""
    )

    status = request.form.get(
        "status",
        ""
    )

    conn = get_db_connection()

    # project_name is kept because the existing
    # database requires this column.

    conn.execute("""
        INSERT INTO development_projects
        (
            village_id,
            project_name,
            title,
            location,
            description,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        village_id,
        title,
        title,
        location,
        description,
        status
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ==================================================
# ADMIN - DELETE DEVELOPMENT
# ==================================================

@app.route(
    "/admin/delete-development/<int:project_id>",
    methods=["POST"]
)
def delete_development(project_id):

    if not is_admin():

        return "Access denied."

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM development_projects
        WHERE project_id = ?
    """, (project_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ==================================================
# ADMIN - UPDATE COMPLAINT
# ==================================================

@app.route(
    "/admin/update-complaint/<int:complaint_id>",
    methods=["POST"]
)
def update_complaint(complaint_id):

    if not is_admin():

        return "Access denied."

    status = request.form["status"]

    conn = get_db_connection()

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


# ==================================================
# ADMIN - DELETE COMPLAINT
# ==================================================

@app.route(
    "/admin/delete-complaint/<int:complaint_id>",
    methods=["POST"]
)
def delete_complaint(complaint_id):

    if not is_admin():

        return "Access denied."

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM complaints
        WHERE complaint_id = ?
    """, (complaint_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# ==================================================
# INITIALIZE DATABASE
# ==================================================

init_database()


# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == "__main__":
    app.run(debug=True)

