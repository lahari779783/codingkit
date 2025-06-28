from flask import Flask, render_template, request, redirect, url_for, session ,flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from urllib.parse import urlparse, parse_qs
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Required for sessions

import os
import shutil
import sqlite3

def get_db_connection():
    is_render = os.environ.get("RENDER") == "true"
    db_source_path = "database.db"
    db_target_path = "/tmp/database.db" if is_render else "database.db"

    # If deploying on Render and db not yet copied
    if is_render and not os.path.exists(db_target_path):
        if os.path.exists(db_source_path):
            shutil.copy(db_source_path, db_target_path)
        else:
            raise FileNotFoundError("❌ 'database.db' not found in root directory!")

    conn = sqlite3.connect(db_target_path)
    conn.row_factory = sqlite3.Row
    return conn


# 🔁 Redirect home to login page
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    video_link = ""
    notes = ""
    video_id = ""

    if request.method == 'POST':
        video_link = request.form.get('video_link')
        notes = request.form.get('notes')
        video_id = extract_video_id(video_link)
    # Fetch buttons from DB
    conn = get_db_connection()
    buttons = conn.execute(
        'SELECT site_name, site_link FROM web_buttons WHERE user_id = ?',
        (session['user_id'],)
    ).fetchall()
    conn.close()

    return render_template(
        'index.html',
        video_link=video_link,
        notes=notes,
        video_id=video_id,
        buttons=buttons
    )


     


# ✅ Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    print("🔄 Entered /login route")

    if request.method == 'POST':
        # Safe way (recommended)
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"📧 Email entered: {email}")
        print(f"🔒 Password entered: {password}")

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user:
            print("✅ User found in database")
            print("📄 Stored hash:", user['password_hash'])

            if  check_password_hash(user['password_hash'], password):
                print("🔐 Password match. Logging in...")            
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('index'))
            else:
                print("❌ Password incorrect")
        else:
            print("❌ No user found with that email")       
        
           
        flash('❌ Invalid email or password.', 'danger')
        return render_template('login.html')
    print("🖥️ GET request - rendering login page")
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


@app.route('/save_history', methods=['POST'])
def save_history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    video_link = request.form.get('video_link')
    notes = request.form.get('notes')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history (user_id, video_link, notes) VALUES (?, ?, ?)",
                   (session['user_id'], video_link, notes))
    conn.commit()
    conn.close()
    flash("✅ History saved successfully.", "success")
    return redirect(url_for('history'))

def extract_video_id(url):
    parsed_url = urlparse(url)
    if "youtube" in parsed_url.netloc:
        query = parse_qs(parsed_url.query)
        return query.get("v", [""])[0]
    elif "youtu.be" in parsed_url.netloc:
        return parsed_url.path.lstrip('/')
    return ""

@app.route('/add_button', methods=['POST'])
def add_button():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    site_name = request.form.get('site_name')  # Name shown on the button
    site_link = request.form.get('site_link')  # Actual URL

    if site_name and site_link:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO web_buttons (user_id, site_name, site_link) VALUES (?, ?, ?)',
            (session['user_id'], site_name, site_link)
        )
        conn.commit()
        conn.close()
        flash('✅ Website button added.', 'success')
    else:
        flash('❌ Please fill both name and link.', 'danger')

    return redirect(url_for('index'))


@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    history = conn.execute('SELECT * FROM history WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('history.html', history=history)


@app.route('/open_history/<int:id>')
def open_history(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM history WHERE id = ? AND user_id = ?",
        (id, session['user_id'])
    )
    history_item = cursor.fetchone()
    conn.close()

    if history_item:
        return render_template(
            'index.html',
            video_link=history_item['video_link'],
            notes=history_item['notes'],
            video_id=extract_video_id(history_item['video_link'])
        )
    else:
        flash("⚠️ History item not found or unauthorized.", "warning")
        return redirect(url_for('history'))



@app.route('/delete_history/<int:id>', methods=['POST'])
def delete_history(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history WHERE id = ? AND user_id = ?", (id, session['user_id']))
    conn.commit()
    conn.close()

    flash("🗑️ History deleted successfully.", "success")
    return redirect(url_for('history'))

# ✅ Run the app
if __name__ == '__main__':
    app.run(debug=True)
