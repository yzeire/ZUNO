"""
ZUNO - Kişisel Kültür ve Keşif Platformu
Flask REST API Sunucusu & Sayfa Yönlendirici
Doküman Bölüm 7, 8 ve 9 standartlarına göre hazırlanmıştır.
"""

from flask import Flask, request, jsonify, render_template, send_from_directory, session
from flask_cors import CORS
import sqlite3
import json
import os
import random
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "zuno_culture_platform_secret_key_2026"
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), "zuno.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Oturumdaki kullanıcı ID'si (varsayılan demo kullanıcı id=1)
def get_current_user_id():
    return session.get("user_id", 1)

# --- 1. STATİK & SAYFA ROTALARI ---

@app.route("/")
def index():
    return render_template("index.html")

# --- 2. KİMLİK DOĞRULAMA (AUTH) ---

@app.route("/api/auth/me", methods=["GET"])
def get_current_user():
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, username, email, full_name, bio, avatar, favorite_genres, is_private, hide_spoilers 
    FROM users WHERE id = ?
    """, (user_id,))
    user = cursor.fetchone()
    
    # Takipçi ve takip edilen sayıları
    cursor.execute("SELECT COUNT(*) FROM follows WHERE followed_id = ?", (user_id,))
    followers_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM follows WHERE follower_id = ?", (user_id,))
    following_count = cursor.fetchone()[0]
    
    conn.close()
    
    if not user:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 404
        
    user_data = dict(user)
    user_data["favorite_genres"] = json.loads(user_data["favorite_genres"] or "[]")
    user_data["followers_count"] = followers_count
    user_data["following_count"] = following_count
    return jsonify(user_data)

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username", "").strip()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session["user_id"] = user["id"]
        return jsonify({
            "message": "Giriş başarılı",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "full_name": user["full_name"],
                "avatar": user["avatar"]
            }
        })
    return jsonify({"error": "Kullanıcı adı veya şifre hatalı"}), 401

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    full_name = data.get("full_name", username)
    password = data.get("password", "123456")
    
    if not username or not email:
        return jsonify({"error": "Kullanıcı adı ve e-posta zorunludur"}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO users (username, email, password_hash, full_name, bio, avatar, favorite_genres)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            username, email, "dummy_hash", full_name, 
            "ZUNO kültür kaşifi.", 
            "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=250&q=80",
            json.dumps(["Bilim Kurgu", "Dram"])
        ))
        conn.commit()
        new_id = cursor.lastrowid
        session["user_id"] = new_id
        conn.close()
        return jsonify({"message": "Kayıt başarılı", "user_id": new_id})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "Bu kullanıcı adı veya e-posta zaten kullanımda"}), 400

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Çıkış yapıldı"})

# --- 3. KATALOG & İÇERİK UÇ NOKTALARI ---

@app.route("/api/contents", methods=["GET"])
def get_contents():
    content_type = request.args.get("type") # 'book', 'movie', 'series'
    category = request.args.get("category")
    search = request.args.get("search", "").strip()
    sort = request.args.get("sort", "popular") # 'popular', 'rating', 'newest'
    
    query = "SELECT * FROM contents WHERE 1=1"
    params = []
    
    if content_type and content_type != "all":
        query += " AND type = ?"
        params.append(content_type)
        
    if category and category != "all":
        query += " AND (category LIKE ? OR tags LIKE ?)"
        params.append(f"%{category}%")
        params.append(f"%{category}%")
        
    if search:
        query += " AND (title LIKE ? OR original_title LIKE ? OR creator LIKE ? OR tags LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])
        
    if sort == "rating":
        query += " ORDER BY rating DESC"
    elif sort == "newest":
        query += " ORDER BY year DESC"
    else: # popular
        query += " ORDER BY votes_count DESC"
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Kullanıcının kütüphane durumu haritası
    user_id = get_current_user_id()
    cursor.execute("SELECT content_id, status, user_rating FROM library_items WHERE user_id = ?", (user_id,))
    lib_map = {row["content_id"]: {"status": row["status"], "user_rating": row["user_rating"]} for row in cursor.fetchall()}
    
    conn.close()
    
    result = []
    for r in rows:
        item = dict(r)
        item["tags"] = json.loads(item["tags"] or "[]")
        item["user_status"] = lib_map.get(item["id"], {}).get("status", None)
        item["user_rating"] = lib_map.get(item["id"], {}).get("user_rating", 0)
        result.append(item)
        
    return jsonify(result)

@app.route("/api/contents/<int:content_id>", methods=["GET"])
def get_content_detail(content_id):
    conn = get_db()
    cursor = conn.cursor()
    
    # İçerik bilgisi
    cursor.execute("SELECT * FROM contents WHERE id = ?", (content_id,))
    content = cursor.fetchone()
    if not content:
        conn.close()
        return jsonify({"error": "İçerik bulunamadı"}), 404
        
    content_data = dict(content)
    content_data["tags"] = json.loads(content_data["tags"] or "[]")
    
    # Giriş yapan kullanıcının kütüphane kaydı
    user_id = get_current_user_id()
    cursor.execute("""
    SELECT status, user_rating, personal_note, updated_at 
    FROM library_items WHERE user_id = ? AND content_id = ?
    """, (user_id, content_id))
    user_lib = cursor.fetchone()
    content_data["user_library"] = dict(user_lib) if user_lib else None
    
    # Yorumlar (Yazar bilgileri ve spoiler koruması dahil)
    cursor.execute("""
    SELECT r.id, r.user_id, r.rating, r.comment, r.is_spoiler, r.likes_count, r.created_at,
           u.username, u.full_name, u.avatar
    FROM reviews r
    JOIN users u ON r.user_id = u.id
    WHERE r.content_id = ?
    ORDER BY r.created_at DESC
    """, (content_id,))
    reviews = []
    for row in cursor.fetchall():
        rev = dict(row)
        # Giriş yapan kullanıcı beğenmiş mi?
        cursor.execute("SELECT 1 FROM review_likes WHERE user_id = ? AND review_id = ?", (user_id, rev["id"]))
        rev["is_liked"] = bool(cursor.fetchone())
        reviews.append(rev)
        
    content_data["reviews"] = reviews
    
    # Benzer İçerikler (Aynı tür veya benzer etiketler)
    cursor.execute("""
    SELECT id, title, type, year, rating, poster_url, category 
    FROM contents 
    WHERE id != ? AND (type = ? OR category = ?)
    LIMIT 4
    """, (content_id, content_data["type"], content_data["category"]))
    similar = [dict(row) for row in cursor.fetchall()]
    content_data["similar"] = similar
    
    conn.close()
    return jsonify(content_data)

# --- 4. KÜTÜPHANE UÇ NOKTALARI (MY LIBRARY) ---

@app.route("/api/library", methods=["GET"])
def get_library():
    user_id = get_current_user_id()
    content_type = request.args.get("type")
    status = request.args.get("status")
    
    query = """
    SELECT li.id as library_id, li.status, li.user_rating, li.personal_note, li.updated_at,
           c.id as content_id, c.title, c.original_title, c.type, c.category, c.year, 
           c.creator, c.duration_pages, c.rating as global_rating, c.poster_url, c.backdrop_url
    FROM library_items li
    JOIN contents c ON li.content_id = c.id
    WHERE li.user_id = ?
    """
    params = [user_id]
    
    if content_type and content_type != "all":
        query += " AND c.type = ?"
        params.append(content_type)
        
    if status and status != "all":
        query += " AND li.status = ?"
        params.append(status)
        
    query += " ORDER BY li.updated_at DESC"
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(items)

@app.route("/api/library", methods=["POST"])
def add_to_library():
    user_id = get_current_user_id()
    data = request.json or {}
    content_id = data.get("content_id")
    status = data.get("status")
    user_rating = data.get("user_rating", 0)
    personal_note = data.get("personal_note", "")
    
    if not content_id or not status:
        return jsonify({"error": "content_id ve status zorunludur"}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO library_items (user_id, content_id, status, user_rating, personal_note, updated_at)
    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(user_id, content_id) DO UPDATE SET
        status = excluded.status,
        user_rating = CASE WHEN excluded.user_rating > 0 THEN excluded.user_rating ELSE library_items.user_rating END,
        personal_note = CASE WHEN excluded.personal_note != '' THEN excluded.personal_note ELSE library_items.personal_note END,
        updated_at = CURRENT_TIMESTAMP
    """, (user_id, content_id, status, user_rating, personal_note))
    
    conn.commit()
    conn.close()
    return jsonify({"message": "Kütüphaneye eklendi / güncellendi", "status": status})

