import streamlit as st
import mysql.connector
from datetime import datetime, timedelta

# ==========================================
# PENGATURAN HALAMAN
# ==========================================
st.set_page_config(
    page_title="Aplikasi Manajemen Tugas",
    page_icon="📋",
    layout="wide"
)
st.title("📋 Aplikasi Manajemen Tugas (To-Do List)")

# ==========================================
# CLASS DATABASE
# ==========================================
class DatabaseTodo:
    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = ""
        self.db_name = "todo_app"
        self.init_db()

    def get_connection(self, use_db=True):
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.db_name if use_db else None
        )

    def init_db(self):
        try:
            conn = self.get_connection(use_db=False)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_name}")
            cursor.close()
            conn.close()

            db = self.get_connection(use_db=True)
            cursor = db.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tugas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    judul VARCHAR(100) NOT NULL,
                    deadline DATE NOT NULL,
                    prioritas ENUM('Rendah', 'Sedang', 'Tinggi') NOT NULL,
                    status ENUM('Belum', 'Sedang Dikerjakan', 'Selesai') DEFAULT 'Belum',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.commit()
            cursor.close()
            db.close()
            print("Database siap!")
        except mysql.connector.Error as err:
            st.error(f"Gagal: {err}")

    def tambah_tugas(self, judul, deadline, prioritas):
        try:
            db = self.get_connection()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO tugas (judul, deadline, prioritas) VALUES (%s, %s, %s)",
                (judul, deadline, prioritas)
            )
            db.commit()
            cursor.close()
            db.close()
            return True, f"Berhasil: {judul}"
        except mysql.connector.Error as err:
            return False, f"Gagal: {err}"

    def lihat_tugas(self, keyword="", filter_prioritas=""):
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
            
            query += " ORDER BY deadline ASC, FIELD(prioritas, 'Tinggi', 'Sedang', 'Rendah')"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            for row in rows:
                if row['deadline'] is not None and isinstance(row['deadline'], datetime):
                    row['deadline'] = row['deadline'].strftime('%Y-%m-%d')
                elif row['deadline'] is None:
                    row['deadline'] = datetime.now().strftime('%Y-%m-%d')
            
            cursor.close()
            db.close()
            return rows
        except mysql.connector.Error as err:
            st.error(f"Gagal: {err}")
            return []

    def ubah_tugas(self, id_tugas, judul, deadline, prioritas, status):
        try:
            db = self.get_connection()
            cursor = db.cursor()
            cursor.execute(
                "UPDATE tugas SET judul=%s, deadline=%s, prioritas=%s, status=%s WHERE id=%s",
                (judul, deadline, prioritas, status, id_tugas)
            )
            db.commit()
            cursor.close()
            db.close()
            return True
        except mysql.connector.Error as err:
            st.error(f"Gagal: {err}")
            return False

    def hapus_tugas(self, id_tugas):
        try:
            db = self.get_connection()
            cursor = db.cursor()
            cursor.execute("DELETE FROM tugas WHERE id = %s", (id_tugas,))
            db.commit()
            cursor.close()
            db.close()
            return True
        except mysql.connector.Error as err:
            st.error(f"Gagal: {err}")
            return False

    def get_tugas_deadline(self):
        try:
            db = self.get_connection()
            cursor = db.cursor(dictionary=True)
            
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            cursor.execute("""
                SELECT * FROM tugas 
                WHERE (deadline = %s OR deadline = %s)
                AND status != 'Selesai'
                ORDER BY deadline ASC, FIELD(prioritas, 'Tinggi', 'Sedang', 'Rendah')
            """, (today, tomorrow))
            
            rows = cursor.fetchall()
            for row in rows:
                if row['deadline'] is not None and isinstance(row['deadline'], datetime):
                    row['deadline'] = row['deadline'].strftime('%Y-%m-%d')
                elif row['deadline'] is None:
                    row['deadline'] = datetime.now().strftime('%Y-%m-%d')
            
            cursor.close()
            db.close()
            return rows
        except mysql.connector.Error as err:
            st.error(f"Gagal: {err}")
            return []

# ==========================================
# CLASS TUGAS (INHERITANCE & POLYMORPHISM)
# ==========================================
class Tugas:
    def __init__(self, id, judul, deadline, prioritas, status="Belum"):
        self._id = id
        self._judul = judul
        self._deadline = deadline
        self._prioritas = prioritas
        self._status = status
    
    def get_info(self):
        return f"{self._judul} - {self._prioritas} - {self._status}"

