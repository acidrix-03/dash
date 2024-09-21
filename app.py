from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pandas as pd
from io import BytesIO
from flask_babel import Babel

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')

# Babel setup for multi-language support
babel = Babel(app)

# UPLOAD FOLDER for file uploads
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

# Database setup
def init_db():
    try:
        with sqlite3.connect('users.db') as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             name TEXT NOT NULL,
                             username TEXT NOT NULL UNIQUE,
                             password TEXT NOT NULL,
                             role TEXT NOT NULL)''')
            admin_password = generate_password_hash('12345', method='pbkdf2:sha256')
            conn.execute('''INSERT OR IGNORE INTO users (name, username, password, role)
                            VALUES ('Admin', 'Admin', ?, 'admin')''', (admin_password,))
            conn.commit()
        print("Database initialized successfully")
    except sqlite3.DatabaseError as db_err:
        print(f"Database error: {db_err}")
    except Exception as e:
        print(f"General error: {e}")

    with sqlite3.connect('documents.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS travel_authority
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         name TEXT NOT NULL,
                         position TEXT NOT NULL,
                         date TEXT NOT NULL,
                         purpose TEXT NOT NULL,
                         host TEXT NOT NULL,
                         start_date TEXT NOT NULL,
                         end_date TEXT NOT NULL,
                         destination TEXT NOT NULL)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS cto_application
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         name TEXT NOT NULL,
                         position TEXT NOT NULL,
                         days INTEGER NOT NULL,
                         start_date TEXT NOT NULL,
                         end_date TEXT NOT NULL)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS leave_application
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         name TEXT NOT NULL,
                         position TEXT NOT NULL,
                         days INTEGER NOT NULL,
                         start_date TEXT NOT NULL,
                         end_date TEXT NOT NULL)''')
        conn.commit()

init_db()

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    with sqlite3.connect('users.db') as conn:
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[2]
            session['role'] = user[4]
            if user[4] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        flash('Invalid credentials')
        return redirect(url_for('index'))

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    with sqlite3.connect('documents.db') as conn:
        travel_authorities = conn.execute('SELECT * FROM travel_authority WHERE user_id = ?', (user_id,)).fetchall()
        cto_applications = conn.execute('SELECT * FROM cto_application WHERE user_id = ?', (user_id,)).fetchall()
        leave_applications = conn.execute('SELECT * FROM leave_application WHERE user_id = ?', (user_id,)).fetchall()
    
    return render_template('user_dashboard.html', travel_authorities=travel_authorities, cto_applications=cto_applications, leave_applications=leave_applications)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('register'))
        with sqlite3.connect('users.db') as conn:
            try:
                conn.execute('INSERT INTO users (name, username, password, role) VALUES (?, ?, ?, ?)', 
                             (name, username, generate_password_hash(password, method='pbkdf2:sha256'), 'user'))
                conn.commit()
                flash('Registration successful')
                return redirect(url_for('index'))
            except sqlite3.IntegrityError:
                flash('Username already exists')
                return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/submit_document', methods=['GET', 'POST'])
def submit_document():
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        division = request.form['division']
        document = request.files['document']
        if document and allowed_file(document.filename):
            filename = secure_filename(document.filename)
            document.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('Document uploaded successfully')
        else:
            flash('Invalid file format')
        return redirect(url_for('submit_document'))
    return render_template('submit_document.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    with sqlite3.connect('documents.db') as conn:
        travel_authorities = conn.execute('SELECT * FROM travel_authority').fetchall()
        cto_applications = conn.execute('SELECT * FROM cto_application').fetchall()
        leave_applications = conn.execute('SELECT * FROM leave_application').fetchall()
    return render_template('admin_dashboard.html', travel_authorities=travel_authorities, cto_applications=cto_applications, leave_applications=leave_applications)

@app.route('/view_users')
def view_users():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    per_page = 20
    with sqlite3.connect('users.db') as conn:
        users = conn.execute('SELECT * FROM users LIMIT ? OFFSET ?', (per_page, (page - 1) * per_page)).fetchall()
    return render_template('view_users.html', users=users)

@app.route('/clear_data', methods=['POST'])
def clear_data():
    admin_password = request.form['admin_password']
    with sqlite3.connect('users.db') as conn:
        admin_user = conn.execute('SELECT * FROM users WHERE username = ?', ('Admin',)).fetchone()
        if admin_user and check_password_hash(admin_user[3], admin_password):
            with sqlite3.connect('documents.db') as doc_conn:
                doc_conn.execute('DELETE FROM documents')
                doc_conn.commit()
            flash('All data has been cleared successfully', 'success')
        else:
            flash('Invalid admin password', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/export_excel')
def export_excel():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))

    with sqlite3.connect('documents.db') as conn:
        travel_authorities = pd.read_sql_query('SELECT * FROM travel_authority', conn)
        cto_applications = pd.read_sql_query('SELECT * FROM cto_application', conn)
        leave_applications = pd.read_sql_query('SELECT * FROM leave_application', conn)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        travel_authorities.to_excel(writer, sheet_name='Travel Authorities', index=False)
        cto_applications.to_excel(writer, sheet_name='CTO Applications', index=False)
        leave_applications.to_excel(writer, sheet_name='Leave Applications', index=False)

    output.seek(0)
    return send_file(output, download_name='admin_data.xlsx', as_attachment=True)

