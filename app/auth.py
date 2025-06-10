from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import UserMixin, login_user, logout_user, login_required, current_user
from . import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
import psycopg2

class User(UserMixin):
    def __init__(self, account_id, username, email): # Added 'email' back to __init__
        self.id = account_id # Flask-Login internally uses 'id' property
        self.username = username
        self.email = email # Now storing the email attribute

    def get_id(self):
        return str(self.id)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
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
                cur.execute("INSERT INTO accounts (account_name, password_hash, email) VALUES (%s, %s, %s)", (username, hashed_password, email))
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
        account_data = None

        # Retrieve user from database by using the username
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT account_id, account_name, password_hash, email FROM accounts WHERE account_name = %s", (username,))
            account_data = cur.fetchone()
          
            print(f"Username from form: '{username}'")  # Debugging line
            print(f"User object from database: {account_data}")  # Debugging line

            if account_data and check_password_hash(account_data[2], password):
                user = User(account_data[0], account_data[1], account_data[3])
                login_user(user)
                flash('Login sucessful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'error')
                return redirect(url_for('auth.login'))
        except psycopg2.Error as e:
            flash(f'Database error: {e}', 'error')
            return redirect(url_for('auth.login'))
        finally:
            if cur:
                  cur.close()
            if conn:
                conn.close()
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))