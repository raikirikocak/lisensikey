import streamlit as st
import json
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from threading import Thread
from flask_cors import CORS
import requests
import socket
from pyngrok import ngrok, conf
from threading import Lock
from flask_socketio import SocketIO, emit


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
        if username == 'adminkocak' and password == 'Mapapa21':
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

    action = st.radio("Pilih Aksi", [
        "Buat Key Baru", 
        "Hapus Key", 
        "Lihat Key yang Aktif", 
        "Pengaturan IP dan URL API Flask",
        "logout"
    ])

    if action == "Buat Key Baru":
        create_key()
    elif action == "Hapus Key":
        delete_key()
    elif action == "Lihat Key yang Aktif":
        display_active_keys()
    elif action == "Pengaturan IP dan URL API Flask":
        api_settings()
    
    elif action == "logout":
            logout()  # Memanggil pengaturan IP dan URL API Flask

def api_settings():
    st.subheader("Pengaturan IP dan URL API Flask")

    # Ambil alamat IP server secara otomatis
    try:
        hostname = socket.gethostname()
        server_ip = socket.gethostbyname(hostname)  # Mendapatkan IP server
    except Exception as e:
        st.error(f"Gagal mendapatkan IP server: {e}")
        return

    # Tetapkan URL API Flask
    flask_ip = f"http://{server_ip}:7495"  # Asumsi Flask berjalan di port 7495
    flask_url = "/validate_key"

    # Tampilkan informasi IP dan URL API Flask
    st.write(f"IP Flask saat ini: {flask_ip}")
    st.write(f"URL API saat ini: {flask_ip}{flask_url}")

    # Input untuk user dan key
    st.subheader("Validasi Key")
    user = st.text_input("Masukkan Nama Pengguna (User)", value="user1")  # Input untuk user
    key = st.text_input("Masukkan Key untuk Validasi", value="key1")  # Input untuk key

    # Tombol validasi
    if st.button("Validasi Key"):
        # Kirim permintaan ke API Flask dengan user dan key
        url = f"{flask_ip}{flask_url}"
        try:
            response = requests.post(url, json={"key": key, "user": user})
            if response.status_code == 200:
                st.success("Sukses: Server Flask merespon dengan status 200")
                st.write(response.json())  # Menampilkan respons dari API
            else:
                st.error(f"Gagal: Server Flask merespon dengan status {response.status_code}")
                st.write(response.json())  # Menampilkan pesan error dari API
        except requests.exceptions.RequestException as e:
            st.error(f"Gagal menghubungi API Flask: {str(e)}")

# Fungsi logout
def logout():
    # Reset session state saat logout
    st.session_state.logged_in = False
    st.session_state.username = ""
    # Simpan status logout ke file
    save_login_status()
    # Arahkan kembali ke halaman login setelah logout
    st.query_params['page'] = 'login'  # Mengubah query params untuk mengarahkan kembali ke login


def load_keys():
    try:
        with open("keys.json", "r") as f:
            keys_data = json.load(f)
            
            # Periksa apakah keys_data adalah dictionary yang valid
            if isinstance(keys_data, dict):
                return keys_data
            else:
                raise ValueError("Data dalam keys.json tidak valid, harus berupa dictionary.")
    
    except (FileNotFoundError, ValueError) as e:
        st.error(f"Error memuat data keys.json: {e}")
        return {}
    except json.JSONDecodeError:
        st.error("Error: Format JSON dalam keys.json tidak valid.")
        return {}


def save_keys(keys_data):
    with open("keys.json", "w") as f:
        json.dump(keys_data, f, indent=4)

# Fungsi untuk membuat key baru
def create_key():
    st.subheader("Buat Key Baru")
    new_key = st.text_input("Masukkan Key Baru:")
    username = st.text_input("Masukkan Nama Pengguna:")
    expiration_days = st.number_input("Masa berlaku key (dalam hari):", min_value=1, value=30)

    if st.button("Buat Key"):
        if new_key and username:
            # Muat data key yang ada
            keys_data = load_keys()

            # Cek apakah key sudah ada
            if new_key in keys_data:
                st.error(f"Key '{new_key}' sudah ada!")
            else:
                # Menentukan tanggal kedaluwarsa
                expiration_date = (datetime.now() + timedelta(days=expiration_days)).strftime("%Y-%m-%d")
                # Menyimpan key baru dengan atribut tambahan
                keys_data[new_key] = {
                    "expiration_date": expiration_date,
                    "used": False,
                    "user": username,
                    "is_active": False,
                    "last_active": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                }
                # Simpan ke file
                save_keys(keys_data)
                st.success(f'Key "{new_key}" untuk pengguna "{username}" berhasil dibuat! Masa berlaku sampai {expiration_date}')
        else:
            st.error("Harap masukkan key dan nama pengguna yang valid.")


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

