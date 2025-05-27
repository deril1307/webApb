# type: ignore
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import mysql.connector
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from flask import send_from_directory
from urllib.parse import quote as url_quote
import cloudinary
import cloudinary.uploader
from datetime import datetime
from flask_mail import Mail, Message
from random import randint
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import time
import secrets
import smtplib
from flask import request, jsonify
from email.mime.text import MIMEText

# Load file env
load_dotenv()
# Flask Configuration
app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET_KEY", "supersecretkey")

bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# Konfigurasi Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

# untuk menyimpan gambar di lokal
UPLOAD_FOLDER = "static/uploads/"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
# 🟢 Landing Page
@app.route("/")
def home():
    some_data = {"message": "Welcome to TrashTech!"}
    return render_template("index.html")  


# 🟢 WebAdmin Login Route with Session
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("login.html")  
    data = request.json
    email = data.get("email")
    password = data.get("password")
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True) # type: ignore
    cursor.execute("SELECT * FROM admin WHERE email = %s", (email,))
    admin = cursor.fetchone()
    cursor.close()
    connection.close() # type: ignore
    if not admin or not bcrypt.check_password_hash(admin["password"], password):
        return jsonify({"message": "Email atau password salah"}), 401
    session["admin_id"] = admin["id"]  # Simpan ID admin di session
    return jsonify({"message": "Login berhasil!"}), 200

# 🟢 Web Admin Logout Route
@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin_id", None)  
    return jsonify({"message": "Logout berhasil!"}), 200

# 🟢 Web Protected Admin Route (Dashboard)
@app.route("/admin/dashboard", methods=["GET"])
def admin_dashboard():
    if "admin_id" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    # Ambil nama admin dari database berdasarkan session
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # type: ignore
    cursor.execute("SELECT name FROM admin WHERE id = %s", (session["admin_id"],))
    admin = cursor.fetchone()
    conn.close() # type: ignore
    if not admin:
        return jsonify({"message": "Admin not found"}), 404
    return render_template("dashboard.html", admin_name=admin["name"])

# 🟢 Web Setup untuk membuat akun admin melalu post man
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

    # Tambahkan points dan balance ke query
    cursor.execute("SELECT id, username, email, points, balance FROM users")  
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


# 🟢 Mendaftarkan jenis sampah 
@app.route('/admin/trash-types', methods=['POST'])
def add_trash_type():
    if 'picture' not in request.files:
        return jsonify({"error": "Gambar harus diunggah"}), 400

    file = request.files['picture']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Format gambar tidak didukung"}), 400

    # Simpan ke lokal
    filename = secure_filename(file.filename)
    local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(local_path)

    # Upload ke Cloudinary
    cloudinary_result = cloudinary.uploader.upload(local_path)
    cloudinary_url = cloudinary_result["secure_url"]

    name = request.form.get("name")
    point_per_unit = request.form.get("point_per_unit")  # Changed from price
    unit = request.form.get("unit")
    description = request.form.get("description")

    if not name or not point_per_unit or not unit:  # Changed validation
        return jsonify({"error": "Nama, poin per unit, dan satuan harus diisi"}), 400

    try:
        point_per_unit = float(point_per_unit)  # Ensure numeric value
    except ValueError:
        return jsonify({"error": "Poin per unit harus berupa angka"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO waste_categories 
        (name, point_per_unit, unit, picture, cloudinary_url, description) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (name, point_per_unit, unit, filename, cloudinary_url, description))
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Jenis sampah berhasil ditambahkan",
        "data": {
            "name": name,
            "point_per_unit": point_per_unit,
            "unit": unit,
            "cloudinary_url": cloudinary_url
        }
    }), 201