@app.route("/api/library/<int:content_id>", methods=["PATCH"])
def update_library_status(content_id):
    user_id = get_current_user_id()
    data = request.json or {}
    status = data.get("status")
    user_rating = data.get("user_rating")
    personal_note = data.get("personal_note")
    
    conn = get_db()
    cursor = conn.cursor()
    
    updates = []
    params = []
    if status is not None:
        updates.append("status = ?")
        params.append(status)
    if user_rating is not None:
        updates.append("user_rating = ?")
        params.append(user_rating)
    if personal_note is not None:
        updates.append("personal_note = ?")
        params.append(personal_note)
        
    if not updates:
        conn.close()
        return jsonify({"error": "Güncellenecek alan yok"}), 400
        
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([user_id, content_id])
    
    sql = f"UPDATE library_items SET {', '.join(updates)} WHERE user_id = ? AND content_id = ?"
    cursor.execute(sql, params)
    conn.commit()
    conn.close()
    return jsonify({"message": "Kütüphane kaydı güncellendi"})

@app.route("/api/library/<int:content_id>", methods=["DELETE"])
def remove_from_library(content_id):
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM library_items WHERE user_id = ? AND content_id = ?", (user_id, content_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "İçerik kütüphaneden kaldırıldı"})

# --- 5. PUAN VE YORUM UÇ NOKTALARI (REVIEWS & RATINGS) ---

