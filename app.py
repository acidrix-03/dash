from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pandas as pd
from io import BytesIO
from flask_babel import Babel
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from flask import jsonify

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

    try:
        with sqlite3.connect('documents.db') as conn:
            # Create CTO Application table
            conn.execute('''CREATE TABLE IF NOT EXISTS cto_application (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position TEXT NOT NULL,
                days INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                recommending_approval TEXT DEFAULT NULL, 
                approval_status TEXT DEFAULT 'Pending',
                date_approved TEXT DEFAULT NULL   
            )''')

            # Create a table for recommended applications
            conn.execute('''CREATE TABLE IF NOT EXISTS recommended_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id INTEGER NOT NULL,
                app_type TEXT NOT NULL,
                name TEXT NOT NULL,
                position TEXT NOT NULL,
                days INTEGER,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                destination TEXT,
                purpose TEXT,
                leave_type TEXT,
                date_recommended TEXT NOT NULL
            )''')

            # Create a table for approved applications
            conn.execute('''CREATE TABLE IF NOT EXISTS approved_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_type TEXT NOT NULL,
                name TEXT NOT NULL,
                position TEXT NOT NULL,
                days INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                destination TEXT,
                purpose TEXT,
                date_recommended TEXT NOT NULL
            )''')

            # Create Leave Application table
            conn.execute('''CREATE TABLE IF NOT EXISTS leave_application (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position TEXT NOT NULL,
                days INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                recommending_approval TEXT DEFAULT NULL, 
                approval_status TEXT DEFAULT 'Pending',
                date_approved TEXT DEFAULT NULL
            )''')

            # Create Travel Authority table
            conn.execute('''CREATE TABLE IF NOT EXISTS travel_authority (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position TEXT NOT NULL,
                purpose TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                destination TEXT NOT NULL,
                recommending_approval TEXT DEFAULT NULL, 
                approval_status TEXT DEFAULT 'Pending',
                date_approved TEXT DEFAULT NULL 
            )''')
        print("Database initialized successfully")
    except sqlite3.DatabaseError as db_err:
        print(f"Database error: {db_err}")
    except Exception as e:
        print(f"General error: {e}")

import sqlite3

def add_rejection_comment_column():
    with sqlite3.connect('documents.db') as conn:
        # Adding rejection_comment column to cto_application
        conn.execute('ALTER TABLE cto_application ADD COLUMN rejection_comment TEXT;')
        conn.execute('ALTER TABLE leave_application ADD COLUMN rejection_comment TEXT;')
        conn.execute('ALTER TABLE travel_authority ADD COLUMN rejection_comment TEXT;')
        conn.commit()
        print("Columns added successfully.")

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/add_column')
def add_column():
    try:
        with sqlite3.connect('documents.db') as conn:
            conn.execute('ALTER TABLE recommended_applications ADD COLUMN recommending_approval TEXT')
        return "Column 'recommending_approval' added successfully!"
    except sqlite3.OperationalError as e:
        return f"Error: {e}"
    
