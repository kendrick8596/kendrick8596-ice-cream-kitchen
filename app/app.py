from flask import Flask, render_template, request, redirect, session
from .auth import auth_bp
from .recipes import recipes_bp
from . import get_db_connection


app = Flask(__name__)
app.secret_key = 'KzeI8hfgoXQ5689074213'

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(recipes_bp, url_prefix='/recipes')


@app.route('/')
def  index():
   username = session.get('username')
   return render_template('index.html', username=username)

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8000, debug=True)