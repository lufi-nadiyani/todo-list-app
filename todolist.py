# Import Library
import streamlit as st
import mysql.connector
from datetime import datetime
import pandas as pd

# Pengaturan Kepala Website
st.set_page_config(page_title="To-Do List App", layout="wide")
st.title("📋 Aplikasi To-Do List")

# ==========================================
# 1. CLASS DATABASE (KONSEP OOP)
# ==========================================
class DatabaseTodo:
    def __init__(self):
        """Constructor: Inisialisasi database dan tabel"""
        self.host = "localhost"
        self.user = "root"
        self.password = ""
        self.db_name = "todo_app"
        self.init_db()

    def get_connection(self, use_db=True):
        """Method untuk membuat koneksi ke MySQL"""
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.db_name if use_db else None
        )

    def init_db(self):
        """Method untuk membuat database dan tabel tugas jika belum ada"""
        try:
            # Buat database jika belum ada
            conn = self.get_connection(use_db=False)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_name}")
            cursor.close()
            conn.close()

            # Buat tabel jika belum ada
            db = self.get_connection(use_db=True)
            cursor = db.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tugas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    judul VARCHAR(200) NOT NULL,
                    deadline DATE NOT NULL,
                    prioritas ENUM('Rendah', 'Sedang', 'Tinggi') NOT NULL,
                    status ENUM('Belum', 'Sedang Dikerjakan', 'Selesai') DEFAULT 'Belum',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.commit()
            cursor.close()
            db.close()
        except mysql.connector.Error as err:
            st.error(f"Gagal inisialisasi database: {err}")

    # ====== CRUD OPERATIONS ======
    def tambah_tugas(self, judul, deadline, prioritas):
        """Method [CREATE] untuk menambah tugas baru"""
        try:
            db = self.get_connection()
            cursor = db.cursor()
            query = """
                INSERT INTO tugas (judul, deadline, prioritas) 
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (judul, deadline, prioritas))
            db.commit()
            cursor.close()
            db.close()
            return True, f"✅ Berhasil menambah tugas: {judul}"
        except mysql.connector.Error as err:
            return False, f"❌ Gagal menyimpan tugas: {err}"

    def lihat_tugas(self, keyword="", filter_prioritas=""):
        """Method [READ] untuk melihat semua tugas dengan filter dan pencarian"""
        try:
            db = self.get_connection()
            cursor = db.cursor(dictionary=True)
            
            query = "SELECT * FROM tugas WHERE 1=1"
            params = []
            
            if keyword:
                query += " AND judul LIKE %s"
                params.append(f"%{keyword}%")
            
            if filter_prioritas and filter_prioritas != "Semua":
                query += " AND prioritas = %s"
                params.append(filter_prioritas)
            
            query += " ORDER BY deadline ASC, prioritas DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            db.close()
            return rows
        except mysql.connector.Error as err:
            st.error(f"Gagal mengambil data: {err}")
            return []

    def ubah_tugas(self, id_tugas, judul, deadline, prioritas, status):
        """Method [UPDATE] untuk mengubah tugas"""
        try:
            db = self.get_connection()
            cursor = db.cursor()
            query = """
                UPDATE tugas 
                SET judul=%s, deadline=%s, prioritas=%s, status=%s 
                WHERE id=%s
            """
            cursor.execute(query, (judul, deadline, prioritas, status, id_tugas))
            db.commit()
            cursor.close()
            db.close()
            return True, "✅ Tugas berhasil diperbarui!"
        except mysql.connector.Error as err:
            return False, f"❌ Gagal update tugas: {err}"

    def hapus_tugas(self, id_tugas):
        """Method [DELETE] untuk menghapus tugas"""
        try:
            db = self.get_connection()
            cursor = db.cursor()
            query = "DELETE FROM tugas WHERE id = %s"
            cursor.execute(query, (id_tugas,))
            db.commit()
            cursor.close()
            db.close()
            return True, "✅ Tugas berhasil dihapus!"
        except mysql.connector.Error as err:
            return False, f"❌ Gagal menghapus tugas: {err}"

# ==========================================
# 2. INHERITANCE - CLASS TUGAS (OOP)
# ==========================================
class Tugas:
    def __init__(self, id, judul, deadline, prioritas, status="Belum"):
        self.id = id
        self.judul = judul
        self.deadline = deadline
        self.prioritas = prioritas
        self.status = status
    
    def get_info(self):
        """Method untuk mendapatkan informasi tugas"""
        return f"{self.judul} - {self.prioritas} - {self.status}"

class TugasPrioritas(Tugas):
    """Polymorphism: Class turunan dengan fitur tambahan"""
    def __init__(self, id, judul, deadline, prioritas, status="Belum", catatan=""):
        super().__init__(id, judul, deadline, prioritas, status)
        self.catatan = catatan
    
    def get_info(self):
        """Override method dari parent class"""
        info = super().get_info()
        if self.catatan:
            info += f" - Catatan: {self.catatan}"
        return info

# Instansiasi Objek Database
db_todo = DatabaseTodo()

# ==========================================
# 3. FUNGSI POP-UP DIALOG (STREAMLIT)
# ==========================================
@st.dialog("✏️ Edit Tugas")
def edit_popup(tugas):
    st.write(f"Mengubah tugas: **{tugas['judul']}**")
    
    judul = st.text_input("Judul Tugas", value=tugas['judul'])
    deadline = st.date_input("Deadline", value=tugas['deadline'])
    prioritas = st.selectbox(
        "Prioritas", 
        ["Rendah", "Sedang", "Tinggi"], 
        index=["Rendah", "Sedang", "Tinggi"].index(tugas['prioritas'])
    )
    status = st.selectbox(
        "Status",
        ["Belum", "Sedang Dikerjakan", "Selesai"],
        index=["Belum", "Sedang Dikerjakan", "Selesai"].index(tugas['status'])
    )
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Simpan Perubahan", use_container_width=True):
            sukses, pesan = db_todo.ubah_tugas(tugas['id'], judul, deadline, prioritas, status)
            if sukses:
                st.success(pesan)
                st.rerun()
            else:
                st.error(pesan)
    with col2:
        if st.button("❌ Batal", use_container_width=True):
            st.rerun()

@st.dialog("⚠️ Konfirmasi Hapus Tugas")
def hapus_popup(id_tugas, judul):
    st.write(f"Apakah Anda yakin ingin menghapus tugas berikut?")
    st.write(f"• **Tugas:** {judul}")
    st.write("Tindakan ini permanen dan tidak dapat dibatalkan.")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔴 Ya, Hapus", type="primary", use_container_width=True):
            sukses, pesan = db_todo.hapus_tugas(id_tugas)
            if sukses:
                st.success(pesan)
                st.rerun()
            else:
                st.error(pesan)
    with col2:
        if st.button("❌ Batal", use_container_width=True):
            st.rerun()


# ==========================================
# 3.5 FUNGSI POP-UP TAMBAH TUGAS (BARU!)
# ==========================================
@st.dialog("✅ Konfirmasi Tambah Tugas")
def tambah_popup(judul, deadline, prioritas):
    st.success(f"🎉 Tugas berhasil ditambahkan!")
    st.write(f"• **Judul:** {judul}")
    st.write(f"• **Deadline:** {deadline.strftime('%d %B %Y')}")
    st.write(f"• **Prioritas:** {prioritas}")
    
    st.markdown("---")
    if st.button("👍 OK, Saya Tahu", use_container_width=True):
        st.rerun()


# ==========================================
# 4. ANTARMUKA UTAMA
# ==========================================
tab1, tab2 = st.tabs(["➕ Tambah Tugas", "📋 Daftar Tugas"])

# --- TAB 1: FORM TAMBAH TUGAS ---
with tab1:
    st.subheader("📝 Tambah Tugas Baru")
    
    with st.form("form_tugas", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            judul = st.text_input("📌 Judul Tugas", placeholder="Masukkan judul tugas...")
            deadline = st.date_input("📅 Deadline", min_value=datetime.today())
        
        with col2:
            prioritas = st.selectbox(
                "🎯 Prioritas",
                ["Rendah", "Sedang", "Tinggi"],
                help="Tinggi = Paling penting, Rendah = Bisa ditunda"
            )
        
        submit = st.form_submit_button("➕ Tambah Tugas", use_container_width=True)
        
        if submit:
            if judul and deadline:
                sukses, pesan = db_todo.tambah_tugas(judul, deadline, prioritas)
                if sukses:
                    # Panggil pop-up pemberitahuan
                    tambah_popup(judul, deadline, prioritas)
                else:
                    st.error(pesan)
            else:
                st.warning("⚠️ Judul dan deadline harus diisi!")

# --- TAB 2: LIHAT DATA TUGAS ---
with tab2:
    st.subheader("📋 Daftar Tugas")
    
    # Filter dan Pencarian
    col1, col2 = st.columns([3, 1])
    with col1:
        keyword = st.text_input("🔍 Cari Tugas", placeholder="Masukkan kata kunci...")
    with col2:
        filter_prioritas = st.selectbox(
            "🎯 Filter Prioritas",
            ["Semua", "Rendah", "Sedang", "Tinggi"]
        )
    
    # Ambil data tugas
    tasks = db_todo.lihat_tugas(keyword, filter_prioritas)
    
    if tasks:
        # Tampilkan statistik
        col1, col2, col3, col4 = st.columns(4)
        total = len(tasks)
        selesai = len([t for t in tasks if t['status'] == 'Selesai'])
        sedang = len([t for t in tasks if t['status'] == 'Sedang Dikerjakan'])
        belum = len([t for t in tasks if t['status'] == 'Belum'])
        
        with col1:
            st.metric("📊 Total Tugas", total)
        with col2:
            st.metric("✅ Selesai", selesai)
        with col3:
            st.metric("🔄 Sedang Dikerjakan", sedang)
        with col4:
            st.metric("⏳ Belum", belum)
        
        st.markdown("---")
        
        # Tampilkan tabel tugas
        for task in tasks:
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 1.5, 1.5, 1, 1])
                
                with col1:
                    st.markdown(f"**{task['judul']}**")
                
                with col2:
                    deadline_str = task['deadline'].strftime('%d %B %Y') if isinstance(task['deadline'], datetime) else task['deadline']
                    st.text(f"📅 {deadline_str}")
                
                with col3:
                    prioritas_warna = {
                        'Tinggi': '🔴',
                        'Sedang': '🟡',
                        'Rendah': '🟢'
                    }
                    st.text(f"{prioritas_warna.get(task['prioritas'], '')} {task['prioritas']}")
                
                with col4:
                    status_warna = {
                        'Selesai': '✅',
                        'Sedang Dikerjakan': '🔄',
                        'Belum': '⏳'
                    }
                    st.text(f"{status_warna.get(task['status'], '')} {task['status']}")
                
                with col5:
                    if st.button("✏️", key=f"edit_{task['id']}", use_container_width=True):
                        edit_popup(task)
                
                with col6:
                    if st.button("🗑️", key=f"hapus_{task['id']}", type="primary", use_container_width=True):
                        hapus_popup(task['id'], task['judul'])
                
                st.markdown("---")
    else:
        st.info("📭 Belum ada tugas. Tambahkan tugas baru di tab 'Tambah Tugas'!")

# ==========================================
# 5. FOOTER
# ==========================================
st.markdown("---")
st.caption(f"© 2026 To-Do List App | Dibuat dengan Streamlit | Terakhir diperbarui: {datetime.now().strftime('%d %B %Y %H:%M')}")