@app.route('/add_recommending_approval_column')
def add_recommending_approval_column():
    try:
        with sqlite3.connect('documents.db') as conn:
            conn.execute('ALTER TABLE recommended_applications ADD COLUMN recommending_approval TEXT')
        return "Column 'recommending_approval' added successfully!"
    except sqlite3.OperationalError as e:
        return f"Error: {e}"

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    name = request.form['username']
    password = request.form['password']
    with sqlite3.connect('users.db') as conn:
        user = conn.execute('SELECT * FROM users WHERE name = ?', (name,)).fetchone()
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[2]
            session['role'] = user[4]

            # Redirect based on user role
            if user[4] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user[4] == 'approver':
                return redirect(url_for('approver_dashboard'))
            elif user[4] == 'recommender':
                return redirect(url_for('recommender_dashboard'))
            elif user[4] == 'unit_head':
                return redirect(url_for('unit_head_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('index'))

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('index'))
    
    user_id = session['user_id']

    # Fetch user details from users.db (e.g., office and salary)
    with sqlite3.connect('users.db') as conn:
        user_details = conn.execute('SELECT office, salary FROM users WHERE id = ?', (user_id,)).fetchone()

    # Fetch applications from documents.db
    with sqlite3.connect('documents.db') as conn:
        # Fetch the CTO applications
        cto_applications = conn.execute('SELECT id, name, position, days, start_date, end_date, recommending_approval, approval_status, date_recommended FROM cto_application WHERE user_id = ?', (user_id,)).fetchall()
        
        # Fetch the leave applications
        leave_applications = conn.execute('SELECT id, name, position, days, start_date, end_date, leave_type, recommending_approval, approval_status, date_recommended FROM leave_application WHERE user_id = ?', (user_id,)).fetchall()
        
        # Fetch the travel authority applications
        travel_authorities = conn.execute('SELECT id, name, position, purpose, start_date, end_date, destination, recommending_approval, approval_status FROM travel_authority WHERE user_id = ?', (user_id,)).fetchall()

        # Fetch the count of pending, recommended, and approved applications
        pending_count = conn.execute('SELECT COUNT(*) FROM leave_application WHERE user_id = ? AND approval_status = "Pending"', (user_id,)).fetchone()[0]
        recommended_count = conn.execute('SELECT COUNT(*) FROM leave_application WHERE user_id = ? AND approval_status = "Recommended"', (user_id,)).fetchone()[0]
        approved_count = conn.execute('SELECT COUNT(*) FROM leave_application WHERE user_id = ? AND approval_status = "Approved"', (user_id,)).fetchone()[0]
    
    stats = {
        'pending': pending_count,
        'recommended': recommended_count,
        'approved': approved_count
    }

    # Pass all relevant data to the template
    return render_template('user_dashboard.html', 
                           user_details=user_details, 
                           stats=stats, 
                           cto_applications=cto_applications, 
                           leave_applications=leave_applications, 
                           travel_authorities=travel_authorities)


def get_user_info_and_stats(user_id):
    with sqlite3.connect('users.db') as conn:
        user_details = conn.execute('SELECT office, salary FROM users WHERE id = ?', (user_id,)).fetchone()

    with sqlite3.connect('documents.db') as conn:
        pending_count = conn.execute('SELECT COUNT(*) FROM leave_application WHERE user_id = ? AND approval_status = "Pending"', (user_id,)).fetchone()[0]
        recommended_count = conn.execute('SELECT COUNT(*) FROM leave_application WHERE user_id = ? AND approval_status = "Recommended"', (user_id,)).fetchone()[0]
        approved_count = conn.execute('SELECT COUNT(*) FROM leave_application WHERE user_id = ? AND approval_status = "Approved"', (user_id,)).fetchone()[0]
    
    stats = {
        'pending': pending_count,
        'recommended': recommended_count,
        'approved': approved_count
    }
    
    return user_details, stats


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
        # Count all applications
        total_cto_applications = conn.execute('SELECT COUNT(*) FROM cto_application').fetchone()[0]
        total_leave_applications = conn.execute('SELECT COUNT(*) FROM leave_application').fetchone()[0]
        total_travel_authorities = conn.execute('SELECT COUNT(*) FROM travel_authority').fetchone()[0]
        
        # Count pending applications
        pending_cto_applications = conn.execute('SELECT COUNT(*) FROM cto_application WHERE approval_status = "Pending"').fetchone()[0]
        pending_leave_applications = conn.execute('SELECT COUNT(*) FROM leave_application WHERE approval_status = "Pending"').fetchone()[0]
        pending_travel_authorities = conn.execute('SELECT COUNT(*) FROM travel_authority WHERE approval_status = "Pending"').fetchone()[0]

        # Count applications for recommending
        recommending_cto_applications = conn.execute('SELECT COUNT(*) FROM cto_application WHERE recommending_approval IS NOT NULL AND approval_status = "Pending"').fetchone()[0]
        recommending_leave_applications = conn.execute('SELECT COUNT(*) FROM leave_application WHERE recommending_approval IS NOT NULL AND approval_status = "Pending"').fetchone()[0]
        recommending_travel_authorities = conn.execute('SELECT COUNT(*) FROM travel_authority WHERE recommending_approval IS NOT NULL AND approval_status = "Pending"').fetchone()[0]

        # Count approved applications
        approved_cto_applications = conn.execute('SELECT COUNT(*) FROM cto_application WHERE approval_status = "Approved"').fetchone()[0]
        approved_leave_applications = conn.execute('SELECT COUNT(*) FROM leave_application WHERE approval_status = "Approved"').fetchone()[0]
        approved_travel_authorities = conn.execute('SELECT COUNT(*) FROM travel_authority WHERE approval_status = "Approved"').fetchone()[0]

    return render_template('admin_dashboard.html', 
                           total_cto=total_cto_applications,
                           total_leave=total_leave_applications,
                           total_travel=total_travel_authorities,
                           pending_cto=pending_cto_applications,
                           pending_leave=pending_leave_applications,
                           pending_travel=pending_travel_authorities,
                           recommending_cto=recommending_cto_applications,
                           recommending_leave=recommending_leave_applications,
                           recommending_travel=recommending_travel_authorities,
                           approved_cto=approved_cto_applications,
                           approved_leave=approved_leave_applications,
                           approved_travel=approved_travel_authorities)

@app.route('/view_users')
def view_users():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))

    search = request.args.get('search', '')
    letter = request.args.get('letter', '')
    page = request.args.get('page', 1, type=int)  # Current page number (default is 1)
    per_page = 20  # Number of users per page

    query = 'SELECT id, name, username, position, role FROM users WHERE 1=1'
    params = []

    if search:
        query += ' AND (name LIKE ? OR username LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])

    if letter:
        query += ' AND (name LIKE ? OR username LIKE ?)'
        params.extend([f'{letter}%', f'{letter}%'])

    query += ' LIMIT ? OFFSET ?'
    params.extend([per_page, (page - 1) * per_page])

    with sqlite3.connect('users.db') as conn:
        total_users = conn.execute('SELECT COUNT(*) FROM users WHERE 1=1').fetchone()[0]
        users = conn.execute(query, params).fetchall()

    # Calculate total pages
    total_pages = (total_users + per_page - 1) // per_page

    return render_template('view_users.html', users=users, page=page, total_pages=total_pages, search=search, letter=letter)