@app.route('/export_users_excel')
def export_users_excel():
    with sqlite3.connect('users.db') as conn:
        users_df = pd.read_sql_query("SELECT * FROM users", conn)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        users_df.to_excel(writer, sheet_name='Users', index=False)
    
    output.seek(0)
    return send_file(output, download_name='users_data.xlsx', as_attachment=True)

@app.route('/import_users_excel', methods=['POST'])
def import_users_excel():
    file = request.files['file']  # Handle file upload from the form
    if not file:
        flash('No file selected', 'error')
        return redirect(url_for('admin_dashboard'))

    try:
        users_df = pd.read_excel(file)
        
        # Hash the passwords
        users_df['password'] = users_df['password'].apply(lambda x: generate_password_hash(x, method='pbkdf2:sha256'))

        with sqlite3.connect('users.db') as conn:
            for _, row in users_df.iterrows():
                try:
                    conn.execute('INSERT INTO users (name, username, password, role) VALUES (?, ?, ?, ?)', 
                                 (row['name'], row['username'], row['password'], row['role']))
                except sqlite3.IntegrityError:
                    flash(f"User {row['username']} already exists", 'warning')
        
        flash('Users imported successfully', 'success')
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        flash(f"Error importing users: {e}", 'error')
        return redirect(url_for('admin_dashboard'))


@app.route('/cto_application', methods=['GET', 'POST'])
def cto_application():
    if request.method == 'POST':
        name = request.form['name']
        position = request.form['position']
        days = request.form['days']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        user_id = session['user_id']  # Assuming user is logged in
        
        with sqlite3.connect('documents.db') as conn:
            conn.execute('''INSERT INTO cto_application (name, position, days, start_date, end_date, user_id)
                            VALUES (?, ?, ?, ?, ?, ?)''', (name, position, days, start_date, end_date, user_id))
            conn.commit()
        
        flash('CTO Application submitted successfully!')
        return redirect(url_for('user_dashboard'))
    
    return render_template('cto_application.html')


@app.route('/leave_application', methods=['GET', 'POST'])
def leave_application():
    if request.method == 'POST':
        name = request.form['name']
        position = request.form['position']
        days = request.form['days']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        leave_type = request.form['leave_type']
        user_id = session['user_id']  # Assuming user is logged in
        
        with sqlite3.connect('documents.db') as conn:
            conn.execute('''INSERT INTO leave_application (name, position, days, start_date, end_date, leave_type, user_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?)''', (name, position, days, start_date, end_date, leave_type, user_id))
            conn.commit()
        
        flash('Leave Application submitted successfully!')
        return redirect(url_for('user_dashboard'))
    
    return render_template('leave_application.html')


@app.route('/travel_authority', methods=['GET', 'POST'])
def travel_authority():
    if request.method == 'POST':
        name = request.form['name']
        position = request.form['position']
        date = request.form['date']
        purpose = request.form['purpose']
        host = request.form['host']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        destination = request.form['destination']
        user_id = session['user_id']  # Assuming user is logged in
        
        with sqlite3.connect('documents.db') as conn:
            conn.execute('''INSERT INTO travel_authority (name, position, date, purpose, host, start_date, end_date, destination, user_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (name, position, date, purpose, host, start_date, end_date, destination, user_id))
            conn.commit()
        
        flash('Travel Authority submitted successfully!')
        return redirect(url_for('user_dashboard'))
    
    return render_template('travel_authority.html')



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Get the PORT from environment, default to 5000
    app.run(debug=True, host='0.0.0.0', port=port)