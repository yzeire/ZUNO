"""
ZUNO - Kişisel Kültür ve Keşif Platformu
SQLite Veritabanı Modeli ve Başlangıç Veri Tohumlayıcı (Seed)
Doküman Bölüm 7 ve 8'e uygun olarak tasarlanmıştır.
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "zuno.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. users tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        bio TEXT,
        avatar TEXT,
        favorite_genres TEXT,
        is_private INTEGER DEFAULT 0,
        hide_spoilers INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. contents tablosu (Kitap, Film, Dizi)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        original_title TEXT,
        type TEXT NOT NULL, -- 'book', 'movie', 'series'
        category TEXT NOT NULL, -- Bilim Kurgu, Polisiye, Psikoloji, Felsefe, vb.
        year INTEGER NOT NULL,
        creator TEXT NOT NULL, -- Yazar / Yönetmen
        duration_pages TEXT, -- '169 dk', '480 sayfa', '4 Sezon (36 Bölüm)'
        rating REAL DEFAULT 0.0,
        votes_count INTEGER DEFAULT 0,
        poster_url TEXT,
        backdrop_url TEXT,
        description TEXT,
        tags TEXT, -- JSON array of tags
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. library_items tablosu (Kullanıcı Kütüphanesi)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS library_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content_id INTEGER NOT NULL,
        status TEXT NOT NULL, 
        -- Kitap: 'Okunacak', 'Okunuyor', 'Okundu', 'Yarım Bırakıldı'
        -- Film: 'İzlenecek', 'İzlendi'
        -- Dizi: 'İzlenecek', 'İzleniyor', 'Tamamlandı', 'Ara Verildi', 'Bırakıldı'
        user_rating REAL DEFAULT 0,
        personal_note TEXT,
        started_at TEXT,
        completed_at TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE,
        UNIQUE(user_id, content_id)
    )
    """)

    # 4. reviews tablosu (Puan, Yorum ve Spoiler Koruması)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content_id INTEGER NOT NULL,
        rating REAL NOT NULL,
        comment TEXT NOT NULL,
        is_spoiler INTEGER DEFAULT 0,
        likes_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE
    )
    """)

    # 5. follows tablosu (Sosyal Takip Sistemi)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS follows (
        follower_id INTEGER NOT NULL,
        followed_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (follower_id, followed_id),
        FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (followed_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 6. review_likes tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS review_likes (
        user_id INTEGER NOT NULL,
        review_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, review_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE
    )
    """)

    # 7. custom_lists tablosu (Özel Listeler)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS custom_lists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        is_private INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 8. list_items tablosu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS list_items (
        list_id INTEGER NOT NULL,
        content_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (list_id, content_id),
        FOREIGN KEY (list_id) REFERENCES custom_lists(id) ON DELETE CASCADE,
        FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()