@app.route('/clear_data', methods=['POST'])
def clear_data():
    admin_password = request.form['admin_password']
    with sqlite3.connect('users.db') as conn:
        admin_user = conn.execute('SELECT * FROM users WHERE username = ?', ('Admin',)).fetchone()
        if admin_user and check_password_hash(admin_user[3], admin_password):
            with sqlite3.connect('documents.db') as doc_conn:
                # Clear all application data
                doc_conn.execute('DELETE FROM cto_application')
                doc_conn.execute('DELETE FROM leave_application')
                doc_conn.execute('DELETE FROM travel_authority')
                # Clear recommended and approved applications as well
                doc_conn.execute('DELETE FROM recommended_applications')
                doc_conn.execute('DELETE FROM approved_applications')
                doc_conn.commit()
            flash('All data has been cleared successfully', 'success')
        else:
            flash('Invalid admin password', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/change_position', methods=['GET', 'POST'])
def change_position():
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        new_position = request.form['position']
        
        with sqlite3.connect('users.db') as conn:
            conn.execute('UPDATE users SET position = ? WHERE id = ?', (new_position, session['user_id']))
            conn.commit()
        
        session['position'] = new_position  # Update session with new position
        flash('Position updated successfully.')
        return redirect(url_for('user_dashboard'))

    # Check if 'position' exists in session
    current_position = session.get('position', 'Not set')  # Use default value if not set
    return render_template('change_position.html', current_position=current_position)


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
        
        # Convert all passwords to strings before hashing
        users_df['password'] = users_df['password'].astype(str)
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

@app.route('/cancel_application/<app_type>/<int:app_id>', methods=['DELETE'])
def cancel_application(app_type, app_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Access denied'}), 403

    try:
        with sqlite3.connect('documents.db') as conn:
            if app_type == 'cto':
                conn.execute('DELETE FROM cto_application WHERE id = ?', (app_id,))
            elif app_type == 'leave':
                conn.execute('DELETE FROM leave_application WHERE id = ?', (app_id,))
            elif app_type == 'travel_authority':
                conn.execute('DELETE FROM travel_authority WHERE id = ?', (app_id,))
            conn.commit()

        return jsonify({'success': 'Application cancelled successfully'})
    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': 'Failed to cancel application'}), 500


@app.route('/reject_application/<int:app_id>', methods=['POST'])
def reject_application(app_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Access denied'}), 403

    user_role = session.get('role')
    if user_role not in ['approver', 'unit_head', 'recommender']:
        return jsonify({'error': 'Access denied'}), 403

    rejection_comment = request.form.get('rejection_comment')
    application_type = request.form.get('application_type')  # Get the application type from the request

    with sqlite3.connect('documents.db') as conn:
        if application_type == 'cto':
            conn.execute('''
                UPDATE cto_application 
                SET approval_status = 'Rejected', rejection_comment = ? 
                WHERE id = ?
            ''', (rejection_comment, app_id))
        elif application_type == 'leave':
            conn.execute('''
                UPDATE leave_application 
                SET approval_status = 'Rejected', rejection_comment = ? 
                WHERE id = ?
            ''', (rejection_comment, app_id))
        elif application_type == 'travel_authority':
            conn.execute('''
                UPDATE travel_authority 
                SET approval_status = 'Rejected', rejection_comment = ? 
                WHERE id = ?
            ''', (rejection_comment, app_id))

        # Commit the changes
        conn.commit()

    return jsonify({'success': True})


@app.route('/cto_application', methods=['GET', 'POST'])
def cto_application():
    user_id = session['user_id']  # Get the logged-in user's ID

    if request.method == 'POST':
        # Handle form submission
        name = request.form['name']
        position = request.form['position']
        days = request.form['days']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        recommending_approval = request.form['recommending_approval']

        # Insert the new CTO application into the database
        with sqlite3.connect('documents.db') as conn:
            conn.execute('''INSERT INTO cto_application (name, position, days, start_date, end_date, user_id, recommending_approval)
                            VALUES (?, ?, ?, ?, ?, ?, ?)''', (name, position, days, start_date, end_date, user_id, recommending_approval))
            conn.commit()

        flash('CTO Application submitted successfully!')
        return redirect(url_for('user_dashboard'))

    else:
        # Fetch existing CTO application for this user
        with sqlite3.connect('documents.db') as conn:
            conn.row_factory = sqlite3.Row  # Allows access to rows as dictionaries
            cto_application = conn.execute('SELECT * FROM cto_application WHERE user_id = ?', (user_id,)).fetchone()

        # Fetch Unit Head and Recommender usernames for the dropdown
        with sqlite3.connect('users.db') as conn:
            unit_heads = conn.execute('SELECT username FROM users WHERE role = "unit_head"').fetchall()
            recommenders = conn.execute('SELECT username FROM users WHERE role = "recommender"').fetchall()

        approving_users = [uh[0] for uh in unit_heads] + [rec[0] for rec in recommenders]

        # Pass the existing application (if any) to the template
        return render_template('cto_application.html', approving_users=approving_users, cto_application=cto_application)


@app.route('/print_cto_application/<int:cto_id>')
def print_cto_application(cto_id):
    with sqlite3.connect('documents.db') as conn:
        conn.row_factory = sqlite3.Row  # Allows accessing rows as dictionaries
        # Fetch all required fields from cto_application
        cto_application = conn.execute('''
            SELECT name, position, days, start_date, end_date, recommending_approval 
            FROM cto_application 
            WHERE id = ?
        ''', (cto_id,)).fetchone()

    if not cto_application:
        return "CTO Application not found.", 404

    # Render the print template with the application details
    return render_template('cto_print_template.html', 
                           name=cto_application['name'], 
                           position=cto_application['position'], 
                           days=cto_application['days'], 
                           start_date=cto_application['start_date'], 
                           end_date=cto_application['end_date'],
                           recommending_approval=cto_application['recommending_approval'])


@app.route('/submit_and_print_cto_application', methods=['POST'])
def submit_and_print_cto_application():
    user_id = session['user_id']  # Get the logged-in user's ID
    
    # Get form data
    name = request.form['name']
    position = request.form['position']
    days = request.form['days']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    recommending_approval = request.form['recommending_approval']
    
    # Insert the new CTO application into the database
    with sqlite3.connect('documents.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cto_application (name, position, days, start_date, end_date, user_id, recommending_approval)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, position, days, start_date, end_date, user_id, recommending_approval))
        conn.commit()

        # Get the last inserted ID
        cto_id = cursor.lastrowid

    # Redirect to the print view with the newly created CTO application
    return redirect(url_for('print_cto_application', cto_id=cto_id))

@app.route('/leave_application', methods=['GET', 'POST'])
def leave_application():
    if request.method == 'POST':
        name = request.form['name']
        position = request.form['position']
        office = request.form['office']  # Capture office
        salary = request.form['salary']  # Capture salary
        days = request.form['days']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        leave_type = request.form['leave_type']
        recommending_approval = request.form['recommending_approval']
        user_id = session['user_id']  # Assuming user is logged in

        # Store the data in the database
        with sqlite3.connect('documents.db') as conn:
            conn.execute('''
                INSERT INTO leave_application (name, position, office, salary, days, start_date, end_date, leave_type, user_id, recommending_approval)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, position, office, salary, days, start_date, end_date, leave_type, user_id, recommending_approval))
            conn.commit()

        flash('Leave Application submitted successfully!')
        return redirect(url_for('user_dashboard'))

    # Fetch Unit Heads and Recommenders for the dropdown
    with sqlite3.connect('users.db') as conn:
        unit_heads = conn.execute('SELECT username FROM users WHERE role = "unit_head"').fetchall()
        recommenders = conn.execute('SELECT username FROM users WHERE role = "recommender"').fetchall()

    approving_users = [uh[0] for uh in unit_heads] + [rec[0] for rec in recommenders]

    # Fetch user details for the sidebar
    user_details, stats = get_user_info_and_stats(session['user_id'])

    # Pass approving_users, user_details, and stats to the template
    return render_template('leave_application.html', approving_users=approving_users, user_details=user_details, stats=stats)


@app.route('/travel_authority', methods=['GET', 'POST'])
def travel_authority():
    if request.method == 'POST':
        name = request.form['name']
        position = request.form['position']
        purpose = request.form['purpose']
        host = request.form['host']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        destination = request.form['destination']
        recommending_approval = request.form['recommending_approval']  # Capture selected recommender
        user_id = session['user_id']  # Logged-in user

        with sqlite3.connect('documents.db') as conn:
            conn.execute('''
                INSERT INTO travel_authority 
                (name, position, purpose, host, start_date, end_date, destination, user_id, recommending_approval)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, position, purpose, host, start_date, end_date, destination, user_id, recommending_approval))
            conn.commit()

        flash('Travel Authority submitted successfully!')
        return redirect(url_for('user_dashboard'))

    # Fetch recommenders and unit heads for the dropdown
    with sqlite3.connect('users.db') as conn:
        recommenders = conn.execute('SELECT username FROM users WHERE role = "recommender"').fetchall()
        unit_heads = conn.execute('SELECT username FROM users WHERE role = "unit_head"').fetchall()

    # Combine the results into a single list
    approving_users = [rec[0] for rec in recommenders] + [uh[0] for uh in unit_heads]

    return render_template('travel_authority.html', approving_users=approving_users)


@app.route('/change_role/<int:user_id>', methods=['POST'])
def change_role(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))

    new_role = request.form['role']
    with sqlite3.connect('users.db') as conn:
        conn.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
        conn.commit()

    flash('User role updated successfully', 'success')
    return redirect(url_for('view_users'))

@app.route('/change_password/<int:user_id>', methods=['GET', 'POST'])
def change_password(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('change_password', user_id=user_id))

        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        with sqlite3.connect('users.db') as conn:
            conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))
            conn.commit()
        flash('Password updated successfully', 'success')
        return redirect(url_for('view_users'))

    return render_template('change_password.html', user_id=user_id)

