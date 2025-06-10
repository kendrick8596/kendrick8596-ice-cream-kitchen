from flask import Flask, render_template, request, redirect, session, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from .auth import auth_bp, User
from .recipes import recipes_bp
from . import get_db_connection


app = Flask(__name__)
app.secret_key = 'KzeI8hfgoXQ5689074213'

# --- Flask-login Initialization ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
   conn = get_db_connection()
   cur = conn.cursor()
   cur.execute("SELECT account_id, account_name, email FROM accounts WHERE account_id = %s", (user_id,))
   user_data = cur.fetchone()
   cur.close()
   conn.close()

   if user_data:
         user = User(user_data[0], user_data[1], user_data[2])
         print(f"DEBUG LOAD_USER: User loaded successfully: ID={user.id}, Username={user.username}")
         return user
   else:
      print(f"DEBUG LOAD_USER: User with ID '{user_id}' not found in database.")
      return None # Crucially, returns None if user not found

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(recipes_bp, url_prefix='/recipes')


@app.route('/')
def  index():
    # Flask-Login's 'current_user' proxy is automatically available
   return render_template('index.html', current_user=current_user)

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8000, debug=True)