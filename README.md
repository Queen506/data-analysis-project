# Data Analysis Application

## วิธีการรัน

1. Clone หรือดาวน์โหลดโปรเจ็กต์นี้
2. เปิด Terminal (หรือ Command Prompt) และนำทางไปยังโฟลเดอร์โปรเจ็กต์
3. ติดตั้งไลบรารีที่จำเป็น โดยใช้คำสั่ง pip install -r requirements.txt
4. สร้างฐานข้อมูลMysql
5. แก้ไขข้อมูลในการเชื่อต่อฐานข้อมูล(db_config)ในapp.py
6. รันแอปพลิเคชันโดยใช้คำสั่ง python app.py

//ฐานข้อมูล MySQL

CREATE DATABASE user_db;
USE user_db;

CREATE TABLE users (
id INT AUTO_INCREMENT PRIMARY KEY,
username VARCHAR(100) NOT NULL,
password VARCHAR(100) NOT NULL
);

//เพิ่ม upload_history

CREATE TABLE upload_history (
id INT AUTO_INCREMENT PRIMARY KEY,
username VARCHAR(255),
file_name VARCHAR(255),
upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

//เพิ่ม role

ALTER TABLE users ADD COLUMN role ENUM('user', 'admin') DEFAULT 'user';

//เพิ่ม admin

USE user_login;
SET SQL_SAFE_UPDATES = 0;
UPDATE users
SET role = 'admin'
WHERE username = 'q2';

SET SQL_SAFE_UPDATES = 1;