@app.route('/document_tracker')
def document_tracker():
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('index'))
    
    # If you're not querying the documents, just render the page
    return render_template('document_tracker.html')

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))

    try:
        with sqlite3.connect('users.db') as user_conn:
            user = user_conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            if user:
                user_conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
                user_conn.commit()

        with sqlite3.connect('documents.db') as doc_conn:
            doc_conn.execute('DELETE FROM travel_authority WHERE user_id = ?', (user_id,))
            doc_conn.execute('DELETE FROM cto_application WHERE user_id = ?', (user_id,))
            doc_conn.execute('DELETE FROM leave_application WHERE user_id = ?', (user_id,))
            doc_conn.commit()

        flash('User and all associated data deleted successfully', 'success')
    except sqlite3.Error as e:
        flash(f"An error occurred: {e}", 'danger')

    return redirect(url_for('view_users'))

@app.route('/change_password_user', methods=['GET', 'POST'])
def change_password_user():
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('index'))

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('New passwords do not match')
            return redirect(url_for('change_password_user'))

        with sqlite3.connect('users.db') as conn:
            user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            if user and check_password_hash(user[3], current_password):
                hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
                conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, session['user_id']))
                conn.commit()
                flash('Password updated successfully', 'success')
                return redirect(url_for('user_dashboard'))
            else:
                flash('Current password is incorrect')
                return redirect(url_for('change_password_user'))

    return render_template('change_password_user.html')