# 🟢 Mengedit jenis sampah
@app.route('/admin/trash-types/<int:trash_id>', methods=['PUT'])
def update_trash_type(trash_id):
    # Get form data
    name = request.form.get("name")
    point_per_unit = request.form.get("point_per_unit")  # Changed from price
    unit = request.form.get("unit")
    description = request.form.get("description")
    
    # Validate required fields
    if not name or not point_per_unit or not unit:
        return jsonify({"error": "Nama, poin per unit, dan satuan harus diisi"}), 400
    
    try:
        point_per_unit = float(point_per_unit)  # Ensure numeric value
    except ValueError:
        return jsonify({"error": "Poin per unit harus berupa angka"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 🔹 Get old data (cloudinary_url & picture)
    cursor.execute("SELECT cloudinary_url, picture FROM waste_categories WHERE id=%s", (trash_id,))
    old_data = cursor.fetchone()
    
    if not old_data:
        conn.close()
        return jsonify({"error": "Jenis sampah tidak ditemukan"}), 404
        
    old_cloudinary_url = old_data["cloudinary_url"]
    old_picture = old_data["picture"]
    cloudinary_url = old_cloudinary_url  # Default to old image
    picture = old_picture

    # Handle image upload if provided
    if "picture" in request.files:
        file = request.files["picture"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(local_path)

            # 🔹 Upload to Cloudinary
            cloudinary_result = cloudinary.uploader.upload(local_path)
            cloudinary_url = cloudinary_result["secure_url"]

            # 🔹 Delete old Cloudinary image if exists
            if old_cloudinary_url:
                public_id = old_cloudinary_url.split("/")[-1].split(".")[0]
                cloudinary.uploader.destroy(public_id)

            # 🔹 Delete old local file if exists
            if old_picture:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_picture)
                if os.path.exists(old_path):
                    os.remove(old_path)

            picture = filename  
        else:
            conn.close()
            return jsonify({"error": "Format gambar tidak didukung"}), 400

    # 🔹 Update database
    query = """
        UPDATE waste_categories 
        SET name=%s, point_per_unit=%s, unit=%s, 
            cloudinary_url=%s, picture=%s, description=%s 
        WHERE id=%s
    """
    cursor.execute(query, (
        name, point_per_unit, unit,
        cloudinary_url, picture, description,
        trash_id
    ))
    conn.commit()
    conn.close()
    
    return jsonify({
        "message": "Jenis sampah berhasil diperbarui",
        "data": {
            "id": trash_id,
            "name": name,
            "point_per_unit": point_per_unit,
            "unit": unit
        }
    }), 200

# 🟢 Menghapus jenis sampah
@app.route('/admin/trash-types/<int:trash_id>', methods=['DELETE'])
def delete_trash_type(trash_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Ambil informasi gambar sebelum dihapus
    cursor.execute("SELECT picture FROM waste_categories WHERE id=%s", (trash_id,))
    trash = cursor.fetchone()

    if trash:
        picture = trash["picture"]
        if picture:
            local_path = os.path.join(app.config['UPLOAD_FOLDER'], picture)
            if os.path.exists(local_path):
                os.remove(local_path)  # Hapus dari lokal

            # Hapus dari Cloudinary
            cloudinary.uploader.destroy(picture)

    # Hapus data dari database
    cursor.execute("DELETE FROM waste_categories WHERE id=%s", (trash_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Jenis sampah berhasil dihapus"}), 200


# 🟢 Melihat jenis sampah melihat gambar
@app.route('/admin/trash-types', methods=['GET'])
def get_trash_types():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM waste_categories")
    trash_types = cursor.fetchall()
    conn.close()

    # Cek apakah ada Cloudinary URL, jika tidak, gunakan gambar lokal
    for trash in trash_types:
        if trash["cloudinary_url"]:  # Jika ada di Cloudinary
            trash["picture"] = trash["cloudinary_url"]
        else:  # Jika tidak ada, gunakan gambar lokal
            trash["picture"] = f"/static/uploads/{trash['picture']}" if trash["picture"] else None
    return jsonify(trash_types)


# 📱 Endpoint Mobile App
# 🟢 Endpoint Register User Mobile App
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")  # Ambil dari request

    if not username or not email or not password or not full_name:
        return jsonify({"message": "Harap isi semua field!"}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    existing_user = cursor.fetchone()
    if existing_user:
        cursor.close()
        connection.close()
        return jsonify({"message": "Email sudah digunakan!"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    try:
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                       (username, email, hashed_password))
        connection.commit()

        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        new_user = cursor.fetchone()
        user_id = new_user[0]

        # Gunakan full_name dari frontend
        cursor.execute(
            "INSERT INTO users_data (user_id, full_name, phone_number, address, profile_picture) VALUES (%s, %s, '', '', NULL)", 
            (user_id, full_name)
        )
        connection.commit()

        message = "Registrasi berhasil!"
        success = True
    except Exception as e:
        connection.rollback()
        message = f"⚠️ Error saat registrasi: {e}"
        success = False
    finally:
        cursor.close()
        connection.close()

    return jsonify({"message": message, "success": success}), 201 if success else 500


# 🟢 Endpoint Login User Mobile App (Bisa dengan Email atau Username)
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    identifier = data.get("identifier")  # Bisa email atau username
    password = data.get("password")
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    # Cari user berdasarkan email ATAU username
    cursor.execute(
        "SELECT * FROM users WHERE email = %s OR username = %s", 
        (identifier, identifier)
    )
    user = cursor.fetchone()
    if not user:
        cursor.close()
        connection.close()
        return jsonify({"message": "Email/Username atau password salah!", "success": False}), 401
    if not bcrypt.check_password_hash(user["password"], password):
        cursor.close()
        connection.close()
        return jsonify({"message": "Email/Username atau password salah!", "success": False}), 401
    user_id = user["id"]
    
    # ✅ Cek apakah user sudah ada di tabel `users_data`
    cursor.execute("SELECT user_id FROM users_data WHERE user_id = %s", (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        print(f"ℹ️ User {user_id} belum ada di users_data, akan dibuat otomatis.")
        try:
            cursor.execute(
                "INSERT INTO users_data (user_id, full_name, phone_number, address, profile_picture) VALUES (%s, '', '', '', NULL)",
                (user_id,)
            )
            connection.commit()
            print(f"✅ User {user_id} berhasil ditambahkan ke users_data!")
        except Exception as e:
            print(f"❌ Gagal menambahkan user {user_id} ke users_data: {e}")
            connection.rollback()  # Batalkan transaksi jika gagal
    cursor.close()
    connection.close()
    return jsonify({
        "message": "Login berhasil!",
        "success": True,
        "user_id": user_id,
        "username": user["username"],
        "email": user["email"]
    }), 200



reset_tokens = {}  # {email: (token, expiry_time)}
@app.route('/request-reset-password', methods=['POST'])
def request_reset_password():
    data = request.json
    email = data.get("email")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"message": "Email tidak ditemukan", "success": False}), 404

    token = secrets.token_hex(3).upper()  # Misal: 'A1B2C3'
    expiry = time.time() + 120  # 120 detik

    reset_tokens[email] = (token, expiry)

    # Kirim token ke email (gunakan SMTP atau API sesungguhnya)
    message = MIMEText(f"Kode reset password Anda adalah: {token}")
    message["Subject"] = "Reset Password - TrashTech"
    message["From"] = "derilwijdan346@gmail.com"
    message["To"] = email

    try:
        smtp = smtplib.SMTP("smtp.gmail.com", 587)
        smtp.starttls()
        smtp.login("derilwijdan346@gmail.com", "pcou krdl errg sdfp")
        smtp.sendmail("derilwijdan346@gmail.com", email, message.as_string())
        smtp.quit()
    except Exception as e:
        print(f"Email gagal dikirim: {e}")
        return jsonify({"message": "Gagal mengirim email", "success": False}), 500

    return jsonify({"message": "Kode reset telah dikirim ke email!", "success": True}), 200

@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get("email")
    token = data.get("token")
    new_password = data.get("new_password")

    saved_token, expiry = reset_tokens.get(email, (None, 0))
    if saved_token != token or time.time() > expiry:
        return jsonify({"message": "Token tidak valid atau telah kedaluwarsa", "success": False}), 400

    hashed_pw = bcrypt.generate_password_hash(new_password).decode("utf-8")
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_pw, email))
    connection.commit()
    cursor.close()
    connection.close()

    del reset_tokens[email]
    return jsonify({"message": "Password berhasil direset", "success": True}), 200



# 🟢 Endpoint Mobile App Melihat jenis sampah
from decimal import Decimal
@app.route('/trash/types', methods=['GET'])
def get_kategori_sampah():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM waste_categories")  
        data = cursor.fetchall()

        # Convert Decimal ke float agar bisa diterima di Flutter
        for item in data:
            for key, value in item.items():
                if isinstance(value, Decimal):
                    item[key] = float(value)  
        cursor.close()
        conn.close()
        print("Response Data:", data)  
        return jsonify(data)  
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🟢 Endpoint Mobile App Melihat gambar jenis sampah 
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if os.path.exists(local_path):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # Cek di database untuk URL Cloudinary
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT cloudinary_url FROM waste_categories WHERE picture = %s", (filename,))
    result = cursor.fetchone()
    conn.close()

    if result and result["cloudinary_url"]:
        return redirect(result["cloudinary_url"])  # Redirect ke Cloudinary

    return jsonify({"error": "File not found"}), 404


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
    

@app.route('/static/uploads/<path:filename>')
def serve_uploaded_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        abort(404)  # Kembalikan error 404 jika file tidak ditemukan
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ✅ Endpoint: Ambil data profil dari tabel `users_data`
@app.route("/get-profile/<int:user_id>", methods=["GET"])
def get_profile(user_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Gagal terhubung ke database"}), 500

    try:
        cur = conn.cursor()
        cur.execute("SELECT full_name, phone_number, address, profile_picture FROM users_data WHERE user_id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()

        if user:
            return jsonify({
                "success": True,
                "data": {
                    "full_name": user[0],  
                    "phone_number": user[1],
                    "address": user[2],
                    "profile_picture": user[3]
                }
            })
        else:
            return jsonify({
                "success": True,
                "data": {
                    "full_name": "",
                    "phone_number": "",
                    "address": "",
                    "profile_picture": None
                }
            })
    except Exception as e:
        return jsonify({"error": "⚠️ Terjadi kesalahan"}), 500
    finally:
        conn.close()


# ✅ Endpoint: Update profil pengguna di tabel `users_data`
@app.route("/update-profile", methods=["PUT"])
def update_profile():
    user_id = request.form.get("user_id")
    full_name = request.form.get("full_name", "").strip()
    phone_number = request.form.get("phone_number", "").strip()
    address = request.form.get("address", "").strip()

    if not user_id or not user_id.isdigit():
        return jsonify({"error": "User ID tidak valid"}), 400
    user_id = int(user_id)

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Gagal terhubung ke database"}), 500
    
    try:
        cur = conn.cursor(dictionary=True)
        
        # 🟢 Cek apakah user ada di `users_data`
        cur.execute("SELECT profile_picture FROM users_data WHERE user_id = %s", (user_id,))
        user_data = cur.fetchone()
        
        if not user_data:
            cur.close()
            conn.close()
            return jsonify({"error": "User tidak ditemukan"}), 404
        profile_picture_url = user_data["profile_picture"]  # Simpan URL lama jika ada

        # ✅ Jika ada file gambar baru, upload ke Cloudinary
        if "profile_picture" in request.files:
            file = request.files["profile_picture"]
            if file:
                upload_result = cloudinary.uploader.upload(file, folder="user_profiles/")
                
                # 🔹 Hapus gambar lama jika ada
                if profile_picture_url:
                    public_id = profile_picture_url.split("/")[-1].split(".")[0]
                    cloudinary.uploader.destroy(f"user_profiles/{public_id}")
                
                profile_picture_url = upload_result["secure_url"]  # Simpan URL gambar baru

        # 🔹 Update data di database
        cur.execute(
            "UPDATE users_data SET full_name=%s, phone_number=%s, address=%s, profile_picture=%s WHERE user_id=%s",
            (full_name, phone_number, address, profile_picture_url, user_id)
        )
        
        conn.commit()
        return jsonify({"message": "✅ Profil berhasil diperbarui!", "profile_picture_url": profile_picture_url}), 200
    
    except mysql.connector.Error as e:
        return jsonify({"error": f"⚠️ Error saat update profil: {e}"}), 500
    finally:
        cur.close()
        conn.close()
# ✅ Endpoint: setor sampah pengguna di tabel `setor_sampah`
@app.route('/setor-sampah', methods=['POST'])
def setor_sampah():
    data = request.get_json()
    if not data or 'user_id' not in data or 'waste_id' not in data or 'weight' not in data:
        return jsonify({'error': 'Data tidak lengkap'}), 400

    user_id = data['user_id']
    waste_id = data['waste_id']
    weight = data['weight']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Ambil poin per unit dari kategori sampah
    cursor.execute('SELECT point_per_unit FROM waste_categories WHERE id = %s', (waste_id,))
    kategori = cursor.fetchone()
    if not kategori:
        conn.close()
        return jsonify({'error': 'Kategori sampah tidak ditemukan'}), 404

    poin_per_unit = kategori[0]
    points_earned = int(weight / 1000 * poin_per_unit)

    # Simpan data setor sampah
    cursor.execute(
        'INSERT INTO setor_sampah (user_id, waste_id, weight, points_earned, date) VALUES (%s, %s, %s, %s, %s)',
        (user_id, waste_id, weight, points_earned, datetime.now())
    )

    # Update total poin user (tambah poin baru ke poin yang lama)
    cursor.execute(
        'UPDATE users SET points = points + %s WHERE id = %s',
        (points_earned, user_id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        'message': 'Setor sampah berhasil',
        'points_earned': points_earned,
        'total_weight': weight
    }), 200

# Membuat fungsi (update saldo) ketika di tarik saldonya
@app.route('/update_saldo', methods=['POST'])
def update_saldo():
    data = request.json
    user_id = data.get('user_id')
    amount = data.get('amount')

    if not user_id or amount is None:
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Ambil balance saat ini
        cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        current_balance = result[0]

        if amount > current_balance:
            return jsonify({'status': 'error', 'message': 'Insufficient balance'}), 400

        new_balance = current_balance - amount

        cursor.execute("UPDATE users SET balance = %s WHERE id = %s", (new_balance, user_id))
        conn.commit()

        return jsonify({'status': 'success', 'new_balance': new_balance}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

# leaderboard

# GET: Ambil leaderboard
@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT username, points 
        FROM users
        ORDER BY points DESC
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results), 200

# tes
# 🟢 Run the App
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000)) 
    app.run(port=port, debug=False) 
