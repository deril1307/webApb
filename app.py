from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import mysql.connector
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from flask import send_from_directory
from urllib.parse import quote as url_quote
# Load environment variables
load_dotenv()
# Flask Configuration
app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET_KEY", "supersecretkey")

bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# untuk menyimpan gambar di lokal
UPLOAD_FOLDER = "static/uploads/"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Database Configuration
# MySQL Database Configuration (Aiven)
# Konfigurasi database menggunakan environment variables
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT"))
}


def get_db_connection():
    """Membuat koneksi ke database dan mengembalikannya jika berhasil."""
    try:
        connection = mysql.connector.connect(**DATABASE_CONFIG)
        if connection.is_connected():
            print("✅ Koneksi ke database berhasil!")
            return connection
        else:
            print("❌ Gagal terhubung ke database!")
            return None
    except mysql.connector.Error as e:
        print(f"🚨 Error: {e}")
        return None


        
# 💻 Endpoint Web
# 🟢 Landing Page Route
@app.route("/")
def home():
    some_data = {"message": "Welcome to TrashTech!"}
    return render_template("index.html")  # Halaman utama perkenalan


# 🟢 WebAdmin Login Route with Session
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("login.html")  # Tampilkan halaman login
    data = request.json
    email = data.get("email")
    password = data.get("password")
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admin WHERE email = %s", (email,))
    admin = cursor.fetchone()
    cursor.close()
    connection.close()
    if not admin or not bcrypt.check_password_hash(admin["password"], password):
        return jsonify({"message": "Email atau password salah"}), 401
    session["admin_id"] = admin["id"]  # Simpan ID admin di session
    return jsonify({"message": "Login berhasil!"}), 200

# 🟢 Web Admin Logout Route
@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin_id", None)  # Hapus session
    return jsonify({"message": "Logout berhasil!"}), 200

# 🟢 Web Protected Admin Route (Dashboard)
@app.route("/admin/dashboard", methods=["GET"])
def admin_dashboard():
    if "admin_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    # Ambil nama admin dari database berdasarkan session
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name FROM admin WHERE id = %s", (session["admin_id"],))
    admin = cursor.fetchone()
    conn.close()
    if not admin:
        return jsonify({"message": "Admin not found"}), 404
    return render_template("dashboard.html", admin_name=admin["name"])

# 🟢 Web Setup Default Admin Route
@app.route("/setup", methods=["POST"])
def setup():
    data = request.json
    username = data.get("username")
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")
    if not username or not name or not email or not phone or not password:
        return jsonify({"message": "Semua field harus diisi!"}), 400
    connection = get_db_connection()
    cursor = connection.cursor()
    # Cek apakah email sudah ada
    cursor.execute("SELECT * FROM admin WHERE email = %s", (email,))
    if cursor.fetchone():
        return jsonify({"message": "Admin dengan email ini sudah ada!"}), 400
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    cursor.execute("INSERT INTO admin (username, name, email, phone, password) VALUES (%s, %s, %s, %s, %s)",
                   (username, name, email, phone, hashed_password))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({"message": "Admin berhasil dibuat!"}), 201

# 🟢 Endpoint untuk mengambil semua pengguna
@app.route("/admin/users", methods=["GET"])
def get_users():
    if "admin_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, username, email FROM users")  # Sesuaikan dengan tabel di database
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(users), 200

# 🟢 Endpoint untuk menghapus pengguna berdasarkan ID
@app.route("/admin/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    if "admin_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "Pengguna berhasil dihapus"}), 200