@app.route('/approver_dashboard')
def approver_dashboard():
    if 'user_id' not in session or session.get('role') != 'approver':
        flash('Access denied')
        return redirect(url_for('index'))

    approver_username = session['username']  # Correctly fetch the logged-in approver's username

    # Fetch applications assigned for approval
    with sqlite3.connect('documents.db') as conn:
        cto_applications = conn.execute('SELECT * FROM cto_application WHERE recommending_approval = "Recommended" AND approval_status = "Pending"').fetchall()
        leave_applications = conn.execute('SELECT * FROM leave_application WHERE recommending_approval = "Recommended" AND approval_status = "Pending"').fetchall()
        travel_authorities = conn.execute('SELECT * FROM travel_authority WHERE recommending_approval = "Recommended" AND approval_status = "Pending"').fetchall()

    return render_template(
        'approver_dashboard.html',
        cto_applications=cto_applications,
        leave_applications=leave_applications,
        travel_authorities=travel_authorities
    )


@app.route('/approve_application/<int:app_id>', methods=['POST'])
def approve_application(app_id):
    if 'user_id' not in session or session.get('role') != 'approver':
        return jsonify({'error': 'Access denied'}), 403

    application_type = request.form['application_type']
    
    with sqlite3.connect('documents.db') as conn:
        # Fetch the application data based on the type
        if application_type == 'cto':
            application = conn.execute('SELECT name, position, days, start_date, end_date FROM cto_application WHERE id = ?', (app_id,)).fetchone()
            name, position, days, start_date, end_date = application
            conn.execute('UPDATE cto_application SET approval_status = "Approved" WHERE id = ?', (app_id,))
            conn.execute('''INSERT INTO approved_applications 
                            (app_type, name, position, days, start_date, end_date, destination, purpose, date_recommended)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, date("now"))''', 
                            (application_type, name, position, days, start_date, end_date, None, None))
        
        elif application_type == 'leave':
            application = conn.execute('SELECT name, position, days, start_date, end_date FROM leave_application WHERE id = ?', (app_id,)).fetchone()
            name, position, days, start_date, end_date = application
            conn.execute('UPDATE leave_application SET approval_status = "Approved" WHERE id = ?', (app_id,))
            conn.execute('''INSERT INTO approved_applications 
                            (app_type, name, position, days, start_date, end_date, destination, purpose, date_recommended)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, date("now"))''', 
                            (application_type, name, position, days, start_date, end_date, None, None))
        
        elif application_type == 'travel_authority':
            application = conn.execute('SELECT name, position, purpose, start_date, end_date, destination FROM travel_authority WHERE id = ?', (app_id,)).fetchone()
            name, position, purpose, start_date, end_date, destination = application
            conn.execute('UPDATE travel_authority SET approval_status = "Approved" WHERE id = ?', (app_id,))
            conn.execute('''INSERT INTO approved_applications 
                            (app_type, name, position, days, start_date, end_date, destination, purpose, date_recommended)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, date("now"))''', 
                            (application_type, name, position, 0, start_date, end_date, destination, purpose))
        
        conn.commit()
    
    return jsonify({'success': True})