class TugasPrioritas(Tugas):
    def __init__(self, id, judul, deadline, prioritas, status="Belum", catatan=""):
        super().__init__(id, judul, deadline, prioritas, status)
        self.__catatan = catatan
    
    def get_info(self):
        info = super().get_info()
        if self.__catatan:
            info += f" - Catatan: {self.__catatan}"
        return info

# ==========================================
# FUNGSI HELPER
# ==========================================
def parse_date(date_str):
    if date_str is None or date_str == '':
        return datetime.now().date()
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return datetime.now().date()

# ==========================================
# FUNGSI CONVERT PRIORITAS
# ==========================================
def convert_prioritas(prioritas):
    if prioritas == 'Segera!':
        return 'Tinggi'
    elif prioritas == 'Harus Dikerjakan':
        return 'Sedang'
    elif prioritas == 'Bisa Nanti':
        return 'Rendah'
    elif prioritas in ['Tinggi', 'Sedang', 'Rendah']:
        return prioritas
    else:
        return 'Rendah'

# ==========================================
# BUAT OBJEK DATABASE
# ==========================================
db_todo = DatabaseTodo()

# ==========================================
# POP-UP SUKSES TAMBAH TUGAS
# ==========================================
@st.dialog("Tugas Berhasil Ditambahkan!")
def sukses_tambah_popup(judul, deadline, prioritas):
    """Pop-up yang muncul saat tugas berhasil ditambahkan"""
    st.success("🎉 Selamat! Tugas baru telah ditambahkan.")
    st.write("📌 **Detail Tugas:**")
    st.write(f"• **Judul:** {judul}")
    st.write(f"• **Deadline:** {deadline.strftime('%d %B %Y')}")
    st.write(f"• **Prioritas:** {prioritas}")
    
    st.markdown("---")
    if st.button("👍 OK, Saya Tahu", use_container_width=True):
        st.rerun()

# ==========================================
# POP-UP EDIT TUGAS
# ==========================================
@st.dialog("✏️ Edit Tugas")
def edit_popup(tugas):
    st.write(f"Mengubah tugas: **{tugas['judul']}**")
    
    deadline_default = parse_date(tugas.get('deadline'))
    
    judul = st.text_input("Judul Tugas", value=tugas['judul'])
    deadline = st.date_input("Deadline", value=deadline_default)
    
    prioritas_baru = convert_prioritas(tugas['prioritas'])
    
    pilihan_prioritas = ["Rendah", "Sedang", "Tinggi"]
    try:
        index = pilihan_prioritas.index(prioritas_baru)
    except ValueError:
        index = 0
    
    prioritas = st.selectbox("Prioritas", pilihan_prioritas, index=index)
    status = st.selectbox("Status", ["Belum", "Sedang Dikerjakan", "Selesai"],
                         index=["Belum", "Sedang Dikerjakan", "Selesai"].index(tugas['status']))
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Simpan Perubahan", use_container_width=True):
            if db_todo.ubah_tugas(tugas['id'], judul, deadline.strftime('%Y-%m-%d'), prioritas, status):
                st.success("Tugas berhasil diperbarui!")
                st.rerun()
            else:
                st.error("Gagal memperbarui tugas!")
    with col2:
        if st.button("Batal", use_container_width=True):
            st.rerun()

# ==========================================
# POP-UP KONFIRMASI HAPUS
# ==========================================
@st.dialog("⚠️ Konfirmasi Hapus")
def hapus_popup(id_tugas, judul):
    st.write(f"Apakah Anda yakin ingin menghapus tugas berikut?")
    st.write(f"• **Tugas:** {judul}")
    st.write("Tindakan ini permanen dan tidak dapat dibatalkan.")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Ya, Hapus", type="primary", use_container_width=True):
            if db_todo.hapus_tugas(id_tugas):
                st.success(f"✅ Tugas berhasil dihapus!")
                st.rerun()
    with col2:
        if st.button("Batal", use_container_width=True):
            st.rerun()

# ==========================================
# NOTIFIKASI DEADLINE
# ==========================================
def tampilkan_notifikasi():
    tasks = db_todo.get_tugas_deadline()
    if tasks:
        today = datetime.now().date()
        
        with st.container(border=True):
            tugas_hari_ini = []
            tugas_besok = []
            
            for t in tasks:
                tgl = parse_date(t.get('deadline'))
                if tgl == today:
                    tugas_hari_ini.append(t)
                else:
                    tugas_besok.append(t)
            
            if tugas_hari_ini:
                st.error("🚨 **DEADLINE HARI INI!**")
                for t in tugas_hari_ini:
                    if t['prioritas'] == 'Tinggi':
                        icon = '🔴'
                    elif t['prioritas'] == 'Sedang':
                        icon = '🟡'
                    else:
                        icon = '🟢'
                    st.write(f"{icon} **{t['judul']}**")
                st.caption(f"📢 {len(tugas_hari_ini)} tugas deadline HARI INI!")
                st.markdown("---")
            
            if tugas_besok:
                st.info("📌 **DEADLINE BESOK!**")
                for t in tugas_besok:
                    if t['prioritas'] == 'Tinggi':
                        icon = '🔴'
                    elif t['prioritas'] == 'Sedang':
                        icon = '🟡'
                    else:
                        icon = '🟢'
                    st.write(f"{icon} **{t['judul']}**")
                st.caption(f"📢 {len(tugas_besok)} tugas deadline BESOK!")

