from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.db import create_user, find_user_by_email, get_db, find_user_by_phone, update_user_password
from utils.auth import hash_password, check_password, create_session, clear_session
import json
import os
import re
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

# Store reset tokens temporarily (in production, use database)
reset_tokens = {}

def send_reset_email(to_email, reset_link):
    """Send password reset email"""
    # Email configuration - Update these with your email settings
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    sender_email = os.getenv('SMTP_EMAIL', '')
    sender_password = os.getenv('SMTP_PASSWORD', '')
    
    if not sender_email or not sender_password:
        print("⚠️ Email not configured. Please set SMTP_EMAIL and SMTP_PASSWORD environment variables.")
        return False
    
    # Create email message
    message = MIMEMultipart("alternative")
    message["Subject"] = "🌾 Smart Farming - Password Reset Request"
    message["From"] = sender_email
    message["To"] = to_email
    
    # Plain text version
    text = f"""
    Smart Farming Assistant - Password Reset
    
    You requested to reset your password. Click the link below to reset it:
    
    {reset_link}
    
    This link will expire in 1 hour.
    
    If you didn't request this, please ignore this email.
    
    - Smart Farming Team
    """
    
    # HTML version
    html = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #0f172a; color: #f1f5f9; padding: 40px;">
        <div style="max-width: 500px; margin: 0 auto; background: #1e293b; border-radius: 16px; padding: 40px; border: 1px solid #334155;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #10b981; margin: 0;">🌾 Smart Farming</h1>
            </div>
            <h2 style="color: #f1f5f9; margin-bottom: 20px;">Password Reset Request</h2>
            <p style="color: #94a3b8; line-height: 1.6;">
                You requested to reset your password. Click the button below to create a new password:
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 14px 32px; text-decoration: none; border-radius: 10px; font-weight: 600; display: inline-block;">
                    Reset Password
                </a>
            </div>
            <p style="color: #64748b; font-size: 14px;">
                This link will expire in 1 hour. If you didn't request this, please ignore this email.
            </p>
            <hr style="border: none; border-top: 1px solid #334155; margin: 30px 0;">
            <p style="color: #64748b; font-size: 12px; text-align: center;">
                © 2024 Smart Farming Assistant
            </p>
        </div>
    </body>
    </html>
    """
    
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())
        print(f"✅ Password reset email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Get database connection
        db = get_db()
        
        # Find user WITH password for authentication
        if hasattr(db, 'users'):
            users = db.users
            user_with_password = users.find_one({'email': email})
        else:
            # Handle mock database
            user_with_password = find_user_by_email(email)
        
        if user_with_password and check_password(password, user_with_password['password']):
            # Create session with user data (excluding password)
            session['user_id'] = str(user_with_password['_id'])
            session['user_name'] = user_with_password['name']
            session['user_email'] = user_with_password['email']
            session['user_phone'] = user_with_password.get('phone', 'Not provided')
            session['user_state'] = user_with_password.get('state', 'Not provided')
            session['user_district'] = user_with_password.get('district', 'Not provided')
            
            flash('🎉 Login successful! Welcome back, ' + user_with_password['name'] + '!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('❌ Invalid email or password. Please try again.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Load states and districts
    try:
        # Try to load from current directory (production)
        if os.path.exists('states_districts.json'):
            with open('states_districts.json', 'r', encoding='utf-8') as f:
                states_districts = json.load(f)
        else:
            # Try to load from script directory (fallback)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.join(script_dir, '..', 'states_districts.json')
            with open(filepath, 'r', encoding='utf-8') as f:
                states_districts = json.load(f)
    except FileNotFoundError as e:
        print(f"Warning: states_districts.json not found: {e}")
        # Fallback states and districts
        states_districts = {
            "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik"],
            "Karnataka": ["Bangalore", "Mysore", "Mangalore", "Hubli"],
            "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem"]
        }
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        state = request.form['state']
        district = request.form['district']
        
        # Check if user already exists by email
        if find_user_by_email(email):
            flash('⚠️ Email already registered! Please use a different email or login.', 'warning')
            return render_template('register.html', states_districts=states_districts)
        
        # Check if phone number is already registered
        if find_user_by_phone(phone):
            flash('⚠️ Phone number already registered! Please use a different phone number or login.', 'warning')
            return render_template('register.html', states_districts=states_districts)
        
        # Validate password strength
        is_strong, message = validate_password_strength(password)
        if not is_strong:
            flash(f'🔒 {message}', 'warning')
            return render_template('register.html', states_districts=states_districts)
        
        # Hash password and create user
        hashed_password = hash_password(password)
        create_user(name, email, hashed_password, phone, state, district)
        
        flash('✅ Registration successful! Welcome to Smart Farming Assistant. Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', states_districts=states_districts)

@auth_bp.route('/logout')
def logout():
    user_name = session.get('user_name', 'User')
    clear_session()
    flash(f'👋 Goodbye {user_name}! You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        # Check if user exists
        user = find_user_by_email(email)
        
        if user:
            # Generate reset token
            token = secrets.token_urlsafe(32)
            expiry = datetime.now() + timedelta(hours=1)
            
            # Store token with email and expiry
            reset_tokens[token] = {
                'email': email,
                'expiry': expiry
            }
            
            # Create reset link
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            
            # Send email
            if send_reset_email(email, reset_link):
                flash('📧 Password reset link has been sent to your email!', 'success')
            else:
                flash('⚠️ Email service not configured. Please contact support.', 'warning')
                # For development, show the link
                print(f"🔗 Reset link (dev mode): {reset_link}")
        else:
            # Don't reveal if email exists or not for security
            flash('📧 If this email is registered, you will receive a password reset link.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Check if token is valid
    if token not in reset_tokens:
        flash('❌ Invalid or expired reset link. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    token_data = reset_tokens[token]
    
    # Check if token has expired
    if datetime.now() > token_data['expiry']:
        del reset_tokens[token]
        flash('⏰ Reset link has expired. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Check if passwords match
        if password != confirm_password:
            flash('❌ Passwords do not match!', 'error')
            return render_template('reset_password.html')
        
        # Validate password strength
        is_strong, message = validate_password_strength(password)
        if not is_strong:
            flash(f'🔒 {message}', 'warning')
            return render_template('reset_password.html')
        
        # Update password in database
        email = token_data['email']
        hashed_password = hash_password(password)
        
        if update_user_password(email, hashed_password):
            # Remove used token
            del reset_tokens[token]
            flash('✅ Password has been reset successfully! Please login with your new password.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('❌ Failed to update password. Please try again.', 'error')
            return render_template('reset_password.html')
    
    return render_template('reset_password.html')