def seed_data():
    conn = get_db()
    cursor = conn.cursor()

    # Kullanıcılar var mı kontrol et
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    print("ZUNO başlangıç verileri veritabanına yükleniyor...")

    # Başlangıç Kullanıcıları (Demo ve Sosyal Topluluk)
    users = [
        (1, "demo_user", "demo@zuno.app", "pbkdf2:sha256:1000$dummy$hash", "Arda Yılmaz", 
         "Kitap kurdu ve sinema aşığı. Özellikle distopya ve psikolojik gerilim tutkunu.", 
         "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=250&q=80", 
         json.dumps(["Bilim Kurgu", "Distopya", "Psikoloji", "Felsefe"]), 0, 1),
        (2, "elif_kaya", "elif@zuno.app", "pbkdf2:sha256:1000$dummy$hash", "Elif Kaya", 
         "Her hafta en az 2 film bitirir, klasik edebiyat hayranı.", 
         "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=250&q=80", 
         json.dumps(["Klasik Edebiyat", "Dram", "Sanat Filmi", "Tarih"]), 0, 1),
        (3, "baris_demir", "baris@zuno.app", "pbkdf2:sha256:1000$dummy$hash", "Barış Demir", 
         "Bilim kurgu dizilerini soluksuz izleyen bir yazılımcı.", 
         "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=250&q=80", 
         json.dumps(["Bilim Kurgu", "Gerilim", "Mini Dizi", "Polisiye"]), 0, 1),
        (4, "selin_y", "selin@zuno.app", "pbkdf2:sha256:1000$dummy$hash", "Selin Yılmaz", 
         "Fantastik evrenler, mitoloji ve epik kurgu gezgini.", 
         "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=250&q=80", 
         json.dumps(["Fantastik", "Macera", "Mitoloji", "Bilim Kurgu"]), 0, 1),
        (5, "can_akin", "can@zuno.app", "pbkdf2:sha256:1000$dummy$hash", "Can Akın", 
         "Sinematografi ve ters köşeli kurguların peşinde.", 
         "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=250&q=80", 
         json.dumps(["Gizem", "Psikolojik Gerilim", "Kurgu", "Kara Film"]), 0, 1)
    ]

    cursor.executemany("""
    INSERT INTO users (id, username, email, password_hash, full_name, bio, avatar, favorite_genres, is_private, hide_spoilers)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, users)

    # Takipleşmeler
    follows = [
        (1, 2), # demo -> elif
        (1, 3), # demo -> baris
        (2, 1), # elif -> demo
        (3, 1), # baris -> demo
        (4, 1), # selin -> demo
        (5, 3), # can -> baris
    ]
    cursor.executemany("INSERT INTO follows (follower_id, followed_id) VALUES (?, ?)", follows)

    # Başlangıç İçerikleri (Kitaplar, Filmler, Diziler)
    contents = [
        # --- KİTAPLAR ---
        (1, "1984", "Nineteen Eighty-Four", "book", "Distopya", 1949, "George Orwell", "352 sayfa", 9.4, 4520,
         "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80",
         "https://images.unsplash.com/photo-1507842229451-7f01be8510ab?auto=format&fit=crop&w=1200&q=80",
         "Büyük Birader sizi izliyor! Düşünce suçunun en büyük suç sayıldığı, geçmişin sürekli yeniden yazıldığı distopik Londra'da Winston Smith'in isyanı ve hakikat arayışı.",
         json.dumps(["Distopya", "Felsefe", "Politik Kurgu", "Klasik", "Baskı", "Kült"])),

        (2, "Suç ve Ceza", "Crime and Punishment", "book", "Psikoloji", 1866, "Fyodor Dostoyevski", "687 sayfa", 9.6, 5210,
         "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=600&q=80",
         "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?auto=format&fit=crop&w=1200&q=80",
         "Yoksul öğrenci Raskolnikov, üstün insanların ahlak kurallarının üzerinde olduğunu kanıtlamak için bir tefeci kadını öldürür. Vicdan azabı ve ruhsal çöküntünün en derin psikolojik tahlili.",
         json.dumps(["Psikoloji", "Klasik Edebiyat", "Felsefe", "Vicdan", "Suç", "Ahlak"])),

        (3, "Dune", "Dune", "book", "Bilim Kurgu", 1965, "Frank Herbert", "712 sayfa", 9.3, 3890,
         "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=600&q=80",
         "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?auto=format&fit=crop&w=1200&q=80",
         "Evrenin en değerli kaynağı olan 'baharat'ın bulunduğu çöl gezegeni Arrakis ve genç Paul Atreides'in kaderi, kehanetler ve galaktik imparatorluk entrikaları.",
         json.dumps(["Bilim Kurgu", "Uzay Operası", "Felsefe", "Ekoloji", "Politika", "Epik"])),

        (4, "Körlük", "Ensaio sobre a Cegueira", "book", "Distopya", 1995, "José Saramago", "336 sayfa", 9.1, 2980,
         "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=600&q=80",
         "https://images.unsplash.com/photo-1476275466078-4007374efbbe?auto=format&fit=crop&w=1200&q=80",
         "Bilinmeyen bir sebeple bütün kentin beyaz bir körlüğe kapılmasıyla başlayan kaos, insan doğasının vahşiliğini ve dayanışmanın sınırlarını sarsıcı biçimde gözler önüne serer.",
         json.dumps(["Distopya", "Psikoloji", "Toplum", "Felsefe", "Nobel"])),

        (5, "Cesur Yeni Dünya", "Brave New World", "book", "Bilim Kurgu", 1932, "Aldous Huxley", "272 sayfa", 9.0, 3140,
         "https://images.unsplash.com/photo-1495640388908-05fa85288e61?auto=format&fit=crop&w=600&q=80",
         "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",
         "Hazzın, uyuşturucuların ve genetik sınıfların hüküm sürdüğü, acının ve mutsuzluğun yasaklandığı bir gelecekte insani duyguların bedeli.",
         json.dumps(["Distopya", "Bilim Kurgu", "Felsefe", "Toplum", "Teknoloji"])),

        (6, "Yabancı", "L'Étranger", "book", "Felsefe", 1942, "Albert Camus", "112 sayfa", 8.9, 3420,
         "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?auto=format&fit=crop&w=600&q=80",
         "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=1200&q=80",
         "Meursault'un annesinin ölümü karşısındaki kayıtsızlığı ve Cezayir sahilinde işlediği bir cinayet üzerinden varoluşçu absürdizm felsefesi.",
         json.dumps(["Felsefe", "Varoluşçuluk", "Klasik", "Absürdizm", "Fransız Edebiyatı"])),

        # --- FİLMLER ---
        (7, "Interstellar", "Interstellar", "movie", "Bilim Kurgu", 2014, "Christopher Nolan", "169 dk", 9.5, 9840,
         "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=600&q=80",
         "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=1200&q=80",
         "Dünya'nın sonu yaklaşırken, insanlığın hayatta kalabilmesi için solucan deliğinden geçerek yaşanabilir yeni bir gezegen arayan bir grup astronotun zaman ve sevgi dolu yolculuğu.",
         json.dumps(["Bilim Kurgu", "Uzay", "Dram", "Zaman", "Kara Delik", "Ters Köşe"])),

        (8, "Fight Club", "Fight Club", "movie", "Psikolojik Gerilim", 1999, "David Fincher", "139 dk", 9.4, 9120,
         "https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?auto=format&fit=crop&w=600&q=80",
         "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80",
         "Uykusuzluk çeken sıradan bir büro çalışanı ile karizmatik sabun satıcısı Tyler Durden'ın kurduğu yeraltı dövüş kulübü ve tüketim toplumuna karşı başlatılan anarşik başkaldırı.",
         json.dumps(["Psikolojik Gerilim", "Ters Köşe", "Kült", "Felsefe", "Anarşi"])),

        (9, "Inception", "Inception", "movie", "Bilim Kurgu", 2010, "Christopher Nolan", "148 dk", 9.3, 8920,
         "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=600&q=80",
         "https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=1200&q=80",
         "İnsanların rüyalarına girerek en derin sırlarını çalan usta hırsız Dom Cobb'a, bu kez imkânsız bir görev teklif edilir: Bir zihne fikir çalmak yerine yeni bir fikir eklemek (başlangıç).",
         json.dumps(["Bilim Kurgu", "Rüya", "Aksiyon", "Ters Köşe", "Gizem", "Zihin"])),

        (10, "Parazit", "Gisaengchung (Parasite)", "movie", "Gerilim / Kara Mizah", 2019, "Bong Joon-ho", "132 dk", 9.2, 7340,
         "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=600&q=80",
         "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
         "Yoksul Kim ailesinin her bir ferdi, zengin Park ailesinin evinde farklı rollerle işe girmeyi başarır. Ancak bu asalak ilişki beklenmedik karanlık bir sırla patlak verecektir.",
         json.dumps(["Gerilim", "Sosyal Eleştiri", "Sınıf Farkı", "Oscar", "Kore", "Ters Köşe"])),

        (11, "Whiplash", "Whiplash", "movie", "Dram / Müzik", 2014, "Damien Chazelle", "106 dk", 9.1, 6210,
         "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=600&q=80",
         "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=1200&q=80",
         "Büyük bir caz bateristi olmak isteyen hırslı genç Andrew Neiman ile sınırları zorlayan acımasız ve kusursuzluk takıntılı müzik öğretmeni Terence Fletcher arasındaki psikolojik savaş.",
         json.dumps(["Dram", "Müzik", "Psikoloji", "Mükemmeliyetçilik", "Hırs", "2 Saatten Kısa"])),

        (12, "Memento", "Memento", "movie", "Gizem / Gerilim", 2000, "Christopher Nolan", "113 dk", 8.9, 5400,
         "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?auto=format&fit=crop&w=600&q=80",
         "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
         "Kısa süreli hafıza kaybı yaşayan Leonard, karısının katilini bulmak için vücuduna dövme yaptırdığı notlar ve fotoğraflarla geriye doğru akan sıradışı bir zaman diliminde gerçeği arar.",
         json.dumps(["Gizem", "Psikolojik Gerilim", "Ters Köşe", "Kült", "2 Saatten Kısa"])),

        # --- DİZİLER ---
        (13, "Severance", "Severance", "series", "Bilim Kurgu / Gizem", 2022, "Dan Erickson", "2 Sezon (19 Bölüm)", 9.3, 6780,
         "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=600&q=80",
         "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1200&q=80",
         "Lumon Industries çalışanları, iş ve özel hayat anılarını cerrahi müdahaleyle ikiye ayıran 'kıdem tazminatı' prosedürüne tabi tutulur. Ancak ofisin içindeki 'benlikler' dışarıdaki gerçeği sorgulamaya başlar.",
         json.dumps(["Bilim Kurgu", "Gizem", "Distopya", "Kurumsal", "Ters Köşe", "Zihin"])),

        (14, "Dark", "Dark", "series", "Bilim Kurgu / Gizem", 2017, "Baran bo Odar", "3 Sezon (26 Bölüm)", 9.4, 8450,
         "https://images.unsplash.com/photo-1509114397022-ed747cca3f65?auto=format&fit=crop&w=600&q=80",
         "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1200&q=80",
         "Almanya'nın Winden kasabasında kaybolan iki çocuk, dört ailenin 33 yıllık döngülerle zamanda yolculuğa uzanan karmaşık sırlarını ve birbiriyle iç içe geçmiş kaderlerini açığa çıkarır.",
         json.dumps(["Zaman Yolculuğu", "Bilim Kurgu", "Gizem", "Felsefe", "Karmaşık", "Alman"])),

        (15, "Succession", "Succession", "series", "Dram", 2018, "Jesse Armstrong", "4 Sezon (39 Bölüm)", 9.2, 7120,
         "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=600&q=80",
         "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=1200&q=80",
         "Küresel medya imparatorluğu Waystar RoyCo'nun acımasız kurucusu Logan Roy'un sağlığı bozulunca, dört çocuğu şirketin kontrolünü ele geçirmek için acımasız bir taht savaşına girişir.",
         json.dumps(["Dram", "Politika", "Güç Savaşı", "Aile", "Kara Mizah", "Zirve"])),

        (16, "Chernobyl", "Chernobyl", "series", "Tarih / Dram", 2019, "Craig Mazin", "1 Sezon (5 Bölüm - Mini Dizi)", 9.6, 9200,
         "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?auto=format&fit=crop&w=600&q=80",
         "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1200&q=80",
         "1986'da Çernobil Nükleer Santrali'nde yaşanan felaket, ardından gelen akılalmaz fedakarlıklar ve bürokratik yalanların gerçek bedeli. TV tarihinin en yüksek puanlı mini dizisi.",
         json.dumps(["Mini Dizi", "Tarih", "Dram", "Gerçek Olay", "Sürükleyici", "Kusursuz"]))
    ]

    cursor.executemany("""
    INSERT INTO contents (id, title, original_title, type, category, year, creator, duration_pages, rating, votes_count, poster_url, backdrop_url, description, tags)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, contents)

    # Demo Kullanıcı Kütüphanesi
    library_items = [
        # (user_id, content_id, status, user_rating, personal_note)
        (1, 1, "Okundu", 9.5, "Son sayfası boğazımı düğümledi. Winston'ın teslimiyeti korkunçtu."),
        (1, 2, "Okundu", 10.0, "Karakterin iç çatışmaları muazzam işlenmiş. Kesinlikle başyapıt."),
        (1, 3, "Okunuyor", 9.0, "Arrakis çölü ve ekolojik detaylar büyüleyici, 450. sayfadayım."),
        (1, 5, "Okunacak", 0, "Dostoyevski bittikten sonra başlayacağım."),
        (1, 7, "İzlendi", 10.0, "Hans Zimmer müziği ve Cooper'ın mesajları izlediğim en iyi sinema anı."),
        (1, 8, "İzlendi", 9.5, "Kurgusu ve final sahnesi mükemmel."),
        (1, 10, "İzlendi", 9.0, "Sosyal adaletsizlik bu kadar akıcı ve gerilimli anlatılamazdı."),
        (1, 11, "İzlendi", 9.5, "Adrenalin dozu hiç düşmüyor, son solo sahnesi efsane."),
        (1, 13, "İzleniyor", 9.0, "2. sezonu bekliyorum, ofis bölümleri dahi kurgulanmış."),
        (1, 14, "Tamamlandı", 9.8, "Zaman yolculuğunun matematiğini en kusursuz kuran dizi."),
        (1, 16, "Tamamlandı", 10.0, "5 bölümde nefes aldırmadı. 'Yalanların bedeli nedir?'"),
        
        # Elif Kaya Kütüphanesi
        (2, 2, "Okundu", 10.0, "Dostoyevski'nin psikoloji zirvesi."),
        (2, 6, "Okundu", 9.0, "Camus'nün en yalın ve vurucu eseri."),
        (2, 7, "İzlendi", 9.5, "Çok dokunaklı ve bilimsel tabanı güçlü."),
        (2, 10, "İzlendi", 9.0, "Akıldan çıkmayacak metaforlar var."),

        # Barış Demir Kütüphanesi
        (3, 1, "Okundu", 9.0, "Gözetim toplumunu anlamak için zorunlu."),
        (3, 7, "İzlendi", 10.0, "Sinemada 3 kez izledim."),
        (3, 13, "Tamamlandı", 9.5, "Distopik kurumsal dünya harika hicvedilmiş."),
        (3, 14, "Tamamlandı", 10.0, "Her saniyesi için not tutturdu.")
    ]

    cursor.executemany("""
    INSERT INTO library_items (user_id, content_id, status, user_rating, personal_note)
    VALUES (?, ?, ?, ?, ?)
    """, library_items)

    # Örnek Yorumlar (Spoiler Korumalı olanlar dahil!)
    reviews = [
        # (user_id, content_id, rating, comment, is_spoiler, likes_count)
        (2, 2, 10.0, "Raskolnikov'un suçtan sonra Sonya ile yüzleştiği ve İncil'den Lazarus bölümünü okuttuğu sahne dünya edebiyatının en büyük anlarından biridir.", 0, 14),
        (3, 1, 9.5, "Kitabın sonunda Winston'ın 'Büyük Birader'i seviyordu' cümlesiyle ruhunun tamamen teslim oluşu içimi ürpertti.", 1, 28), # SPOILER!
        (5, 7, 9.8, "Tesseract sahnesinde Cooper'ın kitaplığın arkasından kızının saatine mors alfabesiyle verileri göndermesi muazzam bir zaman paradoksu çözümüydü.", 1, 35), # SPOILER!
        (4, 3, 9.2, "Frank Herbert sadece bir bilim kurgu değil; din, sosyoloji ve ekolojinin mükemmel bir sentezini yaratmış.", 0, 9),
        (1, 8, 9.5, "Tyler Durden'ın aslında anlatıcının kendi alter egosu olduğunu anladığınız an tüm ipuçları yerine oturuyor.", 1, 42), # SPOILER!
        (2, 16, 10.0, "Legasov'un mahkeme salonunda mavi ve kırmızı plaketlerle reaktörün nasıl patladığını anlattığı monolog oyunculuk dersi niteliğinde.", 0, 19),
        (3, 14, 9.9, "Jonas ile Martha'nın aslında köken dünyadaki bir araba kazasını önlemek için feda edildikleri o veda sahnesi ağlattı.", 1, 31) # SPOILER!
    ]

    cursor.executemany("""
    INSERT INTO reviews (user_id, content_id, rating, comment, is_spoiler, likes_count)
    VALUES (?, ?, ?, ?, ?, ?)
    """, reviews)

    # Özel Liste Örneği
    cursor.execute("""
    INSERT INTO custom_lists (id, user_id, title, description, is_private)
    VALUES (1, 1, "Zihnimi Açan Başyapıtlar", "Hayata ve evrene bakışımı kökten değiştiren kitap ve filmler.", 0)
    """)

    list_items = [(1, 1), (1, 2), (1, 7), (1, 14)]
    cursor.executemany("INSERT INTO list_items (list_id, content_id) VALUES (?, ?)", list_items)

    conn.commit()
    conn.close()
    print("ZUNO başlangıç verileri başarıyla oluşturuldu!")

if __name__ == "__main__":
    init_db()
    seed_data()
