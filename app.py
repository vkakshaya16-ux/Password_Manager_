import os
import psycopg2
from flask import Flask, render_template, request, redirect
from cryptography.fernet import Fernet

app = Flask(__name__)

# Flask secret (for sessions later if needed)
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret")

# ================= DATABASE =================
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# ================= TABLE =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS passwords (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    site_name VARCHAR(255),
    username VARCHAR(255),
    encrypted_password TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()

# ================= ENCRYPTION =================
key = os.getenv("SECRET_KEY").encode()
cipher = Fernet(key)

def encrypt_password(password):
    return cipher.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    return cipher.decrypt(encrypted_password.encode()).decode()

# ================= ROUTES =================

@app.route('/')
def home():
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    cursor.execute("SELECT * FROM passwords")
    data = cursor.fetchall()

    passwords = []
    for row in data:
        passwords.append({
            "id": row[0],
            "site": row[2],
            "username": row[3],
            "password": decrypt_password(row[4])
        })

    return render_template("dashboard.html", passwords=passwords)

@app.route('/add', methods=['POST'])
def add_password():
    site = request.form['site']
    username = request.form['username']
    password = request.form['password']

    encrypted = encrypt_password(password)

    cursor.execute("""
    INSERT INTO passwords (user_id, site_name, username, encrypted_password)
    VALUES (%s, %s, %s, %s)
    """, (1, site, username, encrypted))

    conn.commit()

    return redirect('/dashboard')

@app.route('/delete/<int:id>')
def delete_password(id):
    cursor.execute("DELETE FROM passwords WHERE id=%s", (id,))
    conn.commit()
    return redirect('/dashboard')


if __name__ == "__main__":
    app.run(debug=True)