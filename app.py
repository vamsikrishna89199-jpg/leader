import os
import json
import uuid
import schedule
import threading
import time
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit, join_room
from PIL import Image
import io
import numpy as np
from dotenv import load_dotenv
import logging
from dateutil.relativedelta import relativedelta

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nutri-guide-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Initialize extensions
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
mail = Mail(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/images', exist_ok=True)

# ==================== MODELS ====================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    profile_picture = db.Column(db.String(200), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    
    # Profile fields
    age = db.Column(db.Integer, nullable=True)
    weight = db.Column(db.Float, nullable=True)  # kg
    height = db.Column(db.Float, nullable=True)  # cm
    gender = db.Column(db.String(10), nullable=True)
    activity_level = db.Column(db.String(20), default='moderate')
    goal = db.Column(db.String(20), default='maintain')
    daily_calories = db.Column(db.Float, nullable=True)
    daily_protein = db.Column(db.Float, nullable=True)
    daily_carbs = db.Column(db.Float, nullable=True)
    daily_fat = db.Column(db.Float, nullable=True)
    
    # Settings
    notifications_enabled = db.Column(db.Boolean, default=True)
    water_reminder = db.Column(db.Boolean, default=True)
    meal_reminder = db.Column(db.Boolean, default=True)
    workout_reminder = db.Column(db.Boolean, default=True)
    sleep_reminder = db.Column(db.Boolean, default=True)
    fasting_reminder = db.Column(db.Boolean, default=True)
    
    # Relationships
    meals = db.relationship('Meal', backref='user', lazy=True, cascade="all, delete-orphan")
    workouts = db.relationship('Workout', backref='user', lazy=True, cascade="all, delete-orphan")
    water_logs = db.relationship('WaterLog', backref='user', lazy=True, cascade="all, delete-orphan")
    sleep_logs = db.relationship('SleepLog', backref='user', lazy=True, cascade="all, delete-orphan")
    fasting_sessions = db.relationship('FastingSession', backref='user', lazy=True, cascade="all, delete-orphan")
    grocery_items = db.relationship('GroceryItem', backref='user', lazy=True, cascade="all, delete-orphan")
    meal_plans = db.relationship('MealPlan', backref='user', lazy=True, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade="all, delete-orphan")
    posts = db.relationship('Post', backref='user', lazy=True, cascade="all, delete-orphan")
    friends = db.relationship('Friendship', foreign_keys='Friendship.user_id', backref='user', lazy=True)
    friend_of = db.relationship('Friendship', foreign_keys='Friendship.friend_id', backref='friend', lazy=True)
    messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    weight_logs = db.relationship('WeightLog', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'age': self.age,
            'weight': self.weight,
            'height': self.height,
            'gender': self.gender,
            'goal': self.goal,
            'profile_picture': self.profile_picture,
            'bio': self.bio,
            'daily_calories': self.daily_calories,
            'daily_protein': self.daily_protein,
            'daily_carbs': self.daily_carbs,
            'daily_fat': self.daily_fat,
            'activity_level': self.activity_level,
            'notifications_enabled': self.notifications_enabled,
            'water_reminder': self.water_reminder,
            'meal_reminder': self.meal_reminder,
            'workout_reminder': self.workout_reminder,
            'sleep_reminder': self.sleep_reminder,
            'fasting_reminder': self.fasting_reminder
        }

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    meal_type = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'calories': self.calories,
            'protein': self.protein,
            'carbs': self.carbs,
            'fat': self.fat,
            'image_url': self.image_url,
            'meal_type': self.meal_type,
            'date': self.date.isoformat()
        }

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    duration = db.Column(db.Integer, nullable=False)
    calories_burned = db.Column(db.Float, nullable=False)
    workout_type = db.Column(db.String(50), nullable=False)
    intensity = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'duration': self.duration,
            'calories_burned': self.calories_burned,
            'workout_type': self.workout_type,
            'intensity': self.intensity,
            'date': self.date.isoformat()
        }

class WaterLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SleepLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    duration = db.Column(db.Float, nullable=False)
    quality = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FastingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    target_duration = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GroceryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    purchased = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MealPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    day = db.Column(db.String(20), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    week_start_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    likes = db.relationship('PostLike', backref='post', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")

class PostLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'friend_id', name='unique_friendship'),)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NutritionItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    serving_size = db.Column(db.String(50), nullable=False)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=True)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report_type = db.Column(db.String(20), nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WeightLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== HELPER FUNCTIONS ====================

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def save_image(file, folder='uploads'):
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return f"/uploads/{filename}"
    return None

def calculate_daily_needs(user):
    if user.gender and user.gender.lower() == 'male':
        bmr = 10 * (user.weight or 70) + 6.25 * (user.height or 170) - 5 * (user.age or 30) + 5
    else:
        bmr = 10 * (user.weight or 70) + 6.25 * (user.height or 170) - 5 * (user.age or 30) - 161
    
    activity_multipliers = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'extreme': 1.9
    }
    
    tdee = bmr * activity_multipliers.get(user.activity_level.lower(), 1.55)
    
    if user.goal.lower() == 'lose':
        tdee -= 500
    elif user.goal.lower() == 'gain':
        tdee += 500
    
    calories = round(tdee)
    protein = round((user.weight or 70) * 2.2)
    fat = round(calories * 0.25 / 9)
    carbs = round((calories - (protein * 4 + fat * 9)) / 4)
    
    return calories, protein, carbs, fat

def create_notification(user_id, title, message, type='general'):
    if user_id:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type
        )
        db.session.add(notification)
        db.session.commit()
        
        socketio.emit('new_notification', {
            'title': title,
            'message': message,
            'type': type
        }, room=f'user_{user_id}')

# ==================== NOTIFICATION SCHEDULER ====================

def check_and_send_notifications():
    with app.app_context():
        now = datetime.utcnow()
        current_hour = now.hour
        
        users = User.query.filter_by(notifications_enabled=True).all()
        
        for user in users:
            # Water reminder
            if user.water_reminder and 8 <= current_hour <= 20 and current_hour % 2 == 0:
                create_notification(user.id, "💧 Time to Drink Water!", 
                                  "Stay hydrated! Drink a glass of water.", 'water')
            
            # Meal reminders
            if user.meal_reminder:
                if current_hour == 8:
                    create_notification(user.id, "🍳 Breakfast Time!", 
                                      "Don't forget to have your breakfast!", 'meal')
                elif current_hour == 13:
                    create_notification(user.id, "🥗 Lunch Time!", 
                                      "Time for a healthy lunch!", 'meal')
                elif current_hour == 19:
                    create_notification(user.id, "🍲 Dinner Time!", 
                                      "Don't skip dinner!", 'meal')
            
            # Workout reminder
            if user.workout_reminder and current_hour == 17:
                create_notification(user.id, "🏋️‍♂️ Workout Time!", 
                                  "Time for your daily workout!", 'workout')
            
            # Sleep reminder
            if user.sleep_reminder and current_hour == 22:
                create_notification(user.id, "😴 Bedtime!", 
                                  "Time to wind down and prepare for sleep.", 'sleep')

def run_scheduler():
    schedule.every().hour.do(check_and_send_notifications)
    while True:
        schedule.run_pending()
        time.sleep(3600)

