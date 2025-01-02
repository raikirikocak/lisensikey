import streamlit as st
import json
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from threading import Thread
from flask_cors import CORS

# Fungsi untuk menyimpan status login ke file JSON
def save_login_status():
    status = {
        "logged_in": st.session_state.get("logged_in", False),
        "username": st.session_state.get("username", "")
    }
    with open("login_status.json", "w") as file:
        json.dump(status, file)

# Fungsi untuk memuat status login dari file JSON
def load_login_status():
    if os.path.exists("login_status.json"):
        with open("login_status.json", "r") as file:
            return json.load(file)
    return {"logged_in": False, "username": ""}


# Fungsi login
# Fungsi login
def login_page():
    st.title('Login')

    # Input untuk username dan password
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')

    if st.button('Login'):
        if username == 'admin' and password == '1234':
            # Set session state jika login berhasil
            st.session_state.logged_in = True
            st.session_state.username = username
            # Simpan status login ke file
            save_login_status()
            # Setelah login, arahkan ke dashboard
            st.query_params['page'] = 'dashboard'  # Mengubah query params untuk mengarahkan ke dashboard
        else:
            st.error('Invalid username or password')


# Fungsi dashboard
def dashboard_page():
    st.title("Dashboard")
    username = st.session_state.get("username", "Unknown")
    st.write(f"Selamat datang, {username}!")

    action = st.radio("Pilih Aksi", ["Buat Key Baru", "Hapus Key", "Lihat Key yang Aktif", "Logout"])

    if action == "Buat Key Baru":
        create_key()
    elif action == "Hapus Key":
        delete_key()
    elif action == "Lihat Key yang Aktif":
        display_active_keys()
    elif action == "Logout":
        logout()

# Fungsi logout
def logout():
    # Reset session state saat logout
    st.session_state.logged_in = False
    st.session_state.username = ""
    # Simpan status logout ke file
    save_login_status()
    # Arahkan kembali ke halaman login setelah logout
    st.query_params['page'] = 'login'  # Mengubah query params untuk mengarahkan kembali ke login


# Fungsi untuk membaca dan memperbarui file keys.json
def load_keys():
    try:
        with open("keys.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_keys(keys_data):
    with open("keys.json", "w") as f:
        json.dump(keys_data, f, indent=4)

# Fungsi untuk membuat key baru
def create_key():
    st.subheader("Buat Key Baru")
    new_key = st.text_input("Masukkan Key Baru:")
    expiration_days = st.number_input("Masa berlaku key (dalam hari):", min_value=1, value=30)

    if st.button("Buat Key"):
        if new_key:
            expiration_date = (datetime.now() + timedelta(days=expiration_days)).strftime("%Y-%m-%d")
            keys_data = load_keys()
            keys_data[new_key] = expiration_date
            save_keys(keys_data)
            st.success(f'Key "{new_key}" berhasil dibuat! Masa berlaku sampai {expiration_date}')
        else:
            st.error("Harap masukkan key yang valid.")

# Fungsi untuk menghapus key
def delete_key():
    st.subheader("Hapus Key")
    keys_data = load_keys()
    if not keys_data:
        st.warning("Tidak ada key yang tersimpan.")
        return

    key_to_delete = st.selectbox("Pilih key untuk dihapus", options=list(keys_data.keys()))

    if st.button("Hapus Key"):
        if key_to_delete:
            del keys_data[key_to_delete]
            save_keys(keys_data)
            st.success(f'Key "{key_to_delete}" berhasil dihapus!')
        else:
            st.error("Tidak ada key yang dipilih.")

# Fungsi untuk menampilkan daftar key yang aktif
def display_active_keys():
    st.subheader("Daftar Key yang Aktif")
    keys_data = load_keys()
    if keys_data:
        for key, expiration_date in keys_data.items():
            expiration_date_obj = datetime.strptime(expiration_date, "%Y-%m-%d")
            if expiration_date_obj >= datetime.now():
                st.write(f'Key: `{key}`, Berlaku hingga: {expiration_date}')
            else:
                st.write(f'Key: `{key}` (Expired) - {expiration_date}')
    else:
        st.write("Tidak ada key yang tersimpan.")

# Flask API untuk validasi key
app = Flask(__name__)
CORS(app)
@app.route("/validate_key", methods=["POST"])
def validate_key():
    data = request.json
    input_key = data.get("key")

    if not input_key:
        return jsonify({"success": False, "message": "Key tidak ditemukan dalam request"}), 400

    keys_data = load_keys()
    if input_key in keys_data:
        expiration_date = datetime.strptime(keys_data[input_key], "%Y-%m-%d")
        if expiration_date >= datetime.now():
            return jsonify({"success": True, "message": f"Key valid! Berlaku hingga {keys_data[input_key]}"}), 200
        else:
            return jsonify({"success": False, "message": "Key telah kedaluwarsa"}), 403
    return jsonify({"success": False, "message": "Key tidak valid"}), 404

def run_flask():
    print("Flask API berjalan di http://35.201.127.49:5000")
    app.run(host="0.0.0.0", port=5000)

# Main function
def main():
    # Memuat status login dari file JSON
    status = load_login_status()
    st.session_state.logged_in = status["logged_in"]
    st.session_state.username = status["username"]

    # Ambil query params dari URL
    current_page = st.query_params.get('page', 'login')  # Default ke 'login' jika belum ada query param 'page'

    # Cek apakah pengguna sudah login dan parameter page adalah 'dashboard'
    if current_page == 'dashboard' and st.session_state.logged_in:
        dashboard_page()  # Tampilkan dashboard jika sudah login
    elif current_page == 'login' or not st.session_state.logged_in:
        login_page()  # Tampilkan halaman login jika belum login


if __name__ == "__main__":
    thread = Thread(target=run_flask, daemon=True)
    thread.start()
    main()
