from flask import Flask, render_template, request, redirect, url_for, session , send_file
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import os
import plotly.express as px
import plotly.io as pio
import json
import plotly.utils 
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'

# ตั้งค่าการเชื่อมต่อกับฐานข้อมูล
db_config = {
    'user': 'root',
    'password': 'queen2545',
    'host': 'localhost',
    'database': 'user_login'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def home():
    if 'username' in session:
        uploaded_files = get_uploaded_files()  # ดึงรายการไฟล์ที่อัปโหลดแล้ว
        username = session['username']
        return render_template('home.html', username=username, uploaded_files=uploaded_files)
    else:
        return redirect(url_for('login'))  # ถ้ายังไม่ได้ล็อกอิน ให้ไปที่หน้าล็อกอิน

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['username'] = user[1]  # เก็บชื่อผู้ใช้ใน session
            session['role'] = user[3]  # เก็บบทบาทของผู้ใช้ใน session
            # ตรวจสอบบทบาทของผู้ใช้
            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))  # ส่งไปยังหน้า admin
            return redirect(url_for('home'))  # ส่งไปยังหน้า home สำหรับผู้ใช้ทั่วไป
        else:
            return 'Invalid credentials'
    return render_template('login.html', username=session.get('username'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, hashed_password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html', username=session.get('username'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)  # ลบบทบาทผู้ใช้จาก session
    return redirect(url_for('login'))


# ฟังก์ชันเพื่อดึงรายการไฟล์จากโฟลเดอร์ uploads
def get_uploaded_files():
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        return []
    return [f for f in os.listdir(upload_folder) if f.endswith('.xlsx')] #only .xlsx
    #return os.listdir(upload_folder)  # ดึงรายการไฟล์ทั้งหมดจากโฟลเดอร์ uploads


@app.route('/upload', methods=['POST', 'GET'])
def upload_file():
    global data_frame
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file part"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        if file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            # อ่านข้อมูลจากไฟล์ Excel
            data_frame = pd.read_excel(file_path)

            # แสดงข้อมูลทั้งหมดใน DataFrame
            all_data_html = data_frame.to_html(classes='data')  # แสดงข้อมูลทั้งหมด

            # ตรวจสอบและกรองข้อมูลใน DataFrame
            numeric_df = data_frame.select_dtypes(include=['number'])  # เลือกเฉพาะคอลัมน์ที่เป็นตัวเลข

            if numeric_df.empty:
                return "No numeric data found in the uploaded file."
            
            # บันทึกประวัติการอัปโหลดไฟล์ลงฐานข้อมูล
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO upload_history (username, file_name) VALUES (%s, %s)', (session['username'], file.filename))
            conn.commit()
            conn.close()

    return render_template('select_analysis.html', columns=numeric_df.columns, data=numeric_df.to_html(classes='data'),all_data=all_data_html, username=session.get('username'))

 

@app.route('/use_uploaded_file/<filename>')
def use_uploaded_file(filename):
    global data_frame
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        # อ่านไฟล์ที่เคยอัปโหลด
        data_frame = pd.read_excel(file_path)
        # แสดงข้อมูลทั้งหมดใน DataFrame
        all_data_html = data_frame.to_html(classes='data')  # แสดงข้อมูลทั้งหมด

        # ตรวจสอบและกรองข้อมูลใน DataFrame
        numeric_df = data_frame.select_dtypes(include=['number'])  # เลือกเฉพาะคอลัมน์ที่เป็นตัวเลข

        if numeric_df.empty:
            return "No numeric data found in the uploaded file."

        return render_template('select_analysis.html', columns=numeric_df.columns, data=numeric_df.to_html(classes='data'),all_data=all_data_html, username=session.get('username'))

    except FileNotFoundError:
        return "The selected file was not found."

data_frame = None    

@app.route('/analyze', methods=['POST'])
def analyze_data():
    global data_frame 
    analysis_type = request.form['analysis_type']
    selected_columns = request.form.getlist('column_name')  # ดึงค่าจากหลายคอลัมน์
    graph_type = request.form['graph_type']  # รับประเภทกราฟที่เลือก

    results = {}
    for selected_column in selected_columns:
        # คำนวณตามประเภทการวิเคราะห์ที่เลือก
        if analysis_type == 'mean':
            result = data_frame[selected_column].mean()
        elif analysis_type == 'median':
            result = data_frame[selected_column].median()
        elif analysis_type == 'mode':
            result = data_frame[selected_column].mode()[0]  # เอาผลลัพธ์แรกของ mode
        else:
            result = "Invalid analysis type or missing required columns"

        results[selected_column] = result

    # สร้างกราฟตามประเภทที่เลือก
    if graph_type == 'line':
        fig = px.line(data_frame, x=data_frame.index, y=selected_columns, title=f'{graph_type.capitalize()} of Selected Columns')
    elif graph_type == 'bar':
        fig = px.bar(data_frame, x=data_frame.index, y=selected_columns, title=f'{graph_type.capitalize()} of Selected Columns')
    elif graph_type == 'pie':
        if len(selected_columns) == 1:
            fig = px.pie(data_frame, names=data_frame.index, values=selected_columns[0], title=f'{graph_type.capitalize()} of {selected_columns[0]}')
        else:
            return "Pie chart requires exactly one column."
    else:
        return "Invalid graph type selected."
    # สร้างกราฟ
    #fig = px.histogram(data_frame, x=selected_column, title=f'Distribution of {selected_column}') # distrogram
    #fig = px.line(data_frame, x=data_frame.index, y=selected_column, title=f'Trend of {selected_column}') #กราฟเส้น
    
    # แปลงเป็น JSON
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # บันทึกกราฟเป็นไฟล์ภาพ
    image_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'analysis_graph.png')
    pio.write_image(fig, image_file_path)

    # สร้าง DataFrame สำหรับผลลัพธ์
    result_df = pd.DataFrame({
        'Analysis Type': [analysis_type],
        'Column': [selected_column],
        'Result': [result]
    })

    # บันทึก DataFrame เป็น CSV
    csv_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'analysis_result.csv')
    result_df.to_csv(csv_file_path, index=False)

    # ส่งค่า column name กลับไปยัง result.html
    return render_template('result.html', results=results, analysis_type=analysis_type, columns=selected_columns, username=session.get('username'), graph_json=graph_json, csv_file=f'{selected_column}_analysis_result.csv', image_file=f'{selected_column}_analysis_graph.png')

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(file_path, as_attachment=True)