# 🟢Mendapatkan daftar jenis sampah
@app.route('/admin/trash-types', methods=['POST'])
def add_trash_type():
    if 'picture' not in request.files:
        return jsonify({"error": "Gambar harus diunggah"}), 400

    file = request.files['picture']
    
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Format gambar tidak didukung"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    name = request.form.get("name")
    price = request.form.get("price")
    unit = request.form.get("unit")
    description = request.form.get("description")

    if not name or not price or not unit:
        return jsonify({"error": "Nama, harga, dan satuan harus diisi"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    query = "INSERT INTO waste_categories (name, price, unit, picture, description) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(query, (name, price, unit, filename, description))
    conn.commit()
    conn.close()

    return jsonify({"message": "Jenis sampah berhasil ditambahkan"}), 201

# 🟢 Mengedit jenis sampah
@app.route('/admin/trash-types/<int:trash_id>', methods=['PUT'])
def update_trash_type(trash_id):
    name = request.form.get("name")
    price = request.form.get("price")
    unit = request.form.get("unit")
    description = request.form.get("description")

    # Handle gambar 
    if "picture" in request.files:
        picture = request.files["picture"].filename
        request.files["picture"].save(f"static/uploads/{picture}")  # Simpan gambar ke folder
    else:
        picture = None  # Jika gambar tidak diubah, biarkan tetap None

    conn = get_db_connection()
    cursor = conn.cursor()
    # Perbarui data ke database 
    if picture:
        query = "UPDATE waste_categories SET name=%s, price=%s, unit=%s, picture=%s, description=%s WHERE id=%s"
        cursor.execute(query, (name, price, unit, picture, description, trash_id))
    else:
        query = "UPDATE waste_categories SET name=%s, price=%s, unit=%s, description=%s WHERE id=%s"
        cursor.execute(query, (name, price, unit, description, trash_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Jenis sampah berhasil diperbarui"}), 200


# 🟢 Menghapus jenis sampah
@app.route('/admin/trash-types/<int:trash_id>', methods=['DELETE'])
def delete_trash_type(trash_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM waste_categories WHERE id=%s", (trash_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Jenis sampah berhasil dihapus"}), 200

# # 🟢 upload gambar
# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 🟢 Menghapus jenis sampah melihat gambar
@app.route('/admin/trash-types', methods=['GET'])
def get_trash_types():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM waste_categories")
    trash_types = cursor.fetchall()
    conn.close()

    for trash in trash_types:
        trash["picture"] = f"/uploads/{trash['picture']}"  # Menyertakan path gambar

    return jsonify(trash_types)

# 📱 Endpoint Mobile App
# 🟢 Endpoint Register User Mobile App
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    if not username or not email or not password:
        return jsonify({"message": "Harap isi semua field!"}), 400
    connection = get_db_connection()
    cursor = connection.cursor()

    # Cek apakah email sudah terdaftar
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    existing_user = cursor.fetchone()
    if existing_user:
        cursor.close()
        connection.close()
        return jsonify({"message": "Email sudah digunakan!"}), 400

    # Hash password sebelum disimpan
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                   (username, email, hashed_password))
    connection.commit()

    cursor.close()
    connection.close()
    return jsonify({"message": "Registrasi berhasil!"}), 201

# 🟢 Endpoint Login User Mobile App (Bisa dengan Email atau Username)
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    identifier = data.get("identifier")  # Bisa berupa email atau username
    password = data.get("password")
    print(f"Login attempt: {identifier}")  # Debugging
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    # Cari user berdasarkan email ATAU username
    cursor.execute(
        "SELECT * FROM users WHERE email = %s OR username = %s", 
        (identifier, identifier)
    )
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    if not user:
        print("⚠️ Akun tidak ditemukan!")
        return jsonify({"message": "Email/Username atau password salah!"}), 401
    if not bcrypt.check_password_hash(user["password"], password):
        print("⚠️ Password salah!")
        return jsonify({"message": "Email/Username atau password salah!"}), 401
    print(f"✅ Login berhasil untuk {user['username']} (ID: {user['id']})")
    return jsonify({
        "message": "Login berhasil!",
        "user_id": user["id"],
        "username": user["username"],
        "email": user["email"]
    }), 200

# 🟢 Endpoint Mobile App Menghapus jenis sampah
from decimal import Decimal
@app.route('/trash/types', methods=['GET'])
def get_kategori_sampah():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM waste_categories")  
        data = cursor.fetchall()

        # ✅ Convert Decimal ke float agar bisa diterima di Flutter
        for item in data:
            for key, value in item.items():
                if isinstance(value, Decimal):
                    item[key] = float(value)  # Bisa juga pakai str(value)
        cursor.close()
        conn.close()
        print("Response Data:", data)  # Debugging
        return jsonify(data)  
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🟢 Endpoint Mobile App Melihat gambar jenis sampah 
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('static/uploads', filename)


# 🔵 Endpoint untuk mengambil data user berdasarkan userId
@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    print(f"🔍 GET /users/{user_id} dipanggil")  # Debugging

    try:
        conn = get_db_connection()
        if conn is None:
            print("❌ Database connection gagal")
            return jsonify({"error": "Database connection error"}), 500

        cursor = conn.cursor(dictionary=True)

        # Debug query yang dijalankan
        query = "SELECT id, username, points, balance FROM users WHERE id = %s"
        print(f"🔎 Query: {query} | Params: {user_id}")

        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            print(f"✅ Data ditemukan: {user}")
            return jsonify(user)
        else:
            print("❌ User tidak ditemukan")  # Debugging
            return jsonify({"error": "User not found"}), 404

    except Exception as e:
        print(f"⚠️ Error: {str(e)}")  # Debugging
        return jsonify({"error": str(e)}), 500

# 🟢 Run the App
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))  # Gunakan PORT dari environment variable
    app.run(port=port, debug=False)  # Tidak perlu host="0.0.0.0"
