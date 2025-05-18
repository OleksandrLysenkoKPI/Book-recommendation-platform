from flask import Flask
import os
from dotenv import load_dotenv
from pymongo import MongoClient

def create_app():
    load_dotenv()
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['MONGO_URI'] = os.getenv('MONGO_URI')

    client = MongoClient(app.config['MONGO_URI'])
    db = client['Book_Recommendation_app']
    app.db = db

    from .auth import auth
    from .views import views

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/auth') # /auth/login or /sign-up

    return app