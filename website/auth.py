from flask import Blueprint, render_template, request, current_app, redirect, url_for, session
from flask_bcrypt import Bcrypt
from datetime import datetime

auth = Blueprint('auth', __name__, template_folder='templates/auth')

bcrypt = Bcrypt()

# Логіка сторінки логування
@auth.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    registered = request.args.get('registered') == '1'

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = current_app.db["Users"].find_one({"email": email})

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            return redirect(url_for('views.index'))

        error = "Невірна електронна пошта або пароль"

    return render_template('login.html', error=error, registered=registered)

# Логіка сторінки реєстрації
@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    error_username = None
    error_email = None

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = current_app.db["Users"].find_one({
            "$or": [{"username": username}, {"email": email}]
        })

        if existing_user:
            if existing_user['username'] == username:
                error_username = "Username already taken"
            if existing_user['email'] == email:
                error_email = "Email already registered"
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = {
                "username": username,
                "email": email,
                "password": hashed_password,
                "timestamp": datetime.utcnow().isoformat(),
                "favourite_genre": []
            }
            current_app.db["Users"].insert_one(user)
            return redirect(url_for('auth.login', registered='1'))

        return render_template('sign-up.html', error_username=error_username, error_email=error_email)

    return render_template('sign-up.html')

# Логіка виходу з акаунта
@auth.route('/logout', methods=['POST'])
def logout():
    session.clear()  # clears all session data
    return redirect(url_for('views.account'))