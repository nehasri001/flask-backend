from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager,UserMixin,login_user,logout_user,login_required,current_user
import secrets
from flask import render_template
from flask import send_from_directory
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

import os
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))
class Opportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300))
    category = db.Column(db.String(50))
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)


@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('sky', filename)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
@app.route('/api/opportunities', methods=['POST'])

def add_opportunity():
    data = request.get_json()

    op = Opportunity(
        title=data.get('title'),
        description=data.get('description'),
        category=data.get('category'),
        admin_id=current_user.id   # temporary
    )

    db.session.add(op)
    db.session.commit()

    return {"status": "opportunity created"}

@app.route('/api/opportunities', methods=['GET'])

def get_opportunities():
    ops = Opportunity.query.filter_by(admin_id=current_user.id).all()

    result = []
    for op in ops:
        result.append({
            "id": op.id,
            "title": op.title,
            "description": op.description,
            "category": op.category
        })

    return {"data": result}
@app.route('/api/opportunities/<int:id>', methods=['DELETE'])

def delete_opportunity(id):

    op = Opportunity.query.filter_by(id=id,admin_id=current_user.id).first()

    if not op:
        return {"error": "Opportunity not found"}, 404

    db.session.delete(op)
    db.session.commit()

    return {"status": "deleted successfully"}
@app.route('/api/opportunities/<int:id>', methods=['PUT'])

def edit_opportunity(id):
    data = request.get_json()

    op = Opportunity.query.filter_by(
        id=id,
        admin_id=current_user.id
    ).first()

    if not op:
        return {"error": "Opportunity not found"}, 404

    op.title = data.get('title')
    op.description = data.get('description')
    op.category = data.get('category')

    db.session.commit()

    return {"status": "updated successfully"}

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    existing = Admin.query.filter_by(email=data.get('email')).first()

    if existing:
        return {"error": "Email already exists"}, 400

    hashed_pw = generate_password_hash(data.get('password'))

    user = Admin(
        full_name=data.get('full_name'),
        email=data.get('email'),
        password=hashed_pw
    )

    db.session.add(user)
    db.session.commit()

    return {"status": "user created"}
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    user = Admin.query.filter_by(email=data.get('email')).first()

    if not user or not check_password_hash(user.password, data.get('password')):
        return {"error": "Invalid credentials"}, 401
    login_user(user)
    return {"status": "login success"}
@app.route('/api/logout')
@login_required
def logout():
    logout_user()
    return {"status": "logged out"}
@app.route('/api/forgot-password', methods=['POST'])

def forgot_password():
    data = request.get_json()

    email = data.get('email')

    user = Admin.query.filter_by(email=email).first()

    if user:
        token = secrets.token_hex(16)

        print(f"Reset link: http://127.0.0.1:5000/reset/{token}")

    return {"message": "If the email exists, a reset link has been sent"}
@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))
with app.app_context():
    db.create_all()
if __name__ == "__main__":
    
    app.run(debug=True)