def display_active_keys():
    keys_data = load_keys()  # Memuat data keys dari load_keys()

    st.subheader("Daftar Key yang Aktif atau Tidak Valid")
    if keys_data:
        for key, data in keys_data.items():
            if "expiration_date" in data and "last_active" in data and "user" in data:
                try:
                    expiration_date_obj = datetime.strptime(data["expiration_date"], "%Y-%m-%d")
                    last_active_obj = datetime.strptime(data["last_active"], "%Y-%m-%dT%H:%M:%S")
                    current_time = datetime.now()

                    # Periksa apakah key sudah kedaluwarsa terlebih dahulu
                    if expiration_date_obj < current_time:
                        data["is_active"] = False
                        status_message = "Kedaluwarsa"
                        status_icon = "❌"  # Ikon silang merah untuk kedaluwarsa
                    else:
                        # Jika key masih berlaku, periksa aktivitas terakhir
                        if (current_time - last_active_obj).total_seconds() <= 10:
                            data["is_active"] = True
                            status_message = "Aktif"
                            status_icon = "🟢"  # Lampu hijau
                        else:
                            data["is_active"] = False
                            status_message = "Tidak Aktif"
                            status_icon = "🔴"  # Lampu merah

                    # Tampilkan informasi key dengan statusnya
                    st.markdown(
                        f"""
                        <div style="font-size:15px; color:#CAF4FF;">
                            {status_icon} Key: `{key}`, Status: {status_message}, 
                            Berlaku hingga: {data["expiration_date"]}, Pengguna: `{data["user"]}`
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                except ValueError:
                    st.error(f"Format tanggal untuk key `{key}` tidak valid.")
            else:
                st.error(f"Data untuk key `{key}` tidak lengkap atau tidak memiliki informasi pengguna.")
    else:
        st.write("Tidak ada key yang tersimpan.")



# Flask API untuk validasi key
app = Flask(__name__)
CORS(app)

socketio = SocketIO(app)
lock = Lock()

# Event saat klien terhubung
@socketio.on("connect")
def handle_connect():
    print("Client connected.")

@socketio.on("validate_key")
def validate_key(data):
    with lock:
        input_key = data.get("key")
        input_username = data.get("username")

        if not input_key or not input_username:
            emit("validation_result", {"success": False, "message": "Key atau nama pengguna tidak ditemukan dalam request"})
            return

        keys_data = load_keys()
        if input_key in keys_data:
            key_data = keys_data[input_key]
            expiration_date = datetime.strptime(key_data["expiration_date"], "%Y-%m-%d")

            # Periksa apakah key telah expired
            if expiration_date < datetime.now():
                emit("validation_result", {"success": False, "message": "Key telah kedaluwarsa"})
                return

            current_time = datetime.now()

            last_active_str = key_data.get("last_active", None)
            if last_active_str:
                last_active = datetime.strptime(last_active_str, "%Y-%m-%dT%H:%M:%S")
                # Jika aktivitas terakhir ditemukan, perbarui status aktif berdasarkan aktivitas Socket.IO
                if (current_time - last_active).total_seconds() <= 10:
                    key_data["is_active"] = True
                else:
                    key_data["is_active"] = False

            # Perbarui waktu aktivitas terbaru (berdasarkan waktu sekarang) jika key valid
            key_data["last_active"] = current_time.strftime("%Y-%m-%dT%H:%M:%S")
            save_keys(keys_data)

            emit("validation_result", {"success": True, "message": f"Key valid! Berlaku hingga {key_data['expiration_date']}"})
            return

        emit("validation_result", {"success": False, "message": "Key tidak valid"})

        
# Event saat klien memutuskan koneksi
@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected.")



def run_flask():
    conf.get_default().auth_token = "2rW0ORNPBUVgKvdeC4J5HIKsKLy_7KRz8jfykHYhwmjpiqUx6"
    ngrok_tunnel = ngrok.connect(7495)
    flask_url = ngrok_tunnel.public_url
    st.session_state.flask_url = flask_url
    print(f"Flask berjalan di {flask_url}")
    app.run(host="0.0.0.0", port=7495)

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
