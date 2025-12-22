import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables FIRST before any other imports
load_dotenv()

from flask import Flask, render_template, session, redirect, url_for
from controllers.auth_routes import auth_bp
from controllers.dashboard_routes import dashboard_bp
from controllers.crop_routes import crop_bp
from controllers.fertilizer_routes import fertilizer_bp
from controllers.growing_routes import growing_bp
from controllers.market_routes import market_bp
from controllers.chat_routes import chat_bp
from controllers.market_scheduler import init_scheduler
# from controllers.community_routes import community_bp
from utils.db import init_db

app = Flask(__name__)
app.secret_key = 'smart_farming_assistant_2024_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Initialize MongoDB connection
try:
    init_db(app)
    print("Database initialized successfully!")
except Exception as e:
    print(f"Database initialization warning: {e}")
    print("App will run with limited functionality")

# Initialize market price scheduler for daily auto-updates
try:
    scheduler = init_scheduler(app)
    print("✅ Market price scheduler initialized!")
except Exception as e:
    print(f"⚠️ Scheduler initialization warning: {e}")

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(crop_bp)
app.register_blueprint(fertilizer_bp)
app.register_blueprint(growing_bp)
app.register_blueprint(market_bp)
app.register_blueprint(chat_bp)
# app.register_blueprint(community_bp)

# Global context processor for date and user info
@app.context_processor
def inject_globals():
    return {
        'current_date': datetime.now().strftime('%Y-%m-%d'),
        'current_time': datetime.now().strftime('%H:%M'),
        'user_logged_in': 'user_id' in session,
        'user_name': session.get('user_name', '')
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/toast-demo')
def toast_demo():
    return render_template('toast_demo.html')

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Vercel serverless function handler
def handler(request):
    return app(request)

if __name__ == '__main__':
    app.run(debug=True)
