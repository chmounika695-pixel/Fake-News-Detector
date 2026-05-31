import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_fake_news_tracker'

# MongoDB configuration
client = MongoClient('mongodb+srv://admin:admin123@cluster1.8d1dsga.mongodb.net/?appName=Cluster1')
db = client.fakenews
users_collection = db.users
news_collection = db.news
reports_collection = db.reports
sources_collection = db.sources

# Initialize default trusted sources if empty
def init_trusted_sources():
    if sources_collection.count_documents({}) == 0:
        sources_collection.insert_many([
            {"domain": "reuters.com"},
            {"domain": "bbc.com"},
            {"domain": "apnews.com"},
            {"domain": "npr.org"}
        ])

init_trusted_sources()

def calculate_credibility(headline, content, url, news_id=None):
    """
    Rule-based credibility scoring:
    - Base score: 50
    - Trusted source: +40
    - Verified URL (https): +20
    - Suspicious keywords: -20
    - Multiple user reports: -30
    
    Final Result:
    80-100: Reliable
    50-79: Suspicious
    0-49: Fake
    """
    score = 50 
    
    # Check trusted source
    is_trusted = False
    for source in sources_collection.find():
        if source['domain'] in url.lower():
            is_trusted = True
            break
    if is_trusted:
        score += 40
        
    # Check verified URL (https)
    if url.startswith("https://"):
        score += 20
        
    # Suspicious keywords
    suspicious_words = ["shocking", "miracle", "you won't believe", "secret", "exposed", "hoax", "banned", "click here", "scandal"]
    text = (headline + " " + content).lower()
    if any(word in text for word in suspicious_words):
        score -= 20
        
    # Multiple user reports
    if news_id:
        report_count = reports_collection.count_documents({"news_id": ObjectId(news_id)})
        if report_count >= 2:
            score -= 30
            
    # Cap score between 0 and 100
    score = max(0, min(100, score))
    
    if score >= 80:
        label = "Reliable"
    elif score >= 50:
        label = "Suspicious"
    else:
        label = "Fake"
        
    return score, label

@app.route('/')
def index():
    all_news = list(news_collection.find().sort("date_submitted", -1))
    return render_template('index.html', news=all_news)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'user') # default to user, can be set to admin for testing
        
        if users_collection.find_one({"username": username}):
            flash("Username already exists", "danger")
            return redirect(url_for('signup'))
            
        hashed_pw = generate_password_hash(password)
        users_collection.insert_one({
            "username": username,
            "password": hashed_pw,
            "role": role
        })
        flash("Signup successful! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = users_collection.find_one({"username": username})
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['role'] = user.get('role', 'user')
            flash("Logged in successfully!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials", "danger")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))

@app.route('/submit', methods=['GET', 'POST'])
def submit_news():
    if 'user_id' not in session:
        flash("Please login to submit news.", "warning")
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        headline = request.form.get('headline')
        content = request.form.get('content')
        url = request.form.get('url')
        category = request.form.get('category')
        
        # Calculate initial credibility
        score, label = calculate_credibility(headline, content, url)
        
        news_item = {
            "headline": headline,
            "content": content,
            "url": url,
            "category": category,
            "submitted_by": session['username'],
            "date_submitted": datetime.now(),
            "credibility_score": score,
            "credibility_label": label,
            "image_url": request.form.get('image_url') # Optional image URL for simplicity instead of file upload
        }
        
        news_collection.insert_one(news_item)
        flash("News submitted successfully!", "success")
        return redirect(url_for('index'))
        
    return render_template('submit.html')

@app.route('/report/<news_id>', methods=['POST'])
def report_news(news_id):
    if 'user_id' not in session:
        flash("Please login to report news.", "warning")
        return redirect(url_for('login'))
        
    reason = request.form.get('reason')
    reports_collection.insert_one({
        "news_id": ObjectId(news_id),
        "reported_by": session['username'],
        "reason": reason,
        "date_reported": datetime.now()
    })
    
    # Recalculate credibility based on new reports
    news_item = news_collection.find_one({"_id": ObjectId(news_id)})
    if news_item:
        score, label = calculate_credibility(news_item['headline'], news_item['content'], news_item['url'], news_id)
        news_collection.update_one(
            {"_id": ObjectId(news_id)},
            {"$set": {"credibility_score": score, "credibility_label": label}}
        )
        
    flash("News reported successfully.", "info")
    return redirect(url_for('index'))

@app.route('/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for('index'))
        
    all_news = list(news_collection.find().sort("date_submitted", -1))
    all_reports = list(reports_collection.find().sort("date_reported", -1))
    all_sources = list(sources_collection.find())
    
    # Attach news headline to reports for display
    for report in all_reports:
        news = news_collection.find_one({"_id": report["news_id"]})
        report["news_headline"] = news["headline"] if news else "Unknown News"
    
    return render_template('dashboard.html', news=all_news, reports=all_reports, sources=all_sources)

@app.route('/add_source', methods=['POST'])
def add_source():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    domain = request.form.get('domain')
    if domain:
        sources_collection.insert_one({"domain": domain})
        flash(f"Trusted source {domain} added.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_source/<source_id>', methods=['POST'])
def delete_source(source_id):
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    sources_collection.delete_one({"_id": ObjectId(source_id)})
    flash("Trusted source removed.", "info")
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