# ==================== ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already exists'}), 400
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        create_notification(user.id, "👋 Welcome to Nutri Guide!", 
                          "Start your health journey with us!", 'general')
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': user.to_dict()
        })
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': user.to_dict()
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'success': True, 'message': 'Logged out'})

@app.route('/api/user/profile', methods=['GET', 'PUT'])
@login_required
def user_profile():
    if request.method == 'GET':
        return jsonify(current_user.to_dict())
    
    elif request.method == 'PUT':
        try:
            data = request.json
            
            current_user.username = data.get('username', current_user.username)
            current_user.email = data.get('email', current_user.email)
            current_user.bio = data.get('bio', current_user.bio)
            
            current_user.age = data.get('age', current_user.age)
            current_user.weight = data.get('weight', current_user.weight)
            current_user.height = data.get('height', current_user.height)
            current_user.gender = data.get('gender', current_user.gender)
            current_user.activity_level = data.get('activity_level', current_user.activity_level)
            current_user.goal = data.get('goal', current_user.goal)
            
            if any(key in data for key in ['weight', 'height', 'age', 'gender', 'activity_level', 'goal']):
                calories, protein, carbs, fat = calculate_daily_needs(current_user)
                current_user.daily_calories = calories
                current_user.daily_protein = protein
                current_user.daily_carbs = carbs
                current_user.daily_fat = fat
            
            if 'notifications_enabled' in data:
                current_user.notifications_enabled = data['notifications_enabled']
            if 'water_reminder' in data:
                current_user.water_reminder = data['water_reminder']
            if 'meal_reminder' in data:
                current_user.meal_reminder = data['meal_reminder']
            if 'workout_reminder' in data:
                current_user.workout_reminder = data['workout_reminder']
            if 'sleep_reminder' in data:
                current_user.sleep_reminder = data['sleep_reminder']
            if 'fasting_reminder' in data:
                current_user.fasting_reminder = data['fasting_reminder']
            
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Profile updated',
                'user': current_user.to_dict()
            })
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/user/upload-profile-picture', methods=['POST'])
@login_required
def upload_profile_picture():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        image_url = save_image(file)
        if image_url:
            current_user.profile_picture = image_url
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Profile picture updated',
                'image_url': image_url
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid file type'}), 400
    except Exception as e:
        logger.error(f"Profile picture upload error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== MEAL & NUTRITION ROUTES ====================

@app.route('/api/meals', methods=['GET', 'POST'])
@login_required
def meals():
    if request.method == 'GET':
        try:
            date_str = request.args.get('date')
            meal_type = request.args.get('type')
            
            query = Meal.query.filter_by(user_id=current_user.id)
            
            if date_str:
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    query = query.filter(db.func.date(Meal.date) == date.date())
                except:
                    pass
            
            if meal_type:
                query = query.filter_by(meal_type=meal_type)
            
            meals = query.order_by(Meal.date.desc()).all()
            
            today = datetime.utcnow().date()
            today_meals = Meal.query.filter_by(user_id=current_user.id)\
                .filter(db.func.date(Meal.date) == today).all()
            
            totals = {
                'calories': sum(m.calories for m in today_meals),
                'protein': sum(m.protein for m in today_meals),
                'carbs': sum(m.carbs for m in today_meals),
                'fat': sum(m.fat for m in today_meals)
            }
            
            return jsonify({
                'success': True,
                'meals': [meal.to_dict() for meal in meals],
                'totals': totals,
                'daily_goals': {
                    'calories': current_user.daily_calories,
                    'protein': current_user.daily_protein,
                    'carbs': current_user.daily_carbs,
                    'fat': current_user.daily_fat
                }
            })
        except Exception as e:
            logger.error(f"Get meals error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            
            meal = Meal(
                user_id=current_user.id,
                name=data['name'],
                description=data.get('description', ''),
                calories=float(data['calories']),
                protein=float(data['protein']),
                carbs=float(data['carbs']),
                fat=float(data['fat']),
                meal_type=data['meal_type']
            )
            
            db.session.add(meal)
            db.session.commit()
            
            return jsonify({'success': True, 'meal': meal.to_dict()})
        except Exception as e:
            logger.error(f"Create meal error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/meals/<int:meal_id>', methods=['PUT', 'DELETE'])
@login_required
def meal_detail(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    
    if meal.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    if request.method == 'PUT':
        try:
            data = request.json
            
            meal.name = data.get('name', meal.name)
            meal.description = data.get('description', meal.description)
            meal.calories = float(data.get('calories', meal.calories))
            meal.protein = float(data.get('protein', meal.protein))
            meal.carbs = float(data.get('carbs', meal.carbs))
            meal.fat = float(data.get('fat', meal.fat))
            meal.meal_type = data.get('meal_type', meal.meal_type)
            
            db.session.commit()
            
            return jsonify({'success': True, 'meal': meal.to_dict()})
        except Exception as e:
            logger.error(f"Update meal error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(meal)
            db.session.commit()
            
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Delete meal error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/meals/scan', methods=['POST'])
@login_required
def scan_food():
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'No image uploaded'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No image selected'}), 400
        
        image_url = save_image(file)
        
        import random
        mock_foods = [
            {
                'name': 'Grilled Chicken Salad',
                'calories': 450,
                'protein': 40,
                'carbs': 12,
                'fat': 20,
                'confidence': 0.95
            },
            {
                'name': 'Avocado Toast',
                'calories': 350,
                'protein': 12,
                'carbs': 38,
                'fat': 18,
                'confidence': 0.88
            },
            {
                'name': 'Berry Smoothie',
                'calories': 280,
                'protein': 8,
                'carbs': 52,
                'fat': 6,
                'confidence': 0.92
            }
        ]
        
        detected_food = random.choice(mock_foods)
        
        return jsonify({
            'success': True,
            'image_url': image_url,
            'detected_food': detected_food,
            'message': 'Food analysis complete'
        })
    except Exception as e:
        logger.error(f"Food scan error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/nutrition/database', methods=['GET'])
def nutrition_database():
    try:
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        limit = min(int(request.args.get('limit', 50)), 100)
        
        query = NutritionItem.query
        
        if search:
            query = query.filter(NutritionItem.name.ilike(f'%{search}%'))
        
        if category:
            query = query.filter_by(category=category)
        
        items = query.limit(limit).all()
        
        return jsonify({
            'success': True,
            'items': [{
                'id': item.id,
                'name': item.name,
                'serving_size': item.serving_size,
                'calories': item.calories,
                'protein': item.protein,
                'carbs': item.carbs,
                'fat': item.fat,
                'category': item.category
            } for item in items]
        })
    except Exception as e:
        logger.error(f"Nutrition database error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/diet/calculate', methods=['POST'])
@login_required
def calculate_diet():
    try:
        data = request.json
        
        weight = float(data.get('weight', current_user.weight or 70))
        height = float(data.get('height', current_user.height or 170))
        age = int(data.get('age', current_user.age or 30))
        gender = data.get('gender', current_user.gender or 'male')
        activity = data.get('activity_level', current_user.activity_level or 'moderate')
        goal = data.get('goal', current_user.goal or 'maintain')
        
        if gender.lower() == 'male':
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'extreme': 1.9
        }
        
        tdee = bmr * activity_multipliers.get(activity.lower(), 1.55)
        
        if goal.lower() == 'lose':
            tdee -= 500
        elif goal.lower() == 'gain':
            tdee += 500
        
        calories = round(tdee)
        protein = round(weight * 2.2)
        fat = round(calories * 0.25 / 9)
        carbs = round((calories - (protein * 4 + fat * 9)) / 4)
        
        current_user.daily_calories = calories
        current_user.daily_protein = protein
        current_user.daily_carbs = carbs
        current_user.daily_fat = fat
        db.session.commit()
        
        return jsonify({
            'success': True,
            'calories': calories,
            'protein': protein,
            'carbs': carbs,
            'fat': fat,
            'bmr': round(bmr),
            'tdee': round(tdee)
        })
    except Exception as e:
        logger.error(f"Diet calculation error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== MEAL PLANNING ROUTES ====================

@app.route('/api/meal-plans', methods=['GET', 'POST'])
@login_required
def meal_plans():
    if request.method == 'GET':
        try:
            week_start = request.args.get('week_start')
            
            if week_start:
                week_start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
            else:
                today = datetime.utcnow().date()
                week_start_date = today - timedelta(days=today.weekday())
            
            week_end_date = week_start_date + timedelta(days=6)
            
            plans = MealPlan.query.filter_by(
                user_id=current_user.id,
                week_start_date=week_start_date
            ).order_by(
                db.case(
                    {
                        'Monday': 1,
                        'Tuesday': 2,
                        'Wednesday': 3,
                        'Thursday': 4,
                        'Friday': 5,
                        'Saturday': 6,
                        'Sunday': 7
                    },
                    value=MealPlan.day
                ),
                db.case(
                    {
                        'breakfast': 1,
                        'lunch': 2,
                        'dinner': 3,
                        'snack': 4
                    },
                    value=MealPlan.meal_type
                )
            ).all()
            
            grouped_plans = {}
            for plan in plans:
                if plan.day not in grouped_plans:
                    grouped_plans[plan.day] = []
                grouped_plans[plan.day].append({
                    'id': plan.id,
                    'meal_type': plan.meal_type,
                    'name': plan.name,
                    'description': plan.description,
                    'calories': plan.calories,
                    'protein': plan.protein,
                    'carbs': plan.carbs,
                    'fat': plan.fat
                })
            
            return jsonify({
                'success': True,
                'week_start': week_start_date.isoformat(),
                'week_end': week_end_date.isoformat(),
                'plans': grouped_plans
            })
        except Exception as e:
            logger.error(f"Get meal plans error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            
            week_start_date = datetime.strptime(data['week_start'], '%Y-%m-%d').date()
            
            MealPlan.query.filter_by(
                user_id=current_user.id,
                week_start_date=week_start_date
            ).delete()
            
            meal_templates = {
                'breakfast': [
                    {'name': 'Oatmeal with Berries', 'calories': 350, 'protein': 12, 'carbs': 58, 'fat': 8},
                    {'name': 'Greek Yogurt Parfait', 'calories': 280, 'protein': 20, 'carbs': 32, 'fat': 6},
                    {'name': 'Avocado Toast', 'calories': 320, 'protein': 15, 'carbs': 38, 'fat': 14},
                    {'name': 'Protein Smoothie', 'calories': 300, 'protein': 25, 'carbs': 35, 'fat': 5}
                ],
                'lunch': [
                    {'name': 'Grilled Chicken Salad', 'calories': 450, 'protein': 40, 'carbs': 12, 'fat': 20},
                    {'name': 'Quinoa Bowl', 'calories': 420, 'protein': 22, 'carbs': 60, 'fat': 12},
                    {'name': 'Turkey Wrap', 'calories': 380, 'protein': 28, 'carbs': 42, 'fat': 10},
                    {'name': 'Vegetable Stir Fry', 'calories': 350, 'protein': 18, 'carbs': 48, 'fat': 8}
                ],
                'dinner': [
                    {'name': 'Salmon with Vegetables', 'calories': 500, 'protein': 38, 'carbs': 32, 'fat': 22},
                    {'name': 'Lean Beef Stew', 'calories': 480, 'protein': 42, 'carbs': 28, 'fat': 20},
                    {'name': 'Chicken and Rice', 'calories': 520, 'protein': 45, 'carbs': 55, 'fat': 12},
                    {'name': 'Vegetable Curry', 'calories': 400, 'protein': 15, 'carbs': 58, 'fat': 10}
                ],
                'snack': [
                    {'name': 'Apple with Almonds', 'calories': 200, 'protein': 6, 'carbs': 25, 'fat': 10},
                    {'name': 'Protein Bar', 'calories': 220, 'protein': 20, 'carbs': 22, 'fat': 6},
                    {'name': 'Greek Yogurt', 'calories': 150, 'protein': 15, 'carbs': 12, 'fat': 4},
                    {'name': 'Rice Cakes', 'calories': 120, 'protein': 4, 'carbs': 25, 'fat': 2}
                ]
            }
            
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
            
            for day in days:
                for meal_type in meal_types:
                    template = meal_templates[meal_type][(days.index(day) + meal_types.index(meal_type)) % 4]
                    
                    plan = MealPlan(
                        user_id=current_user.id,
                        day=day,
                        meal_type=meal_type,
                        name=template['name'],
                        description=f'Healthy {meal_type} for {day}',
                        calories=template['calories'],
                        protein=template['protein'],
                        carbs=template['carbs'],
                        fat=template['fat'],
                        week_start_date=week_start_date
                    )
                    db.session.add(plan)
            
            db.session.commit()
            
            generate_grocery_list(current_user.id, week_start_date)
            
            return jsonify({
                'success': True,
                'message': 'Meal plan generated successfully'
            })
        except Exception as e:
            logger.error(f"Generate meal plan error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

def generate_grocery_list(user_id, week_start_date):
    try:
        GroceryItem.query.filter_by(
            user_id=user_id,
            purchased=False
        ).delete()
        
        common_items = [
            {'name': 'Chicken Breast', 'quantity': '500g', 'category': 'Protein'},
            {'name': 'Salmon', 'quantity': '300g', 'category': 'Protein'},
            {'name': 'Greek Yogurt', 'quantity': '1kg', 'category': 'Dairy'},
            {'name': 'Eggs', 'quantity': '12 pieces', 'category': 'Protein'},
            {'name': 'Oats', 'quantity': '500g', 'category': 'Grains'},
            {'name': 'Quinoa', 'quantity': '250g', 'category': 'Grains'},
            {'name': 'Brown Rice', 'quantity': '1kg', 'category': 'Grains'},
            {'name': 'Mixed Vegetables', 'quantity': '1kg', 'category': 'Vegetables'},
            {'name': 'Spinach', 'quantity': '200g', 'category': 'Vegetables'},
            {'name': 'Avocado', 'quantity': '3 pieces', 'category': 'Fruits'},
            {'name': 'Bananas', 'quantity': '6 pieces', 'category': 'Fruits'},
            {'name': 'Mixed Berries', 'quantity': '300g', 'category': 'Fruits'},
            {'name': 'Almonds', 'quantity': '200g', 'category': 'Nuts'},
            {'name': 'Olive Oil', 'quantity': '500ml', 'category': 'Condiments'},
            {'name': 'Protein Powder', 'quantity': '500g', 'category': 'Supplements'}
        ]
        
        for item_data in common_items:
            item = GroceryItem(
                user_id=user_id,
                name=item_data['name'],
                quantity=item_data['quantity'],
                category=item_data['category'],
                purchased=False
            )
            db.session.add(item)
        
        db.session.commit()
        
        create_notification(user_id, "🛒 Grocery List Generated", 
                          "Your grocery list has been created from your meal plan!", 'general')
        
        return True
    except Exception as e:
        logger.error(f"Generate grocery list error: {str(e)}")
        return False

# ==================== WORKOUT ROUTES ====================

@app.route('/api/workouts', methods=['GET', 'POST'])
@login_required
def workouts():
    if request.method == 'GET':
        try:
            date_str = request.args.get('date')
            workout_type = request.args.get('type')
            
            query = Workout.query.filter_by(user_id=current_user.id)
            
            if date_str:
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    query = query.filter(db.func.date(Workout.date) == date.date())
                except:
                    pass
            
            if workout_type:
                query = query.filter_by(workout_type=workout_type)
            
            workouts = query.order_by(Workout.date.desc()).all()
            
            month_start = datetime.utcnow().replace(day=1).date()
            monthly_workouts = Workout.query.filter_by(user_id=current_user.id)\
                .filter(Workout.date >= month_start).all()
            
            monthly_stats = {
                'total_workouts': len(monthly_workouts),
                'total_duration': sum(w.duration for w in monthly_workouts),
                'total_calories': sum(w.calories_burned for w in monthly_workouts),
                'avg_duration': sum(w.duration for w in monthly_workouts) / len(monthly_workouts) if monthly_workouts else 0
            }
            
            return jsonify({
                'success': True,
                'workouts': [workout.to_dict() for workout in workouts],
                'monthly_stats': monthly_stats
            })
        except Exception as e:
            logger.error(f"Get workouts error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            
            workout = Workout(
                user_id=current_user.id,
                name=data['name'],
                description=data.get('description', ''),
                duration=int(data['duration']),
                calories_burned=float(data['calories_burned']),
                workout_type=data['workout_type'],
                intensity=data.get('intensity', 'medium')
            )
            
            db.session.add(workout)
            db.session.commit()
            
            return jsonify({'success': True, 'workout': workout.to_dict()})
        except Exception as e:
            logger.error(f"Create workout error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/workouts/<int:workout_id>', methods=['PUT', 'DELETE'])
@login_required
def workout_detail(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    
    if workout.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    if request.method == 'PUT':
        try:
            data = request.json
            
            workout.name = data.get('name', workout.name)
            workout.description = data.get('description', workout.description)
            workout.duration = int(data.get('duration', workout.duration))
            workout.calories_burned = float(data.get('calories_burned', workout.calories_burned))
            workout.workout_type = data.get('workout_type', workout.workout_type)
            workout.intensity = data.get('intensity', workout.intensity)
            
            db.session.commit()
            
            return jsonify({'success': True, 'workout': workout.to_dict()})
        except Exception as e:
            logger.error(f"Update workout error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(workout)
            db.session.commit()
            
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Delete workout error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

# ==================== HYDRATION ROUTES ====================

@app.route('/api/hydration', methods=['GET', 'POST'])
@login_required
def hydration():
    if request.method == 'GET':
        try:
            date_str = request.args.get('date', datetime.utcnow().date().isoformat())
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            logs = WaterLog.query.filter_by(user_id=current_user.id)\
                .filter(db.func.date(WaterLog.date) == date)\
                .order_by(WaterLog.date.desc()).all()
            
            total = sum(log.amount for log in logs)
            
            return jsonify({
                'success': True,
                'total': total,
                'goal': 2500,
                'logs': [{
                    'id': log.id,
                    'amount': log.amount,
                    'time': log.date.isoformat()
                } for log in logs]
            })
        except Exception as e:
            logger.error(f"Get hydration error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            amount = float(data['amount'])
            
            log = WaterLog(
                user_id=current_user.id,
                amount=amount
            )
            
            db.session.add(log)
            db.session.commit()
            
            today = datetime.utcnow().date()
            today_logs = WaterLog.query.filter_by(user_id=current_user.id)\
                .filter(db.func.date(WaterLog.date) == today).all()
            today_total = sum(log.amount for log in today_logs)
            
            if today_total >= 2500:
                create_notification(current_user.id, "🎉 Water Goal Achieved!", 
                                  "You've reached your daily water goal!", 'water')
            
            return jsonify({'success': True, 'log': {'id': log.id, 'amount': log.amount}})
        except Exception as e:
            logger.error(f"Log water error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

# ==================== SLEEP ROUTES ====================

@app.route('/api/sleep', methods=['GET', 'POST'])
@login_required
def sleep():
    if request.method == 'GET':
        try:
            limit = int(request.args.get('limit', 7))
            
            logs = SleepLog.query.filter_by(user_id=current_user.id)\
                .order_by(SleepLog.date.desc())\
                .limit(limit).all()
            
            if logs:
                avg_duration = sum(log.duration for log in logs) / len(logs)
                avg_quality = sum(log.quality for log in logs) / len(logs)
            else:
                avg_duration = avg_quality = 0
            
            return jsonify({
                'success': True,
                'logs': [{
                    'id': log.id,
                    'duration': log.duration,
                    'quality': log.quality,
                    'date': log.date.isoformat()
                } for log in logs],
                'averages': {
                    'duration': round(avg_duration, 1),
                    'quality': round(avg_quality, 1)
                }
            })
        except Exception as e:
            logger.error(f"Get sleep error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            log = SleepLog(
                user_id=current_user.id,
                duration=float(data['duration']),
                quality=int(data['quality'])
            )
            
            db.session.add(log)
            db.session.commit()
            
            if log.duration < 6:
                create_notification(current_user.id, "😴 Sleep Alert", 
                                  "You got less than 6 hours of sleep. Try to get more rest!", 'sleep')
            elif log.quality < 5:
                create_notification(current_user.id, "🛌 Improve Sleep Quality", 
                                  "Your sleep quality was low. Consider relaxation techniques.", 'sleep')
            
            return jsonify({'success': True, 'log': {
                'id': log.id,
                'duration': log.duration,
                'quality': log.quality
            }})
        except Exception as e:
            logger.error(f"Log sleep error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

# ==================== FASTING ROUTES ====================

@app.route('/api/fasting', methods=['GET', 'POST', 'PUT'])
@login_required
def fasting():
    if request.method == 'GET':
        try:
            active_session = FastingSession.query.filter_by(
                user_id=current_user.id,
                completed=False
            ).first()
            
            if active_session:
                elapsed = (datetime.utcnow() - active_session.start_time).total_seconds() / 3600
                remaining = max(0, active_session.target_duration - elapsed)
                
                return jsonify({
                    'active': True,
                    'session': {
                        'id': active_session.id,
                        'start_time': active_session.start_time.isoformat(),
                        'target_duration': active_session.target_duration,
                        'elapsed_hours': round(elapsed, 2),
                        'remaining_hours': round(remaining, 2)
                    }
                })
            else:
                return jsonify({'active': False})
        except Exception as e:
            logger.error(f"Get fasting error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            target_duration = int(data.get('target_duration', 16))
            
            existing = FastingSession.query.filter_by(
                user_id=current_user.id,
                completed=False
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': 'You already have an active fasting session'
                }), 400
            
            session = FastingSession(
                user_id=current_user.id,
                start_time=datetime.utcnow(),
                target_duration=target_duration
            )
            
            db.session.add(session)
            db.session.commit()
            
            create_notification(current_user.id, "⏱️ Fasting Started", 
                              f"Your {target_duration}-hour fast has started!", 'fasting')
            
            return jsonify({
                'success': True,
                'session': {
                    'id': session.id,
                    'start_time': session.start_time.isoformat(),
                    'target_duration': session.target_duration
                }
            })
        except Exception as e:
            logger.error(f"Start fasting error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.json
            session_id = data.get('session_id')
            
            session = FastingSession.query.get(session_id)
            if not session or session.user_id != current_user.id:
                return jsonify({'success': False, 'message': 'Session not found'}), 404
            
            session.end_time = datetime.utcnow()
            session.completed = True
            
            elapsed = (session.end_time - session.start_time).total_seconds() / 3600
            
            db.session.commit()
            
            create_notification(current_user.id, "🎉 Fasting Completed", 
                              f"You completed a {round(elapsed, 1)}-hour fast!", 'fasting')
            
            return jsonify({
                'success': True,
                'elapsed_hours': round(elapsed, 2)
            })
        except Exception as e:
            logger.error(f"End fasting error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

# ==================== GROCERY LIST ROUTES ====================

@app.route('/api/grocery', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def grocery():
    if request.method == 'GET':
        try:
            purchased = request.args.get('purchased', 'false').lower() == 'true'
            
            items = GroceryItem.query.filter_by(
                user_id=current_user.id,
                purchased=purchased
            ).order_by(GroceryItem.created_at.desc()).all()
            
            grouped_items = {}
            for item in items:
                category = item.category or 'Other'
                if category not in grouped_items:
                    grouped_items[category] = []
                grouped_items[category].append({
                    'id': item.id,
                    'name': item.name,
                    'quantity': item.quantity,
                    'purchased': item.purchased
                })
            
            return jsonify({
                'success': True,
                'items': grouped_items,
                'total': len(items)
            })
        except Exception as e:
            logger.error(f"Get grocery error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            item = GroceryItem(
                user_id=current_user.id,
                name=data['name'],
                quantity=data.get('quantity', '1'),
                category=data.get('category', 'Other'),
                purchased=False
            )
            
            db.session.add(item)
            db.session.commit()
            
            return jsonify({'success': True, 'item': {
                'id': item.id,
                'name': item.name,
                'quantity': item.quantity
            }})
        except Exception as e:
            logger.error(f"Add grocery item error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.json
            item_id = data.get('id')
            purchased = data.get('purchased')
            
            item = GroceryItem.query.get(item_id)
            if not item or item.user_id != current_user.id:
                return jsonify({'success': False, 'message': 'Item not found'}), 404
            
            if purchased is not None:
                item.purchased = purchased
            
            if 'name' in data:
                item.name = data['name']
            if 'quantity' in data:
                item.quantity = data['quantity']
            if 'category' in data:
                item.category = data['category']
            
            db.session.commit()
            
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Update grocery item error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            item_id = request.args.get('id')
            
            item = GroceryItem.query.get(item_id)
            if not item or item.user_id != current_user.id:
                return jsonify({'success': False, 'message': 'Item not found'}), 404
            
            db.session.delete(item)
            db.session.commit()
            
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Delete grocery item error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

# ==================== NOTIFICATION ROUTES ====================

@app.route('/api/notifications', methods=['GET', 'PUT'])
@login_required
def notifications():
    if request.method == 'GET':
        try:
            unread_only = request.args.get('unread_only', 'false').lower() == 'true'
            limit = int(request.args.get('limit', 20))
            
            query = Notification.query.filter_by(user_id=current_user.id)
            
            if unread_only:
                query = query.filter_by(is_read=False)
            
            notifications = query.order_by(Notification.created_at.desc())\
                .limit(limit).all()
            
            unread_count = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).count()
            
            return jsonify({
                'success': True,
                'notifications': [{
                    'id': n.id,
                    'title': n.title,
                    'message': n.message,
                    'type': n.type,
                    'is_read': n.is_read,
                    'created_at': n.created_at.isoformat()
                } for n in notifications],
                'unread_count': unread_count
            })
        except Exception as e:
            logger.error(f"Get notifications error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.json
            notification_id = data.get('id')
            mark_all = data.get('mark_all', False)
            
            if mark_all:
                Notification.query.filter_by(
                    user_id=current_user.id,
                    is_read=False
                ).update({'is_read': True})
                db.session.commit()
            elif notification_id:
                notification = Notification.query.get(notification_id)
                if notification and notification.user_id == current_user.id:
                    notification.is_read = True
                    db.session.commit()
            
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Update notifications error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

# ==================== SOCIAL FEATURES ROUTES ====================

@app.route('/api/social/friends', methods=['GET', 'POST', 'DELETE'])
@login_required
def friends():
    if request.method == 'GET':
        try:
            status = request.args.get('status', 'accepted')
            
            friendships = Friendship.query.filter(
                ((Friendship.user_id == current_user.id) | (Friendship.friend_id == current_user.id)) &
                (Friendship.status == status)
            ).all()
            
            friends_list = []
            for friendship in friendships:
                if friendship.user_id == current_user.id:
                    friend_user = User.query.get(friendship.friend_id)
                    is_requester = True
                else:
                    friend_user = User.query.get(friendship.user_id)
                    is_requester = False
                
                friends_list.append({
                    'id': friend_user.id,
                    'username': friend_user.username,
                    'profile_picture': friend_user.profile_picture,
                    'bio': friend_user.bio,
                    'friendship_id': friendship.id,
                    'status': friendship.status,
                    'is_requester': is_requester,
                    'created_at': friendship.created_at.isoformat()
                })
            
            return jsonify({
                'success': True,
                'friends': friends_list
            })
        except Exception as e:
            logger.error(f"Get friends error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            friend_username = data.get('username')
            action = data.get('action')
            
            if action == 'send':
                friend_user = User.query.filter_by(username=friend_username).first()
                
                if not friend_user:
                    return jsonify({'success': False, 'message': 'User not found'}), 404
                
                if friend_user.id == current_user.id:
                    return jsonify({'success': False, 'message': 'Cannot add yourself'}), 400
                
                existing = Friendship.query.filter(
                    ((Friendship.user_id == current_user.id) & (Friendship.friend_id == friend_user.id)) |
                    ((Friendship.user_id == friend_user.id) & (Friendship.friend_id == current_user.id))
                ).first()
                
                if existing:
                    return jsonify({'success': False, 'message': 'Friendship already exists'}), 400
                
                friendship = Friendship(
                    user_id=current_user.id,
                    friend_id=friend_user.id,
                    status='pending'
                )
                
                db.session.add(friendship)
                db.session.commit()
                
                create_notification(friend_user.id, "👋 New Friend Request", 
                                  f"{current_user.username} sent you a friend request!", 'social')
                
                return jsonify({'success': True, 'message': 'Friend request sent'})
            
            elif action in ['accept', 'reject']:
                friendship_id = data.get('friendship_id')
                friendship = Friendship.query.get(friendship_id)
                
                if not friendship or friendship.friend_id != current_user.id:
                    return jsonify({'success': False, 'message': 'Friend request not found'}), 404
                
                if action == 'accept':
                    friendship.status = 'accepted'
                    
                    create_notification(friendship.user_id, "✅ Friend Request Accepted", 
                                      f"{current_user.username} accepted your friend request!", 'social')
                
                else:
                    db.session.delete(friendship)
                
                db.session.commit()
                
                return jsonify({'success': True, 'message': f'Friend request {action}ed'})
            
            return jsonify({'success': False, 'message': 'Invalid action'}), 400
        except Exception as e:
            logger.error(f"Friend action error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            friendship_id = request.args.get('id')
            
            friendship = Friendship.query.get(friendship_id)
            if not friendship or (
                friendship.user_id != current_user.id and 
                friendship.friend_id != current_user.id
            ):
                return jsonify({'success': False, 'message': 'Friendship not found'}), 404
            
            db.session.delete(friendship)
            db.session.commit()
            
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Remove friend error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/social/posts', methods=['GET', 'POST'])
@login_required
def posts():
    if request.method == 'GET':
        try:
            user_id = request.args.get('user_id')
            limit = int(request.args.get('limit', 20))
            offset = int(request.args.get('offset', 0))
            
            if user_id:
                posts = Post.query.filter_by(user_id=user_id)\
                    .order_by(Post.created_at.desc())\
                    .limit(limit).offset(offset).all()
            else:
                friendships = Friendship.query.filter(
                    ((Friendship.user_id == current_user.id) | (Friendship.friend_id == current_user.id)) &
                    (Friendship.status == 'accepted')
                ).all()
                
                friend_ids = []
                for friendship in friendships:
                    if friendship.user_id == current_user.id:
                        friend_ids.append(friendship.friend_id)
                    else:
                        friend_ids.append(friendship.user_id)
                
                friend_ids.append(current_user.id)
                posts = Post.query.filter(Post.user_id.in_(friend_ids))\
                    .order_by(Post.created_at.desc())\
                    .limit(limit).offset(offset).all()
            
            posts_data = []
            for post in posts:
                user = User.query.get(post.user_id)
                
                liked = PostLike.query.filter_by(
                    post_id=post.id,
                    user_id=current_user.id
                ).first() is not None
                
                posts_data.append({
                    'id': post.id,
                    'content': post.content,
                    'image_url': post.image_url,
                    'likes_count': post.likes_count,
                    'comments_count': post.comments_count,
                    'created_at': post.created_at.isoformat(),
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'profile_picture': user.profile_picture
                    },
                    'liked': liked
                })
            
            return jsonify({
                'success': True,
                'posts': posts_data,
                'has_more': len(posts) == limit
            })
        except Exception as e:
            logger.error(f"Get posts error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            
            post = Post(
                user_id=current_user.id,
                content=data['content'],
                image_url=data.get('image_url')
            )
            
            db.session.add(post)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'post': {
                    'id': post.id,
                    'content': post.content,
                    'image_url': post.image_url,
                    'created_at': post.created_at.isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Create post error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/social/posts/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    try:
        post = Post.query.get(post_id)
        if not post:
            return jsonify({'success': False, 'message': 'Post not found'}), 404
        
        existing_like = PostLike.query.filter_by(
            post_id=post_id,
            user_id=current_user.id
        ).first()
        
        if existing_like:
            db.session.delete(existing_like)
            post.likes_count -= 1
        else:
            like = PostLike(
                post_id=post_id,
                user_id=current_user.id
            )
            db.session.add(like)
            post.likes_count += 1
            
            if post.user_id != current_user.id:
                create_notification(post.user_id, "❤️ New Like", 
                                  f"{current_user.username} liked your post!", 'social')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'liked': not existing_like,
            'likes_count': post.likes_count
        })
    except Exception as e:
        logger.error(f"Like post error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/social/posts/<int:post_id>/comments', methods=['GET', 'POST'])
@login_required
def comments(post_id):
    if request.method == 'GET':
        try:
            comments = Comment.query.filter_by(post_id=post_id)\
                .order_by(Comment.created_at.asc()).all()
            
            comments_data = []
            for comment in comments:
                user = User.query.get(comment.user_id)
                comments_data.append({
                    'id': comment.id,
                    'content': comment.content,
                    'created_at': comment.created_at.isoformat(),
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'profile_picture': user.profile_picture
                    }
                })
            
            return jsonify({
                'success': True,
                'comments': comments_data
            })
        except Exception as e:
            logger.error(f"Get comments error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            
            post = Post.query.get(post_id)
            if not post:
                return jsonify({'success': False, 'message': 'Post not found'}), 404
            
            comment = Comment(
                post_id=post_id,
                user_id=current_user.id,
                content=data['content']
            )
            
            db.session.add(comment)
            post.comments_count += 1
            db.session.commit()
            
            if post.user_id != current_user.id:
                create_notification(post.user_id, "💬 New Comment", 
                                  f"{current_user.username} commented on your post!", 'social')
            
            user = User.query.get(current_user.id)
            
            return jsonify({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'content': comment.content,
                    'created_at': comment.created_at.isoformat(),
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'profile_picture': user.profile_picture
                    }
                }
            })
        except Exception as e:
            logger.error(f"Create comment error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/social/search-users', methods=['GET'])
@login_required
def search_users():
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 10))
        
        if not query or len(query) < 2:
            return jsonify({'success': True, 'users': []})
        
        users = User.query.filter(
            (User.username.ilike(f'%{query}%')) | (User.email.ilike(f'%{query}%'))
        ).filter(User.id != current_user.id).limit(limit).all()
        
        users_data = []
        for user in users:
            friendship = Friendship.query.filter(
                ((Friendship.user_id == current_user.id) & (Friendship.friend_id == user.id)) |
                ((Friendship.user_id == user.id) & (Friendship.friend_id == current_user.id))
            ).first()
            
            friendship_status = None
            if friendship:
                friendship_status = {
                    'id': friendship.id,
                    'status': friendship.status,
                    'is_requester': friendship.user_id == current_user.id
                }
            
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'profile_picture': user.profile_picture,
                'bio': user.bio,
                'friendship': friendship_status
            })
        
        return jsonify({
            'success': True,
            'users': users_data
        })
    except Exception as e:
        logger.error(f"Search users error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== REPORT ROUTES ====================

@app.route('/api/reports/weekly', methods=['GET'])
@login_required
def weekly_report():
    try:
        today = datetime.utcnow().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        meals = Meal.query.filter_by(user_id=current_user.id)\
            .filter(Meal.date >= week_start)\
            .filter(Meal.date <= week_end).all()
        
        workouts = Workout.query.filter_by(user_id=current_user.id)\
            .filter(Workout.date >= week_start)\
            .filter(Workout.date <= week_end).all()
        
        water_logs = WaterLog.query.filter_by(user_id=current_user.id)\
            .filter(WaterLog.date >= week_start)\
            .filter(WaterLog.date <= week_end).all()
        
        sleep_logs = SleepLog.query.filter_by(user_id=current_user.id)\
            .filter(SleepLog.date >= week_start)\
            .filter(SleepLog.date <= week_end).all()
        
        total_calories = sum(m.calories for m in meals)
        total_protein = sum(m.protein for m in meals)
        total_carbs = sum(m.carbs for m in meals)
        total_fat = sum(m.fat for m in meals)
        
        total_workout_calories = sum(w.calories_burned for w in workouts)
        total_workout_duration = sum(w.duration for w in workouts)
        
        total_water = sum(w.amount for w in water_logs)
        
        avg_sleep = sum(s.duration for s in sleep_logs) / len(sleep_logs) if sleep_logs else 0
        avg_sleep_quality = sum(s.quality for s in sleep_logs) / len(sleep_logs) if sleep_logs else 0
        
        days_count = min(7, (today - week_start).days + 1)
        daily_avg_calories = total_calories / days_count if days_count > 0 else 0
        daily_avg_protein = total_protein / days_count if days_count > 0 else 0
        
        calorie_goal = (current_user.daily_calories or 2000) * days_count
        protein_goal = (current_user.daily_protein or 150) * days_count
        
        calorie_percentage = (total_calories / calorie_goal * 100) if calorie_goal > 0 else 0
        protein_percentage = (total_protein / protein_goal * 100) if protein_goal > 0 else 0
        
        report_data = {
            'period': {
                'start': week_start.isoformat(),
                'end': week_end.isoformat(),
                'days_count': days_count
            },
            'nutrition': {
                'total_calories': total_calories,
                'total_protein': total_protein,
                'total_carbs': total_carbs,
                'total_fat': total_fat,
                'daily_avg_calories': daily_avg_calories,
                'daily_avg_protein': daily_avg_protein,
                'calorie_goal_percentage': min(calorie_percentage, 100),
                'protein_goal_percentage': min(protein_percentage, 100)
            },
            'fitness': {
                'workouts_count': len(workouts),
                'total_workout_calories': total_workout_calories,
                'total_workout_duration': total_workout_duration,
                'avg_workout_duration': total_workout_duration / len(workouts) if workouts else 0
            },
            'hydration': {
                'total_water': total_water,
                'daily_avg_water': total_water / days_count if days_count > 0 else 0,
                'water_goal_percentage': min((total_water / (2500 * days_count) * 100), 100) if days_count > 0 else 0
            },
            'sleep': {
                'avg_sleep_duration': avg_sleep,
                'avg_sleep_quality': avg_sleep_quality
            },
            'achievements': {
                'perfect_days': 0,
                'workout_streak': 0,
                'water_goal_days': 0
            },
            'recommendations': []
        }
        
        if daily_avg_calories > (current_user.daily_calories or 2000) * 1.1:
            report_data['recommendations'].append("Consider reducing calorie intake slightly")
        elif daily_avg_calories < (current_user.daily_calories or 2000) * 0.9:
            report_data['recommendations'].append("Consider increasing calorie intake slightly")
        
        if avg_sleep < 7:
            report_data['recommendations'].append("Try to get more sleep each night")
        
        if total_water < 2500 * days_count * 0.8:
            report_data['recommendations'].append("Increase your water intake")
        
        report = Report(
            user_id=current_user.id,
            report_type='weekly',
            period_start=week_start,
            period_end=week_end,
            data=json.dumps(report_data)
        )
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'report': report_data
        })
    except Exception as e:
        logger.error(f"Weekly report error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/reports/monthly', methods=['GET'])
@login_required
def monthly_report():
    try:
        today = datetime.utcnow().date()
        month_start = today.replace(day=1)
        
        meals = Meal.query.filter_by(user_id=current_user.id)\
            .filter(Meal.date >= month_start).all()
        
        workouts = Workout.query.filter_by(user_id=current_user.id)\
            .filter(Workout.date >= month_start).all()
        
        water_logs = WaterLog.query.filter_by(user_id=current_user.id)\
            .filter(WaterLog.date >= month_start).all()
        
        sleep_logs = SleepLog.query.filter_by(user_id=current_user.id)\
            .filter(SleepLog.date >= month_start).all()
        
        days_in_month = today.day
        active_days = len(set([m.date.date() for m in meals] + [w.date.date() for w in workouts]))
        
        total_calories = sum(m.calories for m in meals)
        total_protein = sum(m.protein for m in meals)
        
        total_workout_calories = sum(w.calories_burned for w in workouts)
        total_workout_duration = sum(w.duration for w in workouts)
        
        total_water = sum(w.amount for w in water_logs)
        
        avg_sleep = sum(s.duration for s in sleep_logs) / len(sleep_logs) if sleep_logs else 0
        
        report_data = {
            'period': {
                'start': month_start.isoformat(),
                'end': today.isoformat(),
                'days_count': days_in_month,
                'active_days': active_days
            },
            'summary': {
                'total_calories_burned': total_workout_calories,
                'total_calories_consumed': total_calories,
                'net_calories': total_calories - total_workout_calories,
                'avg_daily_calories': total_calories / days_in_month if days_in_month > 0 else 0,
                'avg_daily_protein': total_protein / days_in_month if days_in_month > 0 else 0,
                'workout_frequency': len(workouts) / days_in_month if days_in_month > 0 else 0,
                'avg_workout_duration': total_workout_duration / len(workouts) if workouts else 0,
                'avg_daily_water': total_water / days_in_month if days_in_month > 0 else 0,
                'avg_sleep_duration': avg_sleep
            },
            'progress': {
                'weight_change': 0,
                'fitness_improvement': 0,
                'consistency_score': (active_days / days_in_month * 100) if days_in_month > 0 else 0
            },
            'achievements': [
                f"Completed {len(workouts)} workouts",
                f"Consumed {round(total_protein)}g of protein",
                f"Drank {round(total_water / 1000, 1)}L of water"
            ],
            'goals_for_next_month': [
                "Increase workout consistency",
                "Improve sleep quality",
                "Meet daily water goal consistently"
            ]
        }
        
        report = Report(
            user_id=current_user.id,
            report_type='monthly',
            period_start=month_start,
            period_end=today,
            data=json.dumps(report_data)
        )
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'report': report_data
        })
    except Exception as e:
        logger.error(f"Monthly report error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/reports/history', methods=['GET'])
@login_required
def report_history():
    try:
        report_type = request.args.get('type', 'weekly')
        limit = int(request.args.get('limit', 10))
        
        reports = Report.query.filter_by(
            user_id=current_user.id,
            report_type=report_type
        ).order_by(Report.period_start.desc())\
         .limit(limit).all()
        
        reports_data = []
        for report in reports:
            data = json.loads(report.data)
            reports_data.append({
                'id': report.id,
                'period_start': report.period_start.isoformat(),
                'period_end': report.period_end.isoformat(),
                'created_at': report.created_at.isoformat(),
                'summary': data.get('summary', {})
            })
        
        return jsonify({
            'success': True,
            'reports': reports_data
        })
    except Exception as e:
        logger.error(f"Report history error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== WEIGHT LOG ROUTES ====================

@app.route('/api/weight-logs', methods=['GET', 'POST'])
@login_required
def weight_logs():
    if request.method == 'GET':
        try:
            limit = int(request.args.get('limit', 30))
            
            logs = WeightLog.query.filter_by(user_id=current_user.id)\
                .order_by(WeightLog.date.desc())\
                .limit(limit).all()
            
            return jsonify({
                'success': True,
                'logs': [{
                    'id': log.id,
                    'weight': log.weight,
                    'date': log.date.isoformat()
                } for log in logs]
            })
        except Exception as e:
            logger.error(f"Get weight logs error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            
            log = WeightLog(
                user_id=current_user.id,
                weight=float(data['weight'])
            )
            
            db.session.add(log)
            
            current_user.weight = float(data['weight'])
            db.session.commit()
            
            return jsonify({'success': True, 'log': {
                'id': log.id,
                'weight': log.weight,
                'date': log.date.isoformat()
            }})
        except Exception as e:
            logger.error(f"Log weight error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

# ==================== DASHBOARD STATS ====================

@app.route('/api/dashboard/stats', methods=['GET'])
@login_required
def dashboard_stats():
    try:
        today = datetime.utcnow().date()
        
        # Today's meals
        today_meals = Meal.query.filter_by(user_id=current_user.id)\
            .filter(db.func.date(Meal.date) == today).all()
        
        today_totals = {
            'calories': sum(m.calories for m in today_meals),
            'protein': sum(m.protein for m in today_meals),
            'carbs': sum(m.carbs for m in today_meals),
            'fat': sum(m.fat for m in today_meals)
        }
        
        # Today's water
        today_water = WaterLog.query.filter_by(user_id=current_user.id)\
            .filter(db.func.date(WaterLog.date) == today).all()
        water_total = sum(w.amount for w in today_water)
        
        # Today's workouts
        today_workouts = Workout.query.filter_by(user_id=current_user.id)\
            .filter(db.func.date(Workout.date) == today).all()
        workout_calories = sum(w.calories_burned for w in today_workouts)
        
        # Active fasting
        active_fasting = FastingSession.query.filter_by(
            user_id=current_user.id,
            completed=False
        ).first()
        
        fasting_data = None
        if active_fasting:
            elapsed = (datetime.utcnow() - active_fasting.start_time).total_seconds() / 3600
            fasting_data = {
                'active': True,
                'elapsed_hours': round(elapsed, 2),
                'target_hours': active_fasting.target_duration
            }
        
        # Recent notifications
        recent_notifications = Notification.query.filter_by(user_id=current_user.id)\
            .order_by(Notification.created_at.desc())\
            .limit(5).all()
        
        return jsonify({
            'success': True,
            'stats': {
                'nutrition': today_totals,
                'water': water_total,
                'workouts': {
                    'count': len(today_workouts),
                    'calories': workout_calories
                },
                'fasting': fasting_data or {'active': False},
                'goals': {
                    'calories': current_user.daily_calories,
                    'protein': current_user.daily_protein,
                    'water': 2500
                }
            },
            'notifications': [{
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.type,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat()
            } for n in recent_notifications]
        })
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== WEBSOCKET EVENTS ====================

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')
        emit('connected', {'message': f'Connected as {current_user.username}'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('send_message')
def handle_send_message(data):
    try:
        sender_id = current_user.id
        receiver_id = data['receiver_id']
        content = data['content']
        
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content
        )
        
        db.session.add(message)
        db.session.commit()
        
        emit('new_message', {
            'sender_id': sender_id,
            'sender_username': current_user.username,
            'content': content,
            'timestamp': message.created_at.isoformat()
        }, room=f'user_{receiver_id}')
        
        create_notification(receiver_id, "💬 New Message", 
                          f"{current_user.username} sent you a message", 'social')
        
    except Exception as e:
        logger.error(f"Send message error: {str(e)}")

# ==================== INITIALIZATION ====================

def init_database():
    with app.app_context():
        db.create_all()
        
        if NutritionItem.query.count() == 0:
            nutrition_items = [
                NutritionItem(name='Chicken Breast (cooked)', serving_size='100g', 
                             calories=165, protein=31, carbs=0, fat=3.6, category='Protein'),
                NutritionItem(name='Brown Rice (cooked)', serving_size='100g', 
                             calories=112, protein=2.6, carbs=24, fat=0.9, category='Grains'),
                NutritionItem(name='Banana', serving_size='1 medium', 
                             calories=105, protein=1.3, carbs=27, fat=0.4, category='Fruit'),
                NutritionItem(name='Apple', serving_size='1 medium', 
                             calories=95, protein=0.5, carbs=25, fat=0.3, category='Fruit'),
                NutritionItem(name='Egg (whole)', serving_size='1 large', 
                             calories=72, protein=6.3, carbs=0.4, fat=4.8, category='Protein'),
                NutritionItem(name='Greek Yogurt', serving_size='100g', 
                             calories=59, protein=10, carbs=3.6, fat=0.4, category='Dairy'),
                NutritionItem(name='Salmon (cooked)', serving_size='100g', 
                             calories=208, protein=20, carbs=0, fat=13, category='Protein'),
                NutritionItem(name='Almonds', serving_size='28g', 
                             calories=164, protein=6, carbs=6, fat=14, category='Nuts'),
                NutritionItem(name='Broccoli', serving_size='100g', 
                             calories=34, protein=2.8, carbs=7, fat=0.4, category='Vegetables'),
                NutritionItem(name='Sweet Potato', serving_size='100g', 
                             calories=86, protein=1.6, carbs=20, fat=0.1, category='Vegetables'),
                NutritionItem(name='Avocado', serving_size='100g', 
                             calories=160, protein=2, carbs=9, fat=15, category='Fruit'),
                NutritionItem(name='Oatmeal (cooked)', serving_size='100g', 
                             calories=71, protein=2.5, carbs=12, fat=1.5, category='Grains'),
                NutritionItem(name='Whole Wheat Bread', serving_size='1 slice', 
                             calories=79, protein=3, carbs=14, fat=1, category='Grains'),
                NutritionItem(name='Milk (whole)', serving_size='1 cup', 
                             calories=149, protein=8, carbs=12, fat=8, category='Dairy'),
                NutritionItem(name='Cheddar Cheese', serving_size='28g', 
                             calories=115, protein=7, carbs=0.5, fat=9, category='Dairy'),
            ]
            
            for item in nutrition_items:
                db.session.add(item)
            
            db.session.commit()
            logger.info("Nutrition database initialized with sample data")
        
        admin = User.query.filter_by(email='admin@nutriguide.com').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@nutriguide.com',
                age=30,
                weight=75,
                height=180,
                gender='male',
                activity_level='moderate',
                goal='maintain'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            logger.info("Admin user created: admin@nutriguide.com / admin123")

# ==================== MAIN ENTRY POINT ====================

if __name__ == '__main__':
    init_database()
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("Starting Nutri Guide application...")
    socketio.run(app, debug=True, port=5001, allow_unsafe_werkzeug=True)