@app.route('/recommend_approval/<int:app_id>', methods=['POST'])
def recommend_approval(app_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Access denied'}), 403

    user_role = session.get('role')
    username = session.get('username')

    # Allow both recommenders and unit heads to recommend approval
    if user_role not in ['recommender', 'unit_head']:
        return jsonify({'error': 'Access denied'}), 403

    application_type = request.form['application_type']

    with sqlite3.connect('documents.db') as conn:
        if application_type == 'cto':
            application = conn.execute('SELECT * FROM cto_application WHERE id = ?', (app_id,)).fetchone()
            conn.execute('UPDATE cto_application SET recommending_approval = "Recommended" WHERE id = ?', (app_id,))
        elif application_type == 'leave':
            application = conn.execute('SELECT * FROM leave_application WHERE id = ?', (app_id,)).fetchone()
            conn.execute('UPDATE leave_application SET recommending_approval = "Recommended" WHERE id = ?', (app_id,))
        elif application_type == 'travel_authority':
            application = conn.execute('SELECT * FROM travel_authority WHERE id = ?', (app_id,)).fetchone()
            conn.execute('UPDATE travel_authority SET recommending_approval = "Recommended" WHERE id = ?', (app_id,))
        else:
            return jsonify({'error': 'Invalid application type'}), 400

        # Insert into recommended_applications table
        conn.execute('''
            INSERT INTO recommended_applications 
            (app_id, app_type, name, position, days, start_date, end_date, destination, purpose, leave_type, date_recommended, recommending_approval)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, date("now"), ?)
        ''', (
            app_id,  # Application ID
            application_type,  # Type of the application (cto/leave/travel_authority)
            application[1],  # Name
            application[2],  # Position
            application[3],  # Days (for leave or CTO)
            application[4],  # Start Date
            application[5],  # End Date
            application[6] if application_type == 'travel_authority' else None,  # Destination for travel authority
            application[7] if application_type == 'travel_authority' else None,  # Purpose for travel authority
            application[6] if application_type == 'leave' else None,  # Leave type for leave applications
            username  # The person recommending approval (e.g., the unit head or recommender)
        ))
        conn.commit()
    return jsonify({'success': True})


@app.route('/recommender_dashboard')
def recommender_dashboard():
    if 'user_id' not in session or session.get('role') != 'recommender':
        flash('Access denied')
        return redirect(url_for('index'))

    recommender_username = session['username']  # Get the logged-in recommender's username

    # Fetch applications assigned to this recommender
    with sqlite3.connect('documents.db') as conn:
        cto_applications = conn.execute('''SELECT * FROM cto_application 
                                           WHERE recommending_approval = ? AND recommending_approval IS NOT NULL''', 
                                        (recommender_username,)).fetchall()

        leave_applications = conn.execute('''SELECT * FROM leave_application 
                                             WHERE recommending_approval = ? AND recommending_approval IS NOT NULL''', 
                                          (recommender_username,)).fetchall()

        travel_authorities = conn.execute('''SELECT * FROM travel_authority 
                                             WHERE recommending_approval = ? AND recommending_approval IS NOT NULL''', 
                                          (recommender_username,)).fetchall()

    return render_template('recommender_dashboard.html', 
                           cto_applications=cto_applications, 
                           leave_applications=leave_applications, 
                           travel_authorities=travel_authorities)


LEAVE_TYPE_MAP = {
    "1": 'Vacation Leave',
    "2": 'Mandatory/Forced Leave',
    "3": 'Sick Leave',
    "4": 'Maternity Leave',
    "5": 'Paternity Leave',
    "6": 'Special Privilege Leave',
    "7": 'Solo Parent Leave',
    "8": 'Study Leave',
    "9": '10-Day VAWC Leave',
    "10": 'Rehabilitation Privilege',
    "11": 'Speical Leave for Women',
    "12": 'Calamity Leave',
    "13": 'Adoption Leave',
    "14": 'Monetization'
 }

@app.route('/recommended_applications')
def recommended_applications():
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('index'))

    with sqlite3.connect('documents.db') as conn:
        cto_recommended_apps = conn.execute('SELECT * FROM recommended_applications WHERE app_type = "cto"').fetchall()
        leave_recommended_apps = conn.execute('''
            SELECT id, name, position, days, start_date, end_date, leave_type, date_recommended 
            FROM recommended_applications 
            WHERE app_type = "leave"
        ''').fetchall()

        for app in leave_recommended_apps:
            print(f"Leave Type from DB: {app[6]}")  # This will show you what leave_type values are coming from the database
        

        # Apply leave type mapping
        leave_recommended_apps = [
            (app[0], app[1], app[2], app[3], app[4], app[5], LEAVE_TYPE_MAP.get(app[6], "Unknown Leave Type"), app[7])
            for app in leave_recommended_apps

        ]
        # for app in cto_recommended_apps:
        #     print(f"CTO Date Recommended from DB: {app}")  # This will show you what date_recommended values are coming from the database

        travel_recommended_apps = conn.execute('SELECT * FROM recommended_applications WHERE app_type = "travel_authority"').fetchall()

    return render_template('recommended_applications.html', cto_recommended_apps=cto_recommended_apps, leave_recommended_apps=leave_recommended_apps, travel_recommended_apps=travel_recommended_apps)

