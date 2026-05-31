from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime

client = MongoClient('mongodb+srv://admin:admin123@cluster1.8d1dsga.mongodb.net/?appName=Cluster1')
db = client.fakenews

# Clear existing data for fresh dummy data
db.users.delete_many({})
db.news.delete_many({})
db.reports.delete_many({})
db.sources.delete_many({})

# 1. Add Trusted Sources
sources = [
    {"domain": "reuters.com"},
    {"domain": "bbc.com"},
    {"domain": "apnews.com"},
    {"domain": "nature.com"}
]
db.sources.insert_many(sources)

# 2. Add Users
users = [
    {"username": "admin", "password": generate_password_hash("admin123"), "role": "admin"},
    {"username": "johndoe", "password": generate_password_hash("password123"), "role": "user"},
    {"username": "janedoe", "password": generate_password_hash("password123"), "role": "user"}
]
db.users.insert_many(users)

# 3. Add Dummy News
# We'll use the credibility logic from app.py to set accurate scores
def calc_score(headline, content, url):
    score = 50
    is_trusted = any(s['domain'] in url.lower() for s in sources)
    if is_trusted: score += 40
    if url.startswith("https://"): score += 20
    
    suspicious_words = ["shocking", "miracle", "you won't believe", "secret", "exposed", "hoax", "banned", "click here", "scandal"]
    text = (headline + " " + content).lower()
    if any(word in text for word in suspicious_words):
        score -= 20
        
    score = max(0, min(100, score))
    if score >= 80: label = "Reliable"
    elif score >= 50: label = "Suspicious"
    else: label = "Fake"
    return score, label

news_items = [
    {
        "headline": "Global Markets Rally Amid Positive Economic Data",
        "content": "Major indices saw significant gains today following better-than-expected jobs reports and cooling inflation metrics.",
        "url": "https://www.reuters.com/markets",
        "category": "Politics",
        "submitted_by": "johndoe",
        "date_submitted": datetime.now(),
        "image_url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&q=80"
    },
    {
        "headline": "SHOCKING: Secret Alien Base Exposed on the Moon!",
        "content": "You won't believe what amateur astronomers discovered. A massive alien base has been exposed, completely banned from mainstream media.",
        "url": "http://truth-uncovered-daily.xyz/alien-base",
        "category": "Science",
        "submitted_by": "janedoe",
        "date_submitted": datetime.now(),
        "image_url": "https://images.unsplash.com/photo-1541873676-a18131494184?w=800&q=80"
    },
    {
        "headline": "New Smartphone Battery Charges in 5 Minutes",
        "content": "A new prototype battery technology demonstrates the ability to fully charge a standard smartphone in just five minutes.",
        "url": "https://tech-gadgets-blog.com/new-battery",
        "category": "Technology",
        "submitted_by": "johndoe",
        "date_submitted": datetime.now(),
        "image_url": "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=800&q=80"
    }
]

for item in news_items:
    score, label = calc_score(item['headline'], item['content'], item['url'])
    item['credibility_score'] = score
    item['credibility_label'] = label
    
db.news.insert_many(news_items)

print("Dummy data successfully populated!")
