from werkzeug.security import check_password_hash, generate_password_hash
from app import login_manager, app

class User():

    def __init__(self, username):
        self.username = username

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username

    @staticmethod
    def validate_login(password_hash, password):
        return check_password_hash(password_hash, password)


@login_manager.user_loader
def load_user(username):
    u = app.config['USERS_COLLECTION'].find_one({"_id": username})
    if not u:
        return None
    return User(u['_id'])


# quick notes for user creation
# from werkzeug.security import check_password_hash, generate_password_hash
# from pymongo import MongoClient
# DB_NAME = 'users'
# DATABASE = MongoClient(connect=False)[DB_NAME]
# USERS_COLLECTION = DATABASE['users']
# USERS_COLLECTION.insert_one({'_id': 'test', 'password': generate_password_hash('test', 'sha256')})