@app.route('/approved_applications')
def approved_applications():
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('index'))

    with sqlite3.connect('documents.db') as conn:
        cto_approved_apps = conn.execute('SELECT * FROM approved_applications WHERE app_type = "cto"').fetchall()
        leave_approved_apps = conn.execute('SELECT * FROM approved_applications WHERE app_type = "leave"').fetchall()
        travel_approved_apps = conn.execute('SELECT * FROM approved_applications WHERE app_type = "travel_authority"').fetchall()

    return render_template('approved_applications.html', cto_approved_apps=cto_approved_apps, leave_approved_apps=leave_approved_apps, travel_approved_apps=travel_approved_apps)

@app.route('/unit_head_dashboard')
def unit_head_dashboard():
    if 'user_id' not in session or session.get('role') != 'unit_head':
        flash('Access denied')
        return redirect(url_for('index'))

    unit_head_username = session['username']  # Ensure the logged-in unit head's username is used

    with sqlite3.connect('documents.db') as conn:
        # Fetch applications specifically assigned to the logged-in unit head
        cto_applications = conn.execute('''
            SELECT id, name, position, days, start_date, end_date 
            FROM cto_application 
            WHERE recommending_approval = ? 
            AND approval_status = "Pending"
        ''', (unit_head_username,)).fetchall()

        leave_applications = conn.execute('''
            SELECT id, name, position, days, start_date, end_date 
            FROM leave_application 
            WHERE recommending_approval = ? 
            AND approval_status = "Pending"
        ''', (unit_head_username,)).fetchall()

        travel_authorities = conn.execute('''
            SELECT id, name, position, purpose, start_date, end_date, destination 
            FROM travel_authority 
            WHERE recommending_approval = ? 
            AND approval_status = "Pending"
        ''', (unit_head_username,)).fetchall()

    return render_template('unit_head_dashboard.html', 
                           cto_applications=cto_applications, 
                           leave_applications=leave_applications, 
                           travel_authorities=travel_authorities)

@app.route('/recommended_head')
def recommended_head():
    if 'user_id' not in session or session.get('role') != 'unit_head':
        flash('Access denied')
        return redirect(url_for('index'))

    unit_head_username = session['username']  # Logged-in unit head's username
    print(f"Unit Head Username: {unit_head_username}")  # Debugging line

    with sqlite3.connect('documents.db') as conn:
        # Fetch recommended CTO applications by this unit head
        cto_recommended_apps = conn.execute('''
            SELECT id, name, position, days, start_date, end_date, date_recommended 
            FROM recommended_applications 
            WHERE app_type = "cto" AND recommending_approval = ?
        ''', (unit_head_username,)).fetchall()
        print(f"CTO Recommended Apps: {len(cto_recommended_apps)}")  # Count instead of full output for cleaner debugging

        # Fetch recommended Leave applications by this unit head
        leave_recommended_apps = conn.execute('''
            SELECT id, name, position, days, start_date, end_date, leave_type, date_recommended 
            FROM recommended_applications 
            WHERE app_type = "leave" AND recommending_approval = ?
        ''', (unit_head_username,)).fetchall()
        print(f"Leave Recommended Apps: {len(leave_recommended_apps)}")  # Cleaner output

        # Fetch recommended Travel Authority applications by this unit head
        travel_recommended_apps = conn.execute('''
            SELECT id, name, position, purpose, start_date, end_date, destination, date_recommended 
            FROM recommended_applications 
            WHERE app_type = "travel_authority" AND recommending_approval = ?
        ''', (unit_head_username,)).fetchall()
        print(f"Travel Recommended Apps: {len(travel_recommended_apps)}")  # Cleaner output

    # Check if data is fetched and returned correctly
    if not cto_recommended_apps and not leave_recommended_apps and not travel_recommended_apps:
        flash("No recommended applications found.")
    
    return render_template('recommended_head.html', 
                           cto_recommended_apps=cto_recommended_apps, 
                           leave_recommended_apps=leave_recommended_apps, 
                           travel_recommended_apps=travel_recommended_apps)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        position = request.form['position']  # Capture the updated position
        role = request.form['role']
        
        # Update the user details including the position
        with sqlite3.connect('users.db') as conn:
            conn.execute('UPDATE users SET name = ?, username = ?, position = ?, role = ? WHERE id = ?', 
                         (name, username, position, role, user_id))
            conn.commit()

        # If the logged-in user is being edited, update the session position
        if user_id == session.get('user_id'):
            session['position'] = position  # Update the position in session data

        flash('User details updated successfully')
        return redirect(url_for('view_users'))

    # Fetch user details for the form
    with sqlite3.connect('users.db') as conn:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    return render_template('edit_user.html', user=user)