# ตรวจสอบว่าผู้ใช้เป็น Admin หรือไม่
def admin_required(func):
    def wrapper(*args, **kwargs):
        if 'role' in session and session['role'] == 'admin':
            return func(*args, **kwargs)
        else:
            return "Unauthorized", 403
    wrapper.__name__ = func.__name__
    return wrapper

# ฟังก์ชันแสดง Admin Dashboard
@app.route('/admin')
@admin_required
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        conn = get_db_connection()
        cursor = conn.cursor()

        # ดึงข้อมูลผู้ใช้ทั้งหมด
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()

        # ดึงประวัติการอัปโหลดไฟล์
        cursor.execute('SELECT * FROM upload_history')
        uploads = cursor.fetchall()

        conn.close()
        return render_template('admin_dashboard.html', users=users, uploads=uploads, username=session['username'])
    return redirect(url_for('home'))  # ถ้าไม่ใช่ admin ให้กลับไปที่หน้า home


# ฟังก์ชันลบผู้ใช้
@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_dashboard'))

# ฟังก์ชันเลื่อนขั้นผู้ใช้เป็น Admin
@app.route('/admin/promote_user/<int:user_id>', methods=['POST'])
@admin_required
def promote_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('UPDATE users SET role = %s WHERE id = %s', ('admin', user_id))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_dashboard'))



if __name__ == '__main__':
    app.run(debug=True)