# ==========================================
# MAIN
# ==========================================
tampilkan_notifikasi()

tab1, tab2 = st.tabs(["➕ Tambah Tugas", "📋 Daftar Tugas"])

# TAB 1: TAMBAH TUGAS
with tab1:
    st.subheader("📝 Tambah Tugas Baru")
    
    with st.form("form_tugas", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            judul = st.text_input("📌 Judul Tugas", placeholder="Masukkan judul tugas...")
            deadline = st.date_input("📅 Deadline", min_value=datetime.today())
        
        with col2:
            prioritas = st.selectbox("🎯 Prioritas", ["Rendah", "Sedang", "Tinggi"])
            st.caption("💡 Prioritas menentukan urutan pengerjaan, deadline menentukan batas waktu.")
        
        submit = st.form_submit_button("➕ Tambah Tugas", use_container_width=True)
        
        if submit:
            if judul and deadline:
                sukses, pesan = db_todo.tambah_tugas(judul, deadline.strftime('%Y-%m-%d'), prioritas)
                if sukses:
                    # POP-UP SUKSES
                    sukses_tambah_popup(judul, deadline, prioritas)
                else:
                    st.error(pesan)
            else:
                st.warning("⚠️ Judul dan deadline harus diisi!")

# TAB 2: DAFTAR TUGAS
with tab2:
    st.subheader("📋 Daftar Tugas")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        keyword = st.text_input("🔍 Cari Tugas", placeholder="Masukkan kata kunci...")
    with col2:
        filter_prioritas = st.selectbox("🎯 Filter Prioritas", ["Semua", "Rendah", "Sedang", "Tinggi"])
    
    tasks = db_todo.lihat_tugas(keyword, filter_prioritas)
    
    if tasks:
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
        
        col_no, col_judul, col_deadline, col_prioritas, col_status, col_edit, col_hapus = st.columns([0.5, 2.5, 1.5, 1.5, 1.2, 0.8, 0.8])
        
        with col_no:
            st.markdown("**No**")
        with col_judul:
            st.markdown("**Judul**")
        with col_deadline:
            st.markdown("**Deadline**")
        with col_prioritas:
            st.markdown("**Prioritas**")
        with col_status:
            st.markdown("**Status**")
        with col_edit:
            st.markdown("**Edit**")
        with col_hapus:
            st.markdown("**Hapus**")
        
        st.markdown("---")
        
        for idx, task in enumerate(tasks, 1):
            col_no, col_judul, col_deadline, col_prioritas, col_status, col_edit, col_hapus = st.columns([0.5, 2.5, 1.5, 1.5, 1.2, 0.8, 0.8])
            
            with col_no:
                st.write(f"**{idx}**")
            with col_judul:
                st.write(task['judul'])
            with col_deadline:
                tgl = parse_date(task.get('deadline'))
                st.write(tgl.strftime('%d %B %Y'))
            with col_prioritas:
                if task['prioritas'] == 'Tinggi':
                    st.write("🔴 Tinggi")
                elif task['prioritas'] == 'Sedang':
                    st.write("🟡 Sedang")
                else:
                    st.write("🟢 Rendah")
            with col_status:
                status_map = {'Selesai': '✅', 'Sedang Dikerjakan': '🔄', 'Belum': '⏳'}
                st.write(f"{status_map.get(task['status'], '')} {task['status']}")
            with col_edit:
                if st.button("✏️", key=f"edit_{task['id']}", use_container_width=True):
                    edit_popup(task)
            with col_hapus:
                if st.button("🗑️", key=f"hapus_{task['id']}", use_container_width=True):
                    hapus_popup(task['id'], task['judul'])
            
            st.markdown("---")
    else:
        st.info("📭 Belum ada tugas. Tambahkan tugas baru di tab 'Tambah Tugas'!")

st.markdown("---")
st.caption("© 2026 Aplikasi Manajemen Tugas")