@app.route('/print_travel_authority/<int:travel_id>')
def print_travel_authority(travel_id):
    with sqlite3.connect('documents.db') as conn:
        conn.row_factory = sqlite3.Row  # Allows accessing rows as dictionaries
        # Fetch the travel authority data from the database
        travel_authority = conn.execute('''
            SELECT name, position, purpose, host, start_date, end_date, destination, recommending_approval, recommender_position 
            FROM travel_authority 
            WHERE id = ?
        ''', (travel_id,)).fetchone()

    if not travel_authority:
        return "Travel Authority not found.", 404

    # Render the template and pass the application data
    return render_template('travel_authority_print_template.html',
                           name=travel_authority['name'], 
                           position=travel_authority['position'], 
                           purpose=travel_authority['purpose'], 
                           host=travel_authority['host'],  # Add host here
                           start_date=travel_authority['start_date'], 
                           end_date=travel_authority['end_date'],
                           destination=travel_authority['destination'],
                           recommending_approval=travel_authority['recommending_approval'],
                           recommender_position=travel_authority['recommender_position'])  # Pass recommender_position



@app.route('/submit_and_print_travel_authority', methods=['POST'])
def submit_and_print_travel_authority():
    user_id = session['user_id']  # Get the logged-in user's ID
    
    # Get form data
    name = request.form['name']
    position = request.form['position']
    purpose = request.form['purpose']
    host = request.form['host']  # Fetch the 'host' field
    destination = request.form['destination']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    recommending_approval = request.form['recommending_approval']
    
    # Insert the new Travel Authority application into the database
    with sqlite3.connect('documents.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO travel_authority (name, position, purpose, host, destination, start_date, end_date, user_id, recommending_approval)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, position, purpose, host, destination, start_date, end_date, user_id, recommending_approval))
        conn.commit()

        # Get the last inserted ID
        travel_id = cursor.lastrowid

    # Redirect to the print view with the newly created Travel Authority application
    return redirect(url_for('print_travel_authority', travel_id=travel_id))

def add_office_and_salary_columns():
    with sqlite3.connect('users.db') as conn:
        # Add 'office' column if it doesn't already exist
        try:
            conn.execute('ALTER TABLE users ADD COLUMN office TEXT')
        except sqlite3.OperationalError:
            print("Column 'office' already exists.")
        
        # Add 'salary' column if it doesn't already exist
        try:
            conn.execute('ALTER TABLE users ADD COLUMN salary INTEGER')
        except sqlite3.OperationalError:
            print("Column 'salary' already exists.")
        
        conn.commit()

@app.route('/update_user_info', methods=['POST'])
def update_user_info():
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    office = request.form['office']
    salary = request.form['salary']
    position = request.form['position']  # Capture the updated position

    # Update the user's office, salary, and position in the database
    with sqlite3.connect('users.db') as conn:
        conn.execute('UPDATE users SET office = ?, salary = ?, position = ? WHERE id = ?', 
                     (office, salary, position, user_id))
        conn.commit()

    # Optionally, update the session variables if you are using them
    session['position'] = position

    flash('User information updated successfully!')

    # Fetch updated user details
    user_details, stats = get_user_info_and_stats(user_id)

    # Fetch applications from documents.db
    with sqlite3.connect('documents.db') as conn:
        # Fetch the CTO applications
        cto_applications = conn.execute('SELECT id, name, position, days, start_date, end_date, recommending_approval, approval_status, date_recommended FROM cto_application WHERE user_id = ?', (user_id,)).fetchall()
        
        # Fetch the leave applications
        leave_applications = conn.execute('SELECT id, name, position, days, start_date, end_date, leave_type, recommending_approval, approval_status, date_recommended FROM leave_application WHERE user_id = ?', (user_id,)).fetchall()
        
        # Fetch the travel authority applications
        travel_authorities = conn.execute('SELECT id, name, position, purpose, start_date, end_date, destination, recommending_approval, approval_status FROM travel_authority WHERE user_id = ?', (user_id,)).fetchall()

    # Pass updated user details and application data to the dashboard template
    return render_template('user_dashboard.html', 
                           user_details=user_details, 
                           stats=stats, 
                           cto_applications=cto_applications, 
                           leave_applications=leave_applications, 
                           travel_authorities=travel_authorities)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Get the PORT from environment, default to 5000
    app.run(debug=True, host='0.0.0.0', port=port)