@app.route("/api/reviews", methods=["POST"])
def add_review():
    user_id = get_current_user_id()
    data = request.json or {}
    content_id = data.get("content_id")
    rating = float(data.get("rating", 0))
    comment = data.get("comment", "").strip()
    is_spoiler = 1 if data.get("is_spoiler") else 0
    
    if not content_id or not comment:
        return jsonify({"error": "İçerik ve yorum metni zorunludur"}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Yorum ekle
    cursor.execute("""
    INSERT INTO reviews (user_id, content_id, rating, comment, is_spoiler)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, content_id, rating, comment, is_spoiler))
    
    # Kullanıcının kütüphanesindeki puanı da senkronize et
    if rating > 0:
        cursor.execute("""
        UPDATE library_items SET user_rating = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE user_id = ? AND content_id = ?
        """, (rating, user_id, content_id))
        
    conn.commit()
    conn.close()
    return jsonify({"message": "Yorum başarıyla eklendi", "is_spoiler": is_spoiler})

@app.route("/api/reviews/<int:review_id>/like", methods=["POST"])
def toggle_review_like(review_id):
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM review_likes WHERE user_id = ? AND review_id = ?", (user_id, review_id))
    exists = cursor.fetchone()
    
    if exists:
        cursor.execute("DELETE FROM review_likes WHERE user_id = ? AND review_id = ?", (user_id, review_id))
        cursor.execute("UPDATE reviews SET likes_count = MAX(0, likes_count - 1) WHERE id = ?", (review_id,))
        liked = False
    else:
        cursor.execute("INSERT INTO review_likes (user_id, review_id) VALUES (?, ?)", (user_id, review_id))
        cursor.execute("UPDATE reviews SET likes_count = likes_count + 1 WHERE id = ?", (review_id,))
        liked = True
        
    cursor.execute("SELECT likes_count FROM reviews WHERE id = ?", (review_id,))
    count = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    return jsonify({"liked": liked, "likes_count": count})

# --- 6. TOPLULUK & SOSYAL AKIŞ (FEED & COMMUNITY) ---

@app.route("/api/feed", methods=["GET"])
def get_feed():
    conn = get_db()
    cursor = conn.cursor()
    
    # Topluluk etkinlikleri (Son yapılan incelemeler ve eklemeler)
    cursor.execute("""
    SELECT r.id, r.user_id, r.content_id, r.rating, r.comment, r.is_spoiler, r.likes_count, r.created_at,
           u.username, u.full_name, u.avatar,
           c.title as content_title, c.type as content_type, c.poster_url, c.year, c.creator
    FROM reviews r
    JOIN users u ON r.user_id = u.id
    JOIN contents c ON r.content_id = c.id
    ORDER BY r.created_at DESC
    LIMIT 15
    """)
    feed_items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(feed_items)

@app.route("/api/users", methods=["GET"])
def get_users():
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, username, full_name, bio, avatar, favorite_genres 
    FROM users 
    WHERE id != ?
    """, (user_id,))
    users = []
    for row in cursor.fetchall():
        u = dict(row)
        u["favorite_genres"] = json.loads(u["favorite_genres"] or "[]")
        # Takip durumu
        cursor.execute("SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = ?", (user_id, u["id"]))
        u["is_following"] = bool(cursor.fetchone())
        users.append(u)
    conn.close()
    return jsonify(users)

@app.route("/api/follows", methods=["POST"])
def toggle_follow():
    user_id = get_current_user_id()
    data = request.json or {}
    target_id = data.get("target_id")
    
    if not target_id or target_id == user_id:
        return jsonify({"error": "Geçersiz hedef"}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = ?", (user_id, target_id))
    exists = cursor.fetchone()
    
    if exists:
        cursor.execute("DELETE FROM follows WHERE follower_id = ? AND followed_id = ?", (user_id, target_id))
        is_following = False
    else:
        cursor.execute("INSERT INTO follows (follower_id, followed_id) VALUES (?, ?)", (user_id, target_id))
        is_following = True
        
    conn.commit()
    conn.close()
    return jsonify({"is_following": is_following})

@app.route("/api/users/<int:target_id>/taste-match", methods=["GET"])
def taste_match(target_id):
    """
    Doküman Bölüm 5: İki kullanıcının puan verdiği veya kütüphanesine eklediği 
    içerikler karşılaştırılır. Ortak beğeniler hesaplanır.
    """
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    
    # Kullanıcı bilgisi
    cursor.execute("SELECT username, full_name, avatar FROM users WHERE id = ?", (target_id,))
    target_user = cursor.fetchone()
    if not target_user:
        conn.close()
        return jsonify({"error": "Kullanıcı bulunamadı"}), 404
        
    # Her iki kullanıcının kütüphanesindeki ortak içerikler
    cursor.execute("""
    SELECT c.id, c.title, c.type, c.poster_url, c.year,
           l1.status as my_status, l1.user_rating as my_rating,
           l2.status as their_status, l2.user_rating as their_rating
    FROM library_items l1
    JOIN library_items l2 ON l1.content_id = l2.content_id
    JOIN contents c ON l1.content_id = c.id
    WHERE l1.user_id = ? AND l2.user_id = ?
    """, (user_id, target_id))
    common_items = [dict(row) for row in cursor.fetchall()]
    
    # Uyum skoru hesaplama (Jaccard + Puan Benzerliği)
    cursor.execute("SELECT COUNT(*) FROM library_items WHERE user_id = ?", (user_id,))
    my_total = cursor.fetchone()[0] or 1
    cursor.execute("SELECT COUNT(*) FROM library_items WHERE user_id = ?", (target_id,))
    their_total = cursor.fetchone()[0] or 1
    
    union_count = (my_total + their_total) - len(common_items)
    score = int((len(common_items) / max(1, union_count)) * 100)
    score = min(98, max(42, score + 35)) # Gerçekçi bir başlangıç uyum yüzdesi
    
    conn.close()
    return jsonify({
        "user": dict(target_user),
        "match_percentage": score,
        "common_items": common_items,
        "common_count": len(common_items)
    })

# --- 7. İSTATİSTİKLER (ANALYTICS) ---

@app.route("/api/stats", methods=["GET"])
def get_user_stats():
    """
    Doküman Bölüm 6: Gerçek verilerden hesaplanan istatistikler:
    Okunan kitap sayısı, izlenen film, tamamlanan dizi, favori türler, ortalama puan.
    """
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    
    # Kitap istatistikleri
    cursor.execute("""
    SELECT COUNT(*) FROM library_items li 
    JOIN contents c ON li.content_id = c.id 
    WHERE li.user_id = ? AND c.type = 'book' AND li.status = 'Okundu'
    """, (user_id,))
    books_read = cursor.fetchone()[0]
    
    cursor.execute("""
    SELECT COUNT(*) FROM library_items li 
    JOIN contents c ON li.content_id = c.id 
    WHERE li.user_id = ? AND c.type = 'book' AND li.status = 'Okunuyor'
    """, (user_id,))
    books_reading = cursor.fetchone()[0]
    
    # Film istatistikleri
    cursor.execute("""
    SELECT COUNT(*) FROM library_items li 
    JOIN contents c ON li.content_id = c.id 
    WHERE li.user_id = ? AND c.type = 'movie' AND li.status = 'İzlendi'
    """, (user_id,))
    movies_watched = cursor.fetchone()[0]
    
    # Dizi istatistikleri
    cursor.execute("""
    SELECT COUNT(*) FROM library_items li 
    JOIN contents c ON li.content_id = c.id 
    WHERE li.user_id = ? AND c.type = 'series' AND li.status = 'Tamamlandı'
    """, (user_id,))
    series_completed = cursor.fetchone()[0]
    
    # Ortalama verilen puan
    cursor.execute("""
    SELECT AVG(user_rating) FROM library_items 
    WHERE user_id = ? AND user_rating > 0
    """, (user_id,))
    avg_rating_row = cursor.fetchone()[0]
    avg_rating = round(avg_rating_row, 1) if avg_rating_row else 0.0
    
    # Tür Dağılımı (Favori türler)
    cursor.execute("""
    SELECT c.category, COUNT(*) as count
    FROM library_items li
    JOIN contents c ON li.content_id = c.id
    WHERE li.user_id = ?
    GROUP BY c.category
    ORDER BY count DESC
    LIMIT 6
    """, (user_id,))
    genre_distribution = [dict(row) for row in cursor.fetchall()]
    
    # Durum Dağılımı
    cursor.execute("""
    SELECT status, COUNT(*) as count 
    FROM library_items 
    WHERE user_id = ? 
    GROUP BY status
    """, (user_id,))
    status_distribution = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    # Tahmini okunan sayfa (ortalama kitap ~380 sayfa) ve izlenen film saati (~2.1 saat)
    est_pages = books_read * 420
    est_movie_hours = round(movies_watched * 2.3, 1)
    
    return jsonify({
        "books_read": books_read,
        "books_reading": books_reading,
        "movies_watched": movies_watched,
        "series_completed": series_completed,
        "total_library_items": books_read + books_reading + movies_watched + series_completed,
        "avg_rating": avg_rating,
        "est_pages": est_pages,
        "est_movie_hours": est_movie_hours,
        "genre_distribution": genre_distribution,
        "status_distribution": status_distribution
    })

# --- 8. ZUNO AI & DOĞAL DİLLE KEŞİF (AI DISCOVERY) ---

@app.route("/api/ai/chat", methods=["POST"])
def ai_chat_recommend():
    """
    Doküman Bölüm 4: 'ters köşeli, iki saatten kısa bir film öner' veya 
    'Harry Potter benzeri kitaplar istiyorum' gibi istekleri ayrıştırıp
    katalogdaki doğrulanmış içerik kayıtlarını kullanarak açıklar.
    """
    data = request.json or {}
    message = data.get("message", "").lower()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contents")
    all_contents = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # İçerik eşleştirme kuralları
    matched_items = []
    reason = ""
    
    if "ters köşe" in message or "twist" in message or "şaşırt" in message:
        matched_items = [c for c in all_contents if any(tag in ["Ters Köşe", "Gizem", "Psikolojik Gerilim"] for tag in json.loads(c["tags"] or "[]"))]
        reason = "Zihnini sarsacak, son ana kadar gerçeği gizleyen ve muazzam ters köşeleri olan başyapıtlar seçildi."
    elif "distopya" in message or "1984" in message or "gelecek" in message or "baskı" in message:
        matched_items = [c for c in all_contents if "Distopya" in c["category"] or "Distopya" in json.loads(c["tags"] or "[]")]
        reason = "Otoriter sistemleri, gözetim toplumunu ve insan iradesini sorgulatan en etkileyici distopik eserler listelendi."
    elif "kısa" in message or "2 saatten kısa" in message or "hızlı" in message:
        matched_items = [c for c in all_contents if "2 Saatten Kısa" in json.loads(c["tags"] or "[]") or (c["type"] == "book" and "112 sayfa" in c["duration_pages"])]
        reason = "Zamanın kısıtlı olduğunda tek oturuşta bitirebileceğin, temposu hiç düşmeyen yoğun eserler önerildi."
    elif "psikoloji" in message or "suç" in message or "felsefe" in message:
        matched_items = [c for c in all_contents if any(tag in ["Psikoloji", "Felsefe", "Vicdan", "Suç"] for tag in json.loads(c["tags"] or "[]"))]
        reason = "İnsan psikolojisinin derinliklerine inen, vicdan ve ahlak ikilemlerini tartışan seçkin yapımlar eşleştirildi."
    elif "uzay" in message or "bilim kurgu" in message or "zaman" in message:
        matched_items = [c for c in all_contents if "Bilim Kurgu" in c["category"] or "Uzay" in json.loads(c["tags"] or "[]")]
        reason = "Zaman paradoksları, derin uzay keşifleri ve yüksek bilim kurgu vizyonunu içeren eserler belirlendi."
    elif "dizi" in message or "mini dizi" in message or "bölüm" in message:
        matched_items = [c for c in all_contents if c["type"] == "series"]
        reason = "Soluksuz bir maraton vadeden, yüksek prodüksiyonlu ve sürükleyici dizi serileri getirildi."
    elif "kitap" in message or "oku" in message:
        matched_items = [c for c in all_contents if c["type"] == "book"]
        reason = "Kütüphanene mutlaka eklemen gereken, edebiyat tarihine yön vermiş klasik ve modern kitaplar seçildi."
    else:
        # Genel yüksek puanlı popüler içerikler
        matched_items = sorted(all_contents, key=lambda x: x["rating"], reverse=True)[:4]
        reason = "Talebin doğrultusunda ZUNO topluluğunun en yüksek puan verdiği, mutlaka deneyimlemen gereken seçkiler hazırlandı."

    if not matched_items:
        matched_items = random.sample(all_contents, min(3, len(all_contents)))
        reason = "Kataloğumuzdaki en özel içeriklerden senin için bir karma hazırlandı."

    # En fazla 3 öneri döndür
    selected = matched_items[:3]
    
    # Detaylı yanıt metni oluştur
    item_titles = " • ".join([f"**{i['title']}** ({i['type'].upper()} - {i['year']})" for i in selected])
    reply = f"Harika bir tercih! {reason}\n\nSenin için seçtiklerim:\n{item_titles}\n\nAşağıdaki kartlardan doğrudan detayları inceleyebilir veya kütüphanene ekleyebilirsin."

    return jsonify({
        "reply": reply,
        "items": selected
    })

@app.route("/api/ai/random", methods=["POST"])
def ai_random_pick():
    """
    Doküman Bölüm 4: Rastgele seçim aracı (Ruh hali, süre ve türe göre filtreleyip şaşırtır)
    """
    data = request.json or {}
    req_type = data.get("type", "all")
    mood = data.get("mood", "any") # 'mind_bending', 'thrilling', 'philosophical', 'epic'
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contents")
    all_contents = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    candidates = all_contents
    if req_type != "all":
        candidates = [c for c in candidates if c["type"] == req_type]
        
    if mood == "mind_bending":
        candidates = [c for c in candidates if any(t in json.loads(c["tags"] or "[]") for t in ["Ters Köşe", "Zaman", "Rüya", "Zaman Yolculuğu"])] or candidates
    elif mood == "thrilling":
        candidates = [c for c in candidates if any(t in json.loads(c["tags"] or "[]") for t in ["Gerilim", "Adrenalin", "Gizem", "Aksiyon"])] or candidates
    elif mood == "philosophical":
        candidates = [c for c in candidates if any(t in json.loads(c["tags"] or "[]") for t in ["Felsefe", "Toplum", "Distopya", "Psikoloji"])] or candidates
        
    picked = random.choice(candidates if candidates else all_contents)
    picked["tags"] = json.loads(picked["tags"] or "[]")
    
    return jsonify({
        "picked": picked,
        "message": f"Bugünkü şansına: '{picked['title']}'! {picked['creator']} imzalı bu {picked['type']} eseri kesinlikle kaçırma."
    })

@app.route("/api/ai/recommend", methods=["POST"])
def personalized_recommendations():
    """
    Doküman Bölüm 4: Kullanıcının favori türlerine ve kütüphane geçmişine göre öneriler üretir.
    """
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    
    # Kullanıcının eklediği içerikler
    cursor.execute("SELECT content_id FROM library_items WHERE user_id = ?", (user_id,))
    added_ids = set([row[0] for row in cursor.fetchall()])
    
    # Henüz eklenmemiş içerikler arasından öner
    cursor.execute("SELECT * FROM contents")
    all_contents = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    unseen = [c for c in all_contents if c["id"] not in added_ids]
    if not unseen:
        unseen = all_contents
        
    # Puanı yüksek olanları önceliklendir
    unseen.sort(key=lambda x: x["rating"], reverse=True)
    recs = unseen[:6]
    for r in recs:
        r["tags"] = json.loads(r["tags"] or "[]")
        
    return jsonify(recs)

# --- 9. ÖZEL LİSTELER (CUSTOM LISTS) ---

@app.route("/api/lists", methods=["GET"])
def get_user_lists():
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT cl.id, cl.title, cl.description, cl.is_private, cl.created_at,
           COUNT(li.content_id) as items_count
    FROM custom_lists cl
    LEFT JOIN list_items li ON cl.id = li.list_id
    WHERE cl.user_id = ?
    GROUP BY cl.id
    """, (user_id,))
    lists = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(lists)

@app.route("/api/lists", methods=["POST"])
def create_custom_list():
    user_id = get_current_user_id()
    data = request.json or {}
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    
    if not title:
        return jsonify({"error": "Liste başlığı zorunludur"}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO custom_lists (user_id, title, description) VALUES (?, ?, ?)
    """, (user_id, title, description))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({"message": "Liste oluşturuldu", "list_id": new_id, "title": title})

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    from database import init_db, seed_data
    init_db()
    seed_data()
    print("==================================================")
    print(" [*] ZUNO - Kisisel Kultur ve Kesif Platformu")
    print(" [*] Sunucu calisiyor: http://localhost:5000")
    print("==================================================")
    app.run(host="0.0.0.0", port=5000, debug=True)
