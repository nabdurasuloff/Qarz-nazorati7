# -*- coding: utf-8 -*-
"""
Ma'lumotlar bazasi (SQLite) bilan ishlash.
Dastur ishga tushganda 'qarz_nazorat.db' fayli avtomatik yaratiladi.
"""
import sqlite3
import os
import sys
import datetime


def _app_dir():
    # .exe (PyInstaller --onefile) sifatida ishga tushganda ma'lumotlar bazasi
    # dastur fayli joylashgan papkada saqlanadi (vaqtinchalik _MEIPASS'da emas),
    # shunda dastur qayta ishga tushirilganda ma'lumotlar yo'qolmaydi.
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


DB_PATH = os.path.join(_app_dir(), 'qarz_nazorat.db')


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS portfel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        port_kod TEXT,
        anketa_raqami TEXT,
        unikal TEXT,
        stir TEXT,
        pinfl TEXT,
        filial_kodi TEXT,
        viloyat TEXT,
        tarmoq TEXT,
        stage TEXT,
        mijoz_turi_kodi TEXT,
        mijoz_turi TEXT,
        mijoz_nomi TEXT,
        valyuta TEXT,
        kredit_hisob_raqami TEXT,
        yillik_foiz REAL,
        shartnoma_sanasi TEXT,
        shartnoma_tugash_sanasi TEXT,
        tulov_maqsadi TEXT,
        dpd_asosiy INTEGER DEFAULT 0,
        dpd_foiz INTEGER DEFAULT 0,
        dpd_max INTEGER DEFAULT 0,
        ead REAL DEFAULT 0,
        jami_qarz REAL DEFAULT 0,
        asosiy_qarz REAL DEFAULT 0,
        foiz_qarz REAL DEFAULT 0,
        jarima REAL DEFAULT 0,
        import_sanasi TEXT,
        holat TEXT DEFAULT 'yangi'
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS mijozlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        turi TEXT,                  -- 'jismoniy' yoki 'yuridik'
        kalit TEXT,                 -- bog'lash uchun: unikal / стир / пинфл
        ism TEXT,
        manzil TEXT,
        telefon TEXT,
        hujjat_raqami TEXT,         -- pasport yoki STIR
        rahbar_ism TEXT,
        import_sanasi TEXT,
        UNIQUE(kalit, turi)
    )
    ''')

    # Eski bazalarda mavjud bo'lmasa, pasport tafsilot ustunlarini qo'shamiz
    existing_mijoz_cols = {r['name'] for r in conn.execute("PRAGMA table_info(mijozlar)").fetchall()}
    for col in ['passport_sana', 'passport_organ']:
        if col not in existing_mijoz_cols:
            cur.execute(f'ALTER TABLE mijozlar ADD COLUMN {col} TEXT')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS davo_taminot (
        anketa_raqami TEXT PRIMARY KEY,
        taminot_turi TEXT,           -- 'yoq' / 'kafillik' / 'garov' / 'kafillik_garov'
        kafil_ism TEXT,
        kafil_manzil TEXT,
        kafil_pinfl TEXT,
        kafil_passport TEXT,
        kafil_passport_sana TEXT,
        kafil_passport_organ TEXT,
        kafil_tel TEXT,
        garov_tavsifi TEXT,          -- masalan: avtomobil rusumi, dvigatel/kuzov raqami va h.k.
        garov_bahosi REAL,
        pochta_xarajati REAL,
        yangilangan_sana TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS xatlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        portfel_id INTEGER,
        anketa_raqami TEXT,
        mijoz_nomi TEXT,
        mijoz_turi TEXT,
        xat_turi TEXT,               -- 'Ogohlantirish' / 'Talabnoma'
        yaratilgan_sana TEXT,
        muddat_sana TEXT,
        holat TEXT DEFAULT 'tayyor', -- tayyor / yuborildi / muddati_otgan
        yuborilgan_sana TEXT,
        fayl_yoli TEXT,
        davo_ariza_sana TEXT,
        davo_ariza_fayl_yoli TEXT,
        davo_ariza_holati TEXT,          -- 'tayyor' / 'olib_kelindi'
        davo_ariza_turi TEXT,            -- jismoniy_oddiy / yuridik_kafil va h.k.
        davo_ariza_ish_raqami TEXT,
        davo_ariza_imzo_sana TEXT,       -- imzodan/Palatadan chiqqan sana
        FOREIGN KEY(portfel_id) REFERENCES portfel(id)
    )
    ''')

    # Eski bazalarda mavjud bo'lmasa, yangi ustunlarni qo'shib qo'yamiz
    existing_cols = {r['name'] for r in conn.execute("PRAGMA table_info(xatlar)").fetchall()}
    for col in ['davo_ariza_sana', 'davo_ariza_fayl_yoli', 'davo_ariza_holati',
                'davo_ariza_turi', 'davo_ariza_ish_raqami', 'davo_ariza_imzo_sana']:
        if col not in existing_cols:
            cur.execute(f'ALTER TABLE xatlar ADD COLUMN {col} TEXT')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS sozlamalar (
        kalit TEXT PRIMARY KEY,
        qiymat TEXT
    )
    ''')

    defaults = {
        'bank_nomi': '"АГРОБАНК" АТБ',
        'bank_qisqa_nomi': 'АГРОБАНК',
        'bank_manzil': "100096, Ўзбекистон Республикаси, Тошкент ш., Муқимий кўчаси, 43",
        'bank_email': 'headoffice@agrobank.uz',
        'bank_sayt': 'www.agrobank.uz',
        'bank_tel': '1216',
        'bank_mobil_ilova': 'AGROBANK',
        'bank_kodi': '00382',
        'aloqa_markazi_tel': '1216',
        'filial_nomi': 'Боёвут',
        'filial_tel': '71-202-80-08 (382-01)',
        'rahbar_ism': '',
        'tolov_muddati_kun': '10',
        'eslatma_muddati_kun': '3',
        'davo_ariza_muddati_kun': '5',
        'dpd_chegara_kun': '45',

        # --- Davo ariza uchun qo'shimcha sozlamalar ---
        'bank_stir': '207243390',
        'bank_hisob_raqami_filial': '16103000700000382001',
        'bank_kodi_filial': '00382',
        'bank_hisob_raqami_bosh': '16103000200001140001',
        'bank_kodi_bosh': '01140',
        'bank_rasmiy_manzil_filial': "Сирдарё вилояти, Боёвут тумани, Боёвут шаҳарчаси, Тинчлик кўчаси, 10-уй",
        'sud_fuqarolik_nomi': 'Боёвут туманлараро суди',
        'sud_iqtisodiy_nomi': 'Гулистон туманлараро иқтисодий суди',
        'palata_nomi': "Ўзбекистон Савдо-саноат палатаси Сирдарё вилояти ҳудудий бошқармаси",
        'palata_manzil': "Сирдарё вилояти, Гулистон ш. 4-мавзе, Бўстон МФЙ, Дўстлик канали қирғоқ бўйи, "
                          "Тадбиркор ва ҳунармандлар маркази, тел. +99867 236 37 27, 1094, "
                          "e-mail: sr@chamber.uz, www.chamber.uz",
        'pochta_xarajati_standart': '41200',
        'sud_ariza_imzo_ism': '',
        'sud_ariza_imzo_lavozimi': "Бошқарма бошлиғи ўринбосари",
        'viloyat_nomi': 'Сирдарё',
    }
    for k, v in defaults.items():
        cur.execute('INSERT OR IGNORE INTO sozlamalar (kalit, qiymat) VALUES (?, ?)', (k, v))

    conn.commit()
    conn.close()


def get_setting(kalit, default=''):
    conn = get_conn()
    row = conn.execute('SELECT qiymat FROM sozlamalar WHERE kalit=?', (kalit,)).fetchone()
    conn.close()
    return row['qiymat'] if row else default


def get_all_settings():
    conn = get_conn()
    rows = conn.execute('SELECT kalit, qiymat FROM sozlamalar').fetchall()
    conn.close()
    return {r['kalit']: r['qiymat'] for r in rows}


def set_setting(kalit, qiymat):
    conn = get_conn()
    conn.execute('INSERT INTO sozlamalar (kalit, qiymat) VALUES (?, ?) '
                 'ON CONFLICT(kalit) DO UPDATE SET qiymat=excluded.qiymat', (kalit, qiymat))
    conn.commit()
    conn.close()


def clear_portfel():
    conn = get_conn()
    conn.execute('DELETE FROM portfel')
    conn.commit()
    conn.close()


def insert_portfel_rows(rows):
    """rows: list of dicts matching portfel columns (without id)."""
    conn = get_conn()
    cur = conn.cursor()
    cols = ['port_kod', 'anketa_raqami', 'unikal', 'stir', 'pinfl', 'filial_kodi', 'viloyat',
            'tarmoq', 'stage',
            'mijoz_turi_kodi', 'mijoz_turi', 'mijoz_nomi', 'valyuta', 'kredit_hisob_raqami',
            'yillik_foiz', 'shartnoma_sanasi', 'shartnoma_tugash_sanasi', 'tulov_maqsadi',
            'dpd_asosiy', 'dpd_foiz', 'dpd_max', 'ead', 'jami_qarz', 'asosiy_qarz', 'foiz_qarz',
            'jarima', 'import_sanasi', 'holat']
    placeholders = ','.join(['?'] * len(cols))
    sql = f"INSERT INTO portfel ({','.join(cols)}) VALUES ({placeholders})"
    now = datetime.datetime.now().isoformat()
    for r in rows:
        r.setdefault('import_sanasi', now)
        r.setdefault('holat', 'yangi')
        values = [r.get(c) for c in cols]
        cur.execute(sql, values)
    conn.commit()
    conn.close()


def upsert_mijoz(turi, kalit, ism, manzil, telefon, hujjat_raqami, rahbar_ism='',
                  passport_sana='', passport_organ=''):
    conn = get_conn()
    now = datetime.datetime.now().isoformat()
    conn.execute('''
        INSERT INTO mijozlar (turi, kalit, ism, manzil, telefon, hujjat_raqami, rahbar_ism,
                               passport_sana, passport_organ, import_sanasi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(kalit, turi) DO UPDATE SET
            ism=excluded.ism, manzil=excluded.manzil, telefon=excluded.telefon,
            hujjat_raqami=excluded.hujjat_raqami, rahbar_ism=excluded.rahbar_ism,
            passport_sana=excluded.passport_sana, passport_organ=excluded.passport_organ,
            import_sanasi=excluded.import_sanasi
    ''', (turi, kalit, ism, manzil, telefon, hujjat_raqami, rahbar_ism,
          passport_sana, passport_organ, now))
    conn.commit()
    conn.close()


def bulk_upsert_mijozlar(records):
    """
    records: list of tuples (turi, kalit, ism, manzil, telefon, hujjat_raqami, rahbar_ism,
                              passport_sana, passport_organ)
    Bitta ulanish/tranzaksiya orqali ko'p mijozni tez saqlaydi.
    """
    conn = get_conn()
    now = datetime.datetime.now().isoformat()
    conn.executemany('''
        INSERT INTO mijozlar (turi, kalit, ism, manzil, telefon, hujjat_raqami, rahbar_ism,
                               passport_sana, passport_organ, import_sanasi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(kalit, turi) DO UPDATE SET
            ism=excluded.ism, manzil=excluded.manzil, telefon=excluded.telefon,
            hujjat_raqami=excluded.hujjat_raqami, rahbar_ism=excluded.rahbar_ism,
            passport_sana=excluded.passport_sana, passport_organ=excluded.passport_organ,
            import_sanasi=excluded.import_sanasi
    ''', [(t, k, i, m, tel, h, r, ps, po, now) for (t, k, i, m, tel, h, r, ps, po) in records])
    conn.commit()
    conn.close()


def find_mijoz(turi, kalit):
    conn = get_conn()
    row = conn.execute('SELECT * FROM mijozlar WHERE turi=? AND kalit=?', (turi, kalit)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_tarmoq_stage3_breakdown(limit=8):
    """Tarmoq (soha) bo'yicha Stage 3 (eng muammoli) kreditlar taqsimoti."""
    conn = get_conn()
    rows = conn.execute('''
        SELECT COALESCE(NULLIF(TRIM(tarmoq), ''), "Noma'lum") AS tarmoq,
               COUNT(*) AS soni, SUM(jami_qarz) AS jami
        FROM portfel
        WHERE TRIM(stage) = '3'
        GROUP BY tarmoq
        ORDER BY jami DESC
        LIMIT ?
    ''', (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_viloyat_breakdown(chegara_kun=45, limit=8):
    """Viloyat bo'yicha 45+ kun mijozlar soni va muddati o'tgan qarz yig'indisi."""
    conn = get_conn()
    rows = conn.execute('''
        SELECT COALESCE(NULLIF(TRIM(viloyat), ''), "Noma'lum") AS viloyat,
               COUNT(*) AS soni, SUM(jami_qarz) AS jami
        FROM portfel
        WHERE dpd_max >= ?
        GROUP BY viloyat
        ORDER BY jami DESC
        LIMIT ?
    ''', (chegara_kun, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_turi_breakdown(chegara_kun=45):
    """Jismoniy/yuridik (portfeldagi kod bo'yicha taxminiy) taqsimot."""
    conn = get_conn()
    rows = conn.execute('''
        SELECT mijoz_turi_kodi, mijoz_turi, COUNT(*) AS soni
        FROM portfel WHERE dpd_max >= ?
        GROUP BY mijoz_turi_kodi, mijoz_turi
    ''', (chegara_kun,)).fetchall()
    conn.close()
    jismoniy, yuridik = 0, 0
    for r in rows:
        kod = str(r['mijoz_turi_kodi'] or '').strip().upper()
        turi = str(r['mijoz_turi'] or '').strip().upper()
        if turi == 'LE' or kod in ('9', 'J', 'YUR'):
            yuridik += r['soni']
        else:
            jismoniy += r['soni']
    return {'jismoniy': jismoniy, 'yuridik': yuridik}


def get_bugungi_harakatlar():
    """Bugun yaratilgan va bugun yuborilgan xatlar soni."""
    bugun = datetime.date.today().isoformat()
    conn = get_conn()
    yaratildi = conn.execute(
        "SELECT COUNT(*) c FROM xatlar WHERE yaratilgan_sana LIKE ?", (bugun + '%',)
    ).fetchone()['c']
    yuborildi = conn.execute(
        "SELECT COUNT(*) c FROM xatlar WHERE yuborilgan_sana LIKE ?", (bugun + '%',)
    ).fetchone()['c']
    conn.close()
    return {'yaratildi': yaratildi, 'yuborildi': yuborildi}


def get_latest_xat_status_by_portfel():
    """Har bir portfel_id uchun eng oxirgi xat holatini qaytaradi: {portfel_id: holat}"""
    conn = get_conn()
    rows = conn.execute('''
        SELECT portfel_id, holat FROM xatlar x1
        WHERE yaratilgan_sana = (
            SELECT MAX(yaratilgan_sana) FROM xatlar x2 WHERE x2.portfel_id = x1.portfel_id
        )
    ''').fetchall()
    conn.close()
    return {r['portfel_id']: r['holat'] for r in rows}


def get_portfel_45_kun(chegara_kun=45):
    conn = get_conn()
    rows = conn.execute(
        'SELECT * FROM portfel WHERE dpd_max >= ? ORDER BY dpd_max DESC', (chegara_kun,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_portfel_by_id(portfel_id):
    conn = get_conn()
    row = conn.execute('SELECT * FROM portfel WHERE id=?', (portfel_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_portfel_by_anketa(anketa_raqami):
    conn = get_conn()
    rows = conn.execute(
        'SELECT * FROM portfel WHERE anketa_raqami LIKE ?', (f'%{anketa_raqami}%',)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_xat(portfel_id, anketa_raqami, mijoz_nomi, mijoz_turi, xat_turi, fayl_yoli, muddat_kun=3):
    conn = get_conn()
    now = datetime.datetime.now()
    muddat = now + datetime.timedelta(days=muddat_kun)
    conn.execute('''
        INSERT INTO xatlar (portfel_id, anketa_raqami, mijoz_nomi, mijoz_turi, xat_turi,
                             yaratilgan_sana, muddat_sana, holat, fayl_yoli)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'tayyor', ?)
    ''', (portfel_id, anketa_raqami, mijoz_nomi, mijoz_turi, xat_turi,
          now.isoformat(), muddat.isoformat(), fayl_yoli))
    conn.commit()
    conn.close()


def get_xatlar(holat=None):
    conn = get_conn()
    if holat:
        rows = conn.execute('SELECT * FROM xatlar WHERE holat=? ORDER BY yaratilgan_sana DESC', (holat,)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM xatlar ORDER BY yaratilgan_sana DESC').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_xat_yuborildi(xat_id):
    conn = get_conn()
    now = datetime.datetime.now().isoformat()
    conn.execute("UPDATE xatlar SET holat='yuborildi', yuborilgan_sana=? WHERE id=?", (now, xat_id))
    conn.commit()
    conn.close()


def mark_davo_ariza_yaratildi(xat_id, fayl_yoli, turi=None):
    conn = get_conn()
    now = datetime.datetime.now().isoformat()
    conn.execute("UPDATE xatlar SET davo_ariza_sana=?, davo_ariza_fayl_yoli=?, davo_ariza_holati='tayyor', "
                 "davo_ariza_turi=? WHERE id=?", (now, fayl_yoli, turi, xat_id))
    conn.commit()
    conn.close()


def mark_davo_ariza_olib_kelindi(xat_id, ish_raqami, imzo_sana):
    """Davo ariza Palata/suddan ish raqami va imzo sanasi bilan qaytarilganda chaqiriladi."""
    conn = get_conn()
    conn.execute("UPDATE xatlar SET davo_ariza_holati='olib_kelindi', "
                 "davo_ariza_ish_raqami=?, davo_ariza_imzo_sana=? WHERE id=?",
                 (ish_raqami, imzo_sana, xat_id))
    conn.commit()
    conn.close()


def get_davo_ariza_pending_by_turi(turi):
    """Muayyan turdagi, hali 'olib_kelindi' bo'lmagan Davo arizalar ro'yxati."""
    conn = get_conn()
    rows = conn.execute('''
        SELECT * FROM xatlar
        WHERE davo_ariza_turi=? AND davo_ariza_holati='tayyor'
    ''', (turi,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_davo_ariza_hisoboti():
    """Davo ariza tayyorlangan barcha mijozlar bo'yicha to'liq hisobot."""
    conn = get_conn()
    rows = conn.execute('''
        SELECT * FROM xatlar
        WHERE davo_ariza_fayl_yoli IS NOT NULL AND davo_ariza_fayl_yoli != ''
        ORDER BY davo_ariza_sana DESC
    ''').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_taminot(anketa_raqami):
    conn = get_conn()
    row = conn.execute('SELECT * FROM davo_taminot WHERE anketa_raqami=?', (anketa_raqami,)).fetchone()
    conn.close()
    return dict(row) if row else None


def upsert_taminot(anketa_raqami, **fields):
    conn = get_conn()
    now = datetime.datetime.now().isoformat()
    existing = conn.execute('SELECT anketa_raqami FROM davo_taminot WHERE anketa_raqami=?',
                             (anketa_raqami,)).fetchone()
    cols = ['taminot_turi', 'kafil_ism', 'kafil_manzil', 'kafil_pinfl', 'kafil_passport',
            'kafil_passport_sana', 'kafil_passport_organ', 'kafil_tel', 'garov_tavsifi',
            'garov_bahosi', 'pochta_xarajati']
    values = {c: fields.get(c, '') for c in cols}
    if existing:
        set_clause = ', '.join(f'{c}=?' for c in cols)
        conn.execute(f'UPDATE davo_taminot SET {set_clause}, yangilangan_sana=? WHERE anketa_raqami=?',
                     [values[c] for c in cols] + [now, anketa_raqami])
    else:
        all_cols = ['anketa_raqami'] + cols + ['yangilangan_sana']
        placeholders = ','.join(['?'] * len(all_cols))
        conn.execute(f'INSERT INTO davo_taminot ({",".join(all_cols)}) VALUES ({placeholders})',
                     [anketa_raqami] + [values[c] for c in cols] + [now])
    conn.commit()
    conn.close()


def bulk_upsert_taminot(records):
    """records: list of dicts with 'anketa_raqami' + the davo_taminot fields."""
    conn = get_conn()
    now = datetime.datetime.now().isoformat()
    cols = ['taminot_turi', 'kafil_ism', 'kafil_manzil', 'kafil_pinfl', 'kafil_passport',
            'kafil_passport_sana', 'kafil_passport_organ', 'kafil_tel', 'garov_tavsifi',
            'garov_bahosi', 'pochta_xarajati']
    all_cols = ['anketa_raqami'] + cols + ['yangilangan_sana']
    placeholders = ','.join(['?'] * len(all_cols))
    set_clause = ', '.join(f'{c}=excluded.{c}' for c in cols)
    sql = f'''INSERT INTO davo_taminot ({",".join(all_cols)}) VALUES ({placeholders})
              ON CONFLICT(anketa_raqami) DO UPDATE SET {set_clause}, yangilangan_sana=excluded.yangilangan_sana'''
    rows = []
    for r in records:
        rows.append([r.get('anketa_raqami')] + [r.get(c, '') for c in cols] + [now])
    conn.executemany(sql, rows)
    conn.commit()
    conn.close()


def get_xatlar_yuborilgan_davo_kerak():
    """'Yuborildi' holatidagi, hali davo ariza tayyorlanmagan xatlar."""
    conn = get_conn()
    rows = conn.execute('''
        SELECT * FROM xatlar WHERE holat='yuborildi'
        ORDER BY yuborilgan_sana DESC
    ''').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_xat_by_id(xat_id):
    conn = get_conn()
    row = conn.execute('SELECT * FROM xatlar WHERE id=?', (xat_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_muddati_otganlar():
    """3 kunlik muddat o'tgan, lekin hali yuborilmagan xatlarni belgilaydi."""
    conn = get_conn()
    now = datetime.datetime.now().isoformat()
    conn.execute('''
        UPDATE xatlar SET holat='muddati_otgan'
        WHERE holat='tayyor' AND muddat_sana < ?
    ''', (now,))
    conn.commit()
    n = conn.execute("SELECT COUNT(*) c FROM xatlar WHERE holat='muddati_otgan'").fetchone()['c']
    conn.close()
    return n


def get_davo_ariza_muddati_otganlar(muddat_kun=None):
    """
    Davo ariza tayyorlangan (yaratilgan), lekin belgilangan muddat ichida
    (standart 5 kun) hali 'olib kelindi' deb belgilanmagan mijozlar ro'yxati.
    """
    if muddat_kun is None:
        muddat_kun = int(get_setting('davo_ariza_muddati_kun', 5))
    chegara = (datetime.datetime.now() - datetime.timedelta(days=muddat_kun)).isoformat()
    conn = get_conn()
    rows = conn.execute('''
        SELECT * FROM xatlar
        WHERE davo_ariza_fayl_yoli IS NOT NULL AND davo_ariza_fayl_yoli != ''
          AND (davo_ariza_holati IS NULL OR davo_ariza_holati != 'olib_kelindi')
          AND davo_ariza_sana < ?
        ORDER BY davo_ariza_sana ASC
    ''', (chegara,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
