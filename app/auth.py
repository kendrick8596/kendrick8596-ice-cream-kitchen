from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from . import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
import psycopg2

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        conn = None  # Initialize conn outside the try block
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM accounts WHERE account_name = %s", (username,))
            existing_user = cur.fetchone()
            if existing_user:
                flash('Username already taken. Please choose another.', 'error')
            elif password != confirm_password:
                flash('Passwords do not match.', 'error')
            else:
                hashed_password = generate_password_hash(password)
                cur.execute("INSERT INTO accounts (account_name, password_hash) VALUES (%s, %s)", (username, hashed_password))
                conn.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))
            cur.close()
        except psycopg2.Error as e:
            flash(f'Database error: {e}', 'error')
        finally:
            if conn:
                conn.close()
    return render_template('register.html')
    
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = None
        cur = None
        user = None

        # Retrieve user from database by using the username
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM accounts WHERE account_name = %s", (username,))
            user = cur.fetchone()
          
            print(f"Username from form: '{username}'")  # Debugging line
            print(f"User object from database: {user}")  # Debugging line

            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                flash('Login sucessful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'error')
        except psycopg2.Error as e:
            flash(f'Database error: {e}', 'error')
        finally:
            if cur:
                  cur.close()
            if conn:
                conn.close()
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)

    return redirect(url_for('index'))