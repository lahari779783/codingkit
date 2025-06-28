from flask import Flask, render_template, request, redirect, url_for, session ,flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Required for sessions

# ✅ SQLite DB connection function
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# 🔁 Redirect home to login page
@app.route('/')
def home():
    return redirect(url_for('login'))

# ✅ Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Safe way (recommended)
        email = request.form.get('email')
        password = request.form.get('password')


        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            flash('❌ Invalid email or password.', 'danger')
            return render_template('login.html')

    return render_template('login.html')

# ✅ Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_pw = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                           (username, email, hashed_pw))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            # email already exists (due to UNIQUE constraint)
            flash('⚠️ Email already registered. Please log in.', 'warning')
            return render_template('register.html')

    return render_template('register.html')

# ✅ Dashboard (after login)
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return f"Welcome {session['username']}!"
    return redirect(url_for('login'))

# ✅ Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/index')
def index():
    return render_template('index.html')


# ✅ Run the app
if __name__ == '__main__':
    app.run(debug=True)
