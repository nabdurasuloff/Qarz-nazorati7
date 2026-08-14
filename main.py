# -*- coding: utf-8 -*-
"""
Qarz Nazorat Dastur — Bosh oyna (Tkinter GUI)

Ishga tushirish:  python main.py
"""
import os
import sys
import threading
import datetime
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

import database as db
import importer
import letters
import util

def _app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


APP_DIR = _app_dir()
XATLAR_DIR = os.path.join(APP_DIR, 'yaratilgan_xatlar')


def bugungi_papka():
    """Bugungi sana bo'yicha papka (masalan yaratilgan_xatlar/14.08.2026) — mavjud bo'lmasa yaratadi."""
    sana_papka = datetime.date.today().strftime('%d.%m.%Y')
    path = os.path.join(XATLAR_DIR, sana_papka)
    os.makedirs(path, exist_ok=True)
    return path

BG = '#F7F3EA'
INK = '#20281F'
STAMP = '#2F5233'
KRAFT = '#A9805A'
WHITE = '#FFFDF8'
ERR = '#8C3B2E'


resolve_mijoz = util.resolve_mijoz  # qulaylik uchun shu modulda ham mavjud


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Qarz Nazorat va Talabnoma Tizimi")
        self.geometry("1180x720")
        self.configure(bg=BG)

        self._setup_style()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.tab_dashboard = DashboardTab(self.notebook, self)
        self.tab_portfel = PortfelTab(self.notebook, self)
        self.tab_mijozlar = MijozlarTab(self.notebook, self)
        self.tab_tahlil = TahlilTab(self.notebook, self)
        self.tab_xatlar = XatlarTab(self.notebook, self)
        self.tab_davo = DavoArizaTab(self.notebook, self)
        self.tab_davo_hisobot = DavoHisobotTab(self.notebook, self)
        self.tab_sozlamalar = SozlamalarTab(self.notebook, self)

        self.notebook.add(self.tab_dashboard, text='  Bosh sahifa  ')
        self.notebook.add(self.tab_portfel, text='  Portfel  ')
        self.notebook.add(self.tab_mijozlar, text='  Mijozlar bazasi  ')
        self.notebook.add(self.tab_tahlil, text='  Tahlil / Talabnoma  ')
        self.notebook.add(self.tab_xatlar, text='  Xatlar holati  ')
        self.notebook.add(self.tab_davo, text='  Davo ariza  ')
        self.notebook.add(self.tab_davo_hisobot, text='  Davo ariza hisoboti  ')
        self.notebook.add(self.tab_sozlamalar, text='  Sozlamalar  ')

        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

        self._check_muddat_otganlar()

    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('TNotebook', background=BG, borderwidth=0)
        style.configure('TNotebook.Tab', font=('Segoe UI', 10, 'bold'), padding=[14, 8])
        style.configure('TFrame', background=BG)
        style.configure('TLabel', background=BG, foreground=INK, font=('Segoe UI', 10))
        style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'), foreground=INK)
        style.configure('Sub.TLabel', font=('Segoe UI', 9), foreground='#5B6459')
        style.configure('Stat.TLabel', font=('Consolas', 22, 'bold'), foreground=STAMP)
        style.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=8)
        style.configure('Accent.TButton', background=STAMP, foreground=WHITE)
        style.map('Accent.TButton', background=[('active', '#3E6B45')])
        style.configure('Treeview', font=('Segoe UI', 9), rowheight=26)
        style.configure('Treeview.Heading', font=('Segoe UI', 9, 'bold'))

    def _on_tab_changed(self, event):
        current = event.widget.tab(event.widget.select(), 'text').strip()
        if current == 'Bosh sahifa':
            self.tab_dashboard.refresh()
        elif current == 'Tahlil / Talabnoma':
            self.tab_tahlil.refresh_stats()
        elif current == 'Xatlar holati':
            self.tab_xatlar.refresh()
        elif current == 'Davo ariza':
            self.tab_davo.refresh()
        elif current == 'Davo ariza hisoboti':
            self.tab_davo_hisobot.refresh()

    def _check_muddat_otganlar(self):
        n = db.update_muddati_otganlar()
        n_davo = len(db.get_davo_ariza_muddati_otganlar())
        if n > 0 or n_davo > 0:
            xabar = []
            if n > 0:
                xabar.append(f"• {n} ta xat yuborish muddati tugagan! 'Xatlar holati' bo'limini tekshiring.")
            if n_davo > 0:
                xabar.append(f"• {n_davo} ta Davo ariza tayyorlangan, lekin belgilangan muddat (5 kun) "
                              f"ichida 'Olib kelindi' deb belgilanmagan! 'Davo ariza' bo'limini tekshiring.")
            messagebox.showwarning("Eslatma", "\n\n".join(xabar))
        self.after(60 * 60 * 1000, self._check_muddat_otganlar)  # har soatda tekshirish


class ScrollableFrame(ttk.Frame):
    """Vertikal scroll qila oladigan konteyner."""
    def __init__(self, parent):
        super().__init__(parent)
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=canvas.yview)
        self.body = ttk.Frame(canvas)

        self.body.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas_window = canvas.create_window((0, 0), window=self.body, anchor='nw')
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        canvas.bind_all('<MouseWheel>', _on_mousewheel)


def _fmt_summa_qisqa(v):
    v = v or 0
    if v >= 1_000_000_000:
        return f"{v / 1_000_000_000:.1f} mlrd"
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f} mln"
    return f"{v:,.0f}".replace(',', ' ')


class DashboardTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        scroll = ScrollableFrame(self)
        scroll.pack(fill='both', expand=True)
        body = scroll.body

        ttk.Label(body, text="Qarz Nazorat va Talabnoma Tizimi", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(20, 4))
        ttk.Label(body, text="Portfelni tahlil qiling, muddati o'tgan mijozlarga xat tayyorlang.",
                  style='Sub.TLabel').pack(anchor='w', padx=20, pady=(0, 16))

        cards = ttk.Frame(body)
        cards.pack(fill='x', padx=20)
        self.card_portfel = self._card(cards, "Portfeldagi kreditlar")
        self.card_45kun = self._card(cards, "45+ kun muddati o'tgan")
        self.card_tayyor = self._card(cards, "Yuborilmagan xatlar")
        self.card_otgan = self._card(cards, "Muddati o'tgan xatlar")

        # ---- Bugungi harakatlar ----
        ttk.Label(body, text="Bugungi harakatlar", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(24, 8))
        today_cards = ttk.Frame(body)
        today_cards.pack(fill='x', padx=20)
        self.card_bugun_yaratildi = self._card(today_cards, "Bugun yaratilgan xatlar", small=True)
        self.card_bugun_yuborildi = self._card(today_cards, "Bugun yuborilgan xatlar", small=True)
        self.card_davo_muddati = self._card(today_cards, "Davo ariza muddati o'tgan", small=True)

        # ---- Statistika (grafik) ----
        ttk.Label(body, text="Statistika", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(24, 8))
        charts_row = ttk.Frame(body)
        charts_row.pack(fill='x', padx=20)

        viloyat_box = tk.Frame(charts_row, bg=WHITE, highlightbackground='#E4DCC8', highlightthickness=1)
        viloyat_box.pack(side='left', fill='both', expand=True, padx=(0, 8), ipady=10)
        tk.Label(viloyat_box, text="Tarmoq bo'yicha Stage 3 kreditlar",
                 bg=WHITE, fg=INK, font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=12, pady=(4, 8))
        self.viloyat_canvas = tk.Canvas(viloyat_box, bg=WHITE, height=200, highlightthickness=0)
        self.viloyat_canvas.pack(fill='x', padx=12, pady=(0, 8))

        turi_box = tk.Frame(charts_row, bg=WHITE, highlightbackground='#E4DCC8', highlightthickness=1)
        turi_box.pack(side='left', fill='both', expand=True, padx=(8, 0), ipady=10)
        tk.Label(turi_box, text="Jismoniy / Yuridik shaxslar taqsimoti",
                 bg=WHITE, fg=INK, font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=12, pady=(4, 8))
        self.turi_canvas = tk.Canvas(turi_box, bg=WHITE, height=200, highlightthickness=0)
        self.turi_canvas.pack(fill='x', padx=12, pady=(0, 8))

        # ---- So'nggi harakatlar ----
        ttk.Label(body, text="So'nggi harakatlar", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(24, 8))
        cols = ('sana', 'mijoz', 'xat_turi', 'holat')
        self.recent_tree = ttk.Treeview(body, columns=cols, show='headings', height=8)
        headings = {'sana': 'Sana', 'mijoz': 'Mijoz', 'xat_turi': 'Xat turi', 'holat': 'Holat'}
        widths = {'sana': 140, 'mijoz': 320, 'xat_turi': 110, 'holat': 130}
        for c in cols:
            self.recent_tree.heading(c, text=headings[c])
            self.recent_tree.column(c, width=widths[c])
        self.recent_tree.pack(fill='x', padx=20, pady=(0, 10))

        # ---- Ishlash tartibi ----
        info = ttk.Frame(body)
        info.pack(fill='x', padx=20, pady=(14, 30))
        ttk.Label(info, text="Ishlash tartibi:", style='Header.TLabel').pack(anchor='w')
        steps = [
            "1. 'Portfel' bo'limida .xlsb faylni yuklang.",
            "2. 'Mijozlar bazasi' bo'limida jismoniy/yuridik shaxslar ma'lumotini import qiling.",
            "3. 'Tahlil / Talabnoma' bo'limida 45 kundan o'tgan mijozlarni ko'ring, xat yarating.",
            "4. 'Xatlar holati' bo'limida yuborilganlarni belgilang — 3 kun ichida yuborilmasa, eslatma chiqadi.",
        ]
        for s in steps:
            ttk.Label(info, text=s, font=('Segoe UI', 10)).pack(anchor='w', pady=3)

        self.refresh()

    def _card(self, parent, title, small=False):
        f = tk.Frame(parent, bg=WHITE, highlightbackground='#E4DCC8', highlightthickness=1)
        f.pack(side='left', expand=True, fill='both', padx=6, ipady=14 if not small else 10)
        num = tk.Label(f, text='0', bg=WHITE, fg=STAMP, font=('Consolas', 22 if small else 26, 'bold'))
        num.pack(pady=(10, 0))
        tk.Label(f, text=title, bg=WHITE, fg='#5B6459', font=('Segoe UI', 9),
                 wraplength=220, justify='center').pack(pady=(0, 8))
        return num

    def _draw_hbar_chart(self, canvas, items, label_key, value_key, value_fmt=str, color=STAMP):
        """items: list of dict; oddiy tk.Canvas'da gorizontal ustunli diagramma chizadi."""
        canvas.delete('all')
        canvas.update_idletasks()
        width = canvas.winfo_width() or 380
        if not items:
            canvas.create_text(width // 2, 90, text="Ma'lumot yo'q", fill='#5B6459', font=('Segoe UI', 9))
            return
        max_val = max((it[value_key] or 0) for it in items) or 1
        row_h = 22
        label_w = 150
        bar_max_w = max(width - label_w - 130, 40)
        y = 8
        for it in items:
            label = str(it[label_key])[:22]
            val = it[value_key] or 0
            bar_w = int((val / max_val) * bar_max_w)
            canvas.create_text(4, y + row_h // 2, text=label, anchor='w',
                                font=('Segoe UI', 8), fill=INK)
            canvas.create_rectangle(label_w, y + 3, label_w + bar_w, y + row_h - 3,
                                     fill=color, outline='')
            canvas.create_text(label_w + bar_w + 6, y + row_h // 2,
                                text=value_fmt(val), anchor='w',
                                font=('Segoe UI', 8), fill='#5B6459')
            y += row_h
        canvas.configure(height=max(y + 6, 60))

    def refresh(self):
        conn = db.get_conn()
        portfel_n = conn.execute('SELECT COUNT(*) c FROM portfel').fetchone()['c']
        conn.close()
        chegara = int(db.get_setting('dpd_chegara_kun', 45))
        kun45 = len(db.get_portfel_45_kun(chegara))
        tayyor = len(db.get_xatlar('tayyor'))
        otgan = len(db.get_xatlar('muddati_otgan'))

        self.card_portfel.config(text=str(portfel_n))
        self.card_45kun.config(text=str(kun45))
        self.card_tayyor.config(text=str(tayyor))
        self.card_otgan.config(text=str(otgan))
        self.card_otgan.config(fg=ERR if otgan > 0 else STAMP)

        bugungi = db.get_bugungi_harakatlar()
        self.card_bugun_yaratildi.config(text=str(bugungi['yaratildi']))
        self.card_bugun_yuborildi.config(text=str(bugungi['yuborildi']))
        n_davo_otgan = len(db.get_davo_ariza_muddati_otganlar())
        self.card_davo_muddati.config(text=str(n_davo_otgan), fg=ERR if n_davo_otgan > 0 else STAMP)

        tarmoq_data = db.get_tarmoq_stage3_breakdown(limit=8)
        self._draw_hbar_chart(
            self.viloyat_canvas, tarmoq_data, 'tarmoq', 'jami',
            value_fmt=_fmt_summa_qisqa, color=STAMP
        )

        turi_data = db.get_turi_breakdown(chegara)
        turi_items = [
            {'nomi': 'Jismoniy', 'soni': turi_data['jismoniy']},
            {'nomi': 'Yuridik', 'soni': turi_data['yuridik']},
        ]
        self._draw_hbar_chart(self.turi_canvas, turi_items, 'nomi', 'soni', color=KRAFT)

        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)
        recent = db.get_xatlar()[:10]
        status_labels = {'tayyor': 'Tayyor', 'yuborildi': '✓ Yuborildi', 'muddati_otgan': "⚠ Muddati o'tgan"}
        for r in recent:
            try:
                sana = datetime.datetime.fromisoformat(r['yaratilgan_sana']).strftime('%d.%m.%Y %H:%M')
            except Exception:
                sana = r['yaratilgan_sana'] or ''
            self.recent_tree.insert('', 'end', values=(
                sana, r['mijoz_nomi'], r['xat_turi'], status_labels.get(r['holat'], r['holat'])
            ))


class PortfelTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="Portfel ma'lumotlarini import qilish", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(20, 4))
        ttk.Label(self, text="IFRS portfel hisobotini (.xlsb) yuklang. Mavjud bo'lsa, eski "
                              "ma'lumotlar almashtiriladi.", style='Sub.TLabel').pack(
            anchor='w', padx=20, pady=(0, 16))

        btn_frame = ttk.Frame(self)
        btn_frame.pack(anchor='w', padx=20)
        ttk.Button(btn_frame, text="📂 .xlsb faylni tanlash va import qilish",
                   style='Accent.TButton', command=self.import_file).pack(side='left')

        self.status_label = ttk.Label(self, text='', style='Sub.TLabel')
        self.status_label.pack(anchor='w', padx=20, pady=10)

        self.progress = ttk.Progressbar(self, mode='determinate', length=400)
        self.progress.pack(anchor='w', padx=20, pady=(0, 10))

        cols = ('anketa', 'mijoz', 'turi', 'dpd', 'jami_qarz')
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=18)
        headings = {'anketa': 'Anketa №', 'mijoz': 'Mijoz nomi', 'turi': 'Turi',
                    'dpd': 'DPD (kun)', 'jami_qarz': "Muddati o'tgan qarz"}
        widths = {'anketa': 100, 'mijoz': 350, 'turi': 90, 'dpd': 90, 'jami_qarz': 160}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c])
        self.tree.pack(fill='both', expand=True, padx=20, pady=10)

        self.refresh_table()

    def import_file(self):
        filepath = filedialog.askopenfilename(
            title="Portfel faylini tanlang",
            filetypes=[("Excel Binary", "*.xlsb"), ("Barcha fayllar", "*.*")]
        )
        if not filepath:
            return
        self.status_label.config(text="Import qilinmoqda...")
        self.progress['value'] = 0

        def worker():
            try:
                db.clear_portfel()

                def cb(i, total):
                    pct = int(i / max(total, 1) * 100)
                    self.progress['value'] = pct

                result = importer.import_portfel_xlsb(filepath, progress_cb=cb)
                self.progress['value'] = 100
                msg = f"Tayyor! {result['jami_qator']} ta qator import qilindi (varaq: {result['sheet']})."
                if result['topilmagan_ustunlar']:
                    msg += f"\nOgohlantirish: {len(result['topilmagan_ustunlar'])} ta ustun faylda topilmadi."
                self.status_label.config(text=msg)
                self.refresh_table()
                self.app.tab_dashboard.refresh()
            except Exception as e:
                messagebox.showerror("Xato", f"Import vaqtida xato: {e}")
                self.status_label.config(text="Xato yuz berdi.")

        threading.Thread(target=worker, daemon=True).start()

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        conn = db.get_conn()
        rows = conn.execute('SELECT * FROM portfel ORDER BY dpd_max DESC LIMIT 500').fetchall()
        conn.close()
        for r in rows:
            self.tree.insert('', 'end', values=(
                r['anketa_raqami'], r['mijoz_nomi'], r['mijoz_turi'], r['dpd_max'],
                f"{r['jami_qarz']:,.0f}".replace(',', ' ') if r['jami_qarz'] else '0'
            ))


class MijozlarTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="Mijozlar bazasini import qilish", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(20, 4))

        # ---- Tavsiya etilgan usul: xom matn (.txt / .zip) ----
        ttk.Label(self, text="Tavsiya etiladi: bank tizimidan olingan xom matn fayli",
                  style='Header.TLabel').pack(anchor='w', padx=20, pady=(10, 2))
        ttk.Label(self, text="Bank tizimidan '|' bilan ajratilgan xom (.txt yoki uni ichiga olgan "
                              ".zip) faylni to'g'ridan-to'g'ri yuklang — Excel orqali o'tmagani "
                              "uchun hech qanday ma'lumot buzilmaydi, ustunlarni moslashtirish "
                              "shart emas.",
                  style='Sub.TLabel', wraplength=900, justify='left').pack(
            anchor='w', padx=20, pady=(0, 10))
        ttk.Button(self, text="📄 Xom matn (.txt / .zip) faylni import qilish",
                   style='Accent.TButton',
                   command=self.import_txt_file).pack(anchor='w', padx=20)

        self.txt_status_label = ttk.Label(self, text='', style='Sub.TLabel')
        self.txt_status_label.pack(anchor='w', padx=20, pady=(8, 0))
        self.txt_progress = ttk.Progressbar(self, mode='determinate', length=400)
        self.txt_progress.pack(anchor='w', padx=20, pady=(6, 4))

        # ---- Muqobil usul: Excel (ustunlarni qo'lda moslashtirish) ----
        sep = ttk.Frame(self, height=2)
        sep.pack(fill='x', padx=20, pady=(18, 14))
        ttk.Label(self, text="Muqobil usul: Excel fayl (ustunlarni o'zingiz moslashtirasiz)",
                  style='Header.TLabel').pack(anchor='w', padx=20, pady=(0, 4))
        ttk.Label(self, text="Agar xom matn fayli mavjud bo'lmasa, Excel (.xlsx) faylni "
                              "yuklab, ustunlarni qo'lda moslashtirishingiz mumkin.",
                  style='Sub.TLabel').pack(anchor='w', padx=20, pady=(0, 10))

        btns = ttk.Frame(self)
        btns.pack(anchor='w', padx=20)
        ttk.Button(btns, text="👤 Jismoniy shaxslar Excel faylini import qilish",
                   command=lambda: self.import_file('jismoniy')).pack(side='left', padx=(0, 10))
        ttk.Button(btns, text="🏢 Yuridik shaxslar Excel faylini import qilish",
                   command=lambda: self.import_file('yuridik')).pack(side='left')

        self.status_label = ttk.Label(self, text='', style='Sub.TLabel')
        self.status_label.pack(anchor='w', padx=20, pady=14)

        stats = ttk.Frame(self)
        stats.pack(anchor='w', padx=20)
        self.lbl_jis = ttk.Label(stats, text="Jismoniy shaxslar: 0")
        self.lbl_jis.pack(anchor='w', pady=2)
        self.lbl_yur = ttk.Label(stats, text="Yuridik shaxslar: 0")
        self.lbl_yur.pack(anchor='w', pady=2)
        self.refresh_stats()

    def import_txt_file(self):
        filepath = filedialog.askopenfilename(
            title="Xom matn (.txt) yoki .zip faylni tanlang",
            filetypes=[("Matn / Zip", "*.txt *.zip"), ("Barcha fayllar", "*.*")]
        )
        if not filepath:
            return
        self.txt_status_label.config(text="Import qilinmoqda... (katta fayllar 20-30 sekund olishi mumkin)")
        self.txt_progress['value'] = 0

        def worker():
            try:
                def cb(i, total):
                    pct = int(i / max(total, 1) * 100)
                    self.txt_progress['value'] = pct

                result = importer.import_clients_txt(filepath, progress_cb=cb)
                self.txt_progress['value'] = 100
                msg = (f"Tayyor! {result['import_qilingan']} / {result['jami_qator']} "
                       f"yozuv import qilindi.")
                if result['otkazib_yuborildi']:
                    msg += f" ({result['otkazib_yuborildi']} ta qator o'tkazib yuborildi.)"
                self.txt_status_label.config(text=msg)
                self.refresh_stats()
            except Exception as e:
                messagebox.showerror("Xato", f"Import vaqtida xato: {e}")
                self.txt_status_label.config(text="Xato yuz berdi.")

        threading.Thread(target=worker, daemon=True).start()

    def refresh_stats(self):
        conn = db.get_conn()
        jis = conn.execute("SELECT COUNT(*) c FROM mijozlar WHERE turi='jismoniy'").fetchone()['c']
        yur = conn.execute("SELECT COUNT(*) c FROM mijozlar WHERE turi='yuridik'").fetchone()['c']
        conn.close()
        self.lbl_jis.config(text=f"Jismoniy shaxslar: {jis}")
        self.lbl_yur.config(text=f"Yuridik shaxslar: {yur}")

    def import_file(self, turi):
        filepath = filedialog.askopenfilename(
            title="Mijozlar faylini tanlang",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Barcha fayllar", "*.*")]
        )
        if not filepath:
            return
        try:
            cols, preview_df = importer.preview_mijozlar_columns(filepath)
        except Exception as e:
            messagebox.showerror("Xato", f"Fayl o'qilmadi: {e}")
            return

        dialog = ColumnMapDialog(self, cols, preview_df, turi)
        self.wait_window(dialog)
        if not dialog.result:
            return

        self.status_label.config(text="Import qilinmoqda...")

        def worker():
            try:
                result = importer.import_mijozlar_xlsx(filepath, turi, dialog.result)
                self.status_label.config(
                    text=f"Tayyor! {result['import_qilingan']} / {result['jami_qator']} qator import qilindi.")
                self.refresh_stats()
            except Exception as e:
                messagebox.showerror("Xato", f"Import vaqtida xato: {e}")

        threading.Thread(target=worker, daemon=True).start()


class ColumnMapDialog(tk.Toplevel):
    """Excel ustunlarini bazadagi maydonlarga moslashtirish oynasi."""
    FIELDS = [
        ('kalit', "Bog'lovchi ID (STIR / PINFL / Уникал) *", True),
        ('ism', "Ism-familiya / Tashkilot nomi *", True),
        ('manzil', "Manzil", False),
        ('telefon', "Telefon", False),
        ('hujjat_raqami', "Passport / STIR raqami", False),
        ('rahbar_ism', "Rahbar F.I.Sh (yuridik shaxs uchun)", False),
    ]

    def __init__(self, parent, columns, preview_df, turi):
        super().__init__(parent)
        self.title(f"Ustunlarni moslashtirish — {turi}")
        self.geometry("560x480")
        self.configure(bg=BG)
        self.result = None
        self.columns = [''] + list(columns)

        ttk.Label(self, text="Har bir maydon uchun mos Excel ustunini tanlang:",
                  style='Header.TLabel').pack(anchor='w', padx=16, pady=(16, 10))

        self.vars = {}
        form = ttk.Frame(self)
        form.pack(fill='x', padx=16)
        for field, label, required in self.FIELDS:
            row = ttk.Frame(form)
            row.pack(fill='x', pady=4)
            ttk.Label(row, text=label, width=38).pack(side='left')
            var = tk.StringVar(value='')
            combo = ttk.Combobox(row, textvariable=var, values=self.columns, state='readonly', width=28)
            combo.pack(side='left')
            self.vars[field] = var

        btns = ttk.Frame(self)
        btns.pack(fill='x', padx=16, pady=16, side='bottom')
        ttk.Button(btns, text="Bekor qilish", command=self.destroy).pack(side='right', padx=4)
        ttk.Button(btns, text="Import qilish", style='Accent.TButton',
                   command=self.on_confirm).pack(side='right', padx=4)

        self.transient(parent)
        self.grab_set()

    def on_confirm(self):
        mapping = {f: v.get() for f, v in self.vars.items() if v.get()}
        if not mapping.get('kalit') or not mapping.get('ism'):
            messagebox.showerror("Xato", "Bog'lovchi ID va Ism ustunlari majburiy.")
            return
        self.result = mapping
        self.destroy()


class TahlilTab(ttk.Frame):
    PAKET_OPTIONS = ['10', '30', '50', '100', 'Barchasi']

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Tahlil va Talabnoma", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(20, 4))
        self.sub_label = ttk.Label(self, text='', style='Sub.TLabel')
        self.sub_label.pack(anchor='w', padx=20, pady=(0, 10))

        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=20)
        ttk.Button(toolbar, text="🔍 Tahlil qilish (yangilash)",
                   command=self.refresh_stats).pack(side='left')

        self.only_new_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(toolbar, text="Faqat xat yaratilmagan / muddati o'tganlar",
                         variable=self.only_new_var,
                         command=self.refresh_stats).pack(side='left', padx=14)

        paket_frame = ttk.Frame(self)
        paket_frame.pack(fill='x', padx=20, pady=(10, 6))
        ttk.Label(paket_frame, text="Paket hajmi:").pack(side='left')
        self.paket_var = tk.StringVar(value='30')
        ttk.Combobox(paket_frame, textvariable=self.paket_var, values=self.PAKET_OPTIONS,
                     state='readonly', width=10).pack(side='left', padx=8)
        ttk.Button(paket_frame, text="① Birinchi paketni belgilash",
                   command=self.select_paket).pack(side='left', padx=6)
        ttk.Button(paket_frame, text="📊 Excel'ga eksport qilish (tanlanganlar)",
                   command=self.export_excel).pack(side='left', padx=6)
        ttk.Button(paket_frame, text="📥 Tahrirlangan Excel'ni yuklash",
                   command=self.import_excel_updates).pack(side='left', padx=6)

        format_frame = ttk.Frame(self)
        format_frame.pack(fill='x', padx=20, pady=(0, 6))
        ttk.Label(format_frame, text="Xat fayl formati:").pack(side='left')
        self.format_var = tk.StringVar(value='Word (.docx)')
        ttk.Combobox(format_frame, textvariable=self.format_var,
                     values=['Word (.docx)', 'PDF (.pdf)'],
                     state='readonly', width=14).pack(side='left', padx=8)
        ttk.Label(format_frame, text="(PDF uchun kompyuterda Microsoft Word o'rnatilgan bo'lishi kerak)",
                  style='Sub.TLabel').pack(side='left', padx=6)

        gen_frame = ttk.Frame(self)
        gen_frame.pack(fill='x', padx=20, pady=(0, 6))
        ttk.Button(gen_frame, text="✉ Tanlanganlar uchun xat yaratish (ommaviy)",
                   style='Accent.TButton', command=self.generate_bulk).pack(side='left')

        search_frame = ttk.Frame(self)
        search_frame.pack(fill='x', padx=20, pady=(14, 6))
        ttk.Label(search_frame, text="Bitta mijozga: Anketa raqami").pack(side='left')
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var, width=20).pack(side='left', padx=8)
        ttk.Button(search_frame, text="Qidirish", command=self.search_single).pack(side='left')
        ttk.Button(search_frame, text="✉ Xatni yuborish (shu mijozga)",
                   command=self.generate_single).pack(side='left', padx=8)

        cols = ('anketa', 'mijoz', 'turi', 'dpd', 'jami_qarz', 'mijoz_topildi', 'holat')
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=14, selectmode='extended')
        headings = {'anketa': 'Anketa №', 'mijoz': 'Mijoz nomi', 'turi': 'Turi',
                    'dpd': 'DPD (kun)', 'jami_qarz': "Muddati o'tgan qarz",
                    'mijoz_topildi': "Bazada mavjud?", 'holat': 'Oldingi xat holati'}
        widths = {'anketa': 90, 'mijoz': 280, 'turi': 80, 'dpd': 80, 'jami_qarz': 140,
                  'mijoz_topildi': 100, 'holat': 130}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c])
        self.tree.pack(fill='both', expand=True, padx=20, pady=10)
        ttk.Label(self, text="Ctrl / Shift bosib bir nechta mijozni tanlashingiz mumkin.",
                  style='Sub.TLabel').pack(anchor='w', padx=20, pady=(0, 10))

        self._rows_cache = []
        self.refresh_stats()

    def refresh_stats(self):
        chegara = int(db.get_setting('dpd_chegara_kun', 45))
        rows = db.get_portfel_45_kun(chegara)
        status_map = db.get_latest_xat_status_by_portfel()

        if self.only_new_var.get():
            rows = [r for r in rows if status_map.get(r['id']) not in ('tayyor', 'yuborildi')]

        self._rows_cache = rows
        self._status_map = status_map
        self.sub_label.config(
            text=f"{chegara}+ kun muddati o'tgan mijozlar: {len(rows)} ta "
                 f"(jami tahlil qilingan {len(db.get_portfel_45_kun(chegara))} tadan)")
        self._fill_tree(rows)

    def _fill_tree(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)
        status_labels = {'tayyor': 'Tayyor', 'yuborildi': 'Yuborilgan',
                          'muddati_otgan': "⚠ Muddati o'tgan"}
        for r in rows:
            turi, mijoz = resolve_mijoz(r)
            holat = status_labels.get(self._status_map.get(r['id']), '—') if hasattr(self, '_status_map') else '—'
            self.tree.insert('', 'end', iid=str(r['id']), values=(
                r['anketa_raqami'], r['mijoz_nomi'], turi, r['dpd_max'],
                f"{r['jami_qarz']:,.0f}".replace(',', ' ') if r['jami_qarz'] else '0',
                "Ha" if mijoz else "Yo'q", holat
            ))

    def select_paket(self):
        paket = self.paket_var.get()
        all_items = self.tree.get_children()
        if not all_items:
            messagebox.showinfo("Diqqat", "Ro'yxat bo'sh.")
            return
        n = len(all_items) if paket == 'Barchasi' else int(paket)
        to_select = all_items[:n]
        self.tree.selection_set(to_select)
        if to_select:
            self.tree.see(to_select[0])
        messagebox.showinfo("Tanlandi", f"{len(to_select)} ta mijoz tanlandi (paket hajmi: {paket}).")

    def _selected_rows(self):
        selected = self.tree.selection()
        if not selected:
            return []
        ids = [int(i) for i in selected]
        return [r for r in self._rows_cache if r['id'] in ids]

    def _rows_for_excel(self, portfel_rows):
        out = []
        for r in portfel_rows:
            turi, mijoz = resolve_mijoz(r)
            xat_turi = 'Talabnoma' if turi == 'yuridik' else 'Ogohlantirish'
            out.append({
                'anketa_raqami': r.get('anketa_raqami', ''),
                'mijoz_nomi': mijoz['ism'] if mijoz else r.get('mijoz_nomi', ''),
                'turi': turi,
                'manzil': mijoz['manzil'] if mijoz else '',
                'telefon': mijoz['telefon'] if mijoz else '',
                'dpd_max': r.get('dpd_max', 0),
                'jami_qarz': r.get('jami_qarz', 0),
                'xat_turi': xat_turi,
            })
        return out

    def export_excel(self):
        rows = self._selected_rows()
        if not rows:
            messagebox.showinfo("Diqqat", "Avval ro'yxatdan mijozlarni tanlang "
                                           "('Birinchi paketni belgilash' yordam beradi).")
            return
        out_path = filedialog.asksaveasfilename(
            title="Excel faylni saqlash", defaultextension=".xlsx",
            initialfile="talabnoma_royxati.xlsx",
            filetypes=[("Excel", "*.xlsx")]
        )
        if not out_path:
            return
        try:
            excel_rows = self._rows_for_excel(rows)
            importer.export_tahlil_excel(excel_rows, out_path)
            messagebox.showinfo(
                "Tayyor",
                f"{len(excel_rows)} ta qator eksport qilindi:\n{out_path}\n\n"
                "Manzil / Telefon ustunlarini tahrirlab, so'ng "
                "'Tahrirlangan Excel'ni yuklash' orqali qaytaring."
            )
            webbrowser.open(out_path)
        except Exception as e:
            messagebox.showerror("Xato", str(e))

    def import_excel_updates(self):
        filepath = filedialog.askopenfilename(
            title="Tahrirlangan Excel faylni tanlang",
            filetypes=[("Excel", "*.xlsx *.xls")]
        )
        if not filepath:
            return
        try:
            result = importer.import_manzil_updates(filepath)
            msg = f"{result['yangilandi']} ta mijoz manzili/ma'lumoti yangilandi."
            if result['otkazib_yuborildi']:
                msg += f"\n{result['otkazib_yuborildi']} ta qator o'tkazib yuborildi " \
                       f"(anketa raqami portfelda topilmadi)."
            messagebox.showinfo("Tayyor", msg)
            self.refresh_stats()
        except Exception as e:
            messagebox.showerror("Xato", str(e))

    def search_single(self):
        anketa = self.search_var.get().strip()
        if not anketa:
            return
        rows = db.get_portfel_by_anketa(anketa)
        self._status_map = db.get_latest_xat_status_by_portfel()
        self._rows_cache = rows
        self._fill_tree(rows)

    def _generate_for_row(self, portfel_row):
        turi, mijoz = resolve_mijoz(portfel_row)
        xat_turi = 'Talabnoma' if turi == 'yuridik' else 'Ogohlantirish'

        mijoz_ism = mijoz['ism'] if mijoz else portfel_row.get('mijoz_nomi', '')
        mijoz_manzil = mijoz['manzil'] if mijoz else ''
        rahbar_ism = mijoz.get('rahbar_ism') if mijoz else ''

        settings = db.get_all_settings()
        anketa = portfel_row.get('anketa_raqami', 'noma_lum')
        fname = f"{xat_turi}_{letters.safe_filename(anketa)}_{letters.safe_filename(mijoz_ism)}.docx"
        out_path = os.path.join(bugungi_papka(), fname)

        letters.generate_letter(
            output_path=out_path,
            xat_turi=xat_turi,
            mijoz_ism=mijoz_ism,
            mijoz_manzil=mijoz_manzil,
            portfel_row=portfel_row,
            settings=settings,
            anketa_raqami=anketa,
            rahbar_ism=rahbar_ism,
        )

        want_pdf = self.format_var.get().startswith('PDF')
        if want_pdf:
            pdf_path = letters.convert_docx_to_pdf(out_path, delete_docx=True)
            out_path = pdf_path

        muddat_kun = int(settings.get('eslatma_muddati_kun', 3))
        db.create_xat(
            portfel_id=portfel_row['id'],
            anketa_raqami=anketa,
            mijoz_nomi=mijoz_ism,
            mijoz_turi=turi,
            xat_turi=xat_turi,
            fayl_yoli=out_path,
            muddat_kun=muddat_kun,
        )
        return out_path

    def generate_bulk(self):
        rows = self._selected_rows()
        if not rows:
            messagebox.showinfo("Diqqat", "Iltimos, kamida bitta mijozni tanlang "
                                           "('Birinchi paketni belgilash' yordam beradi).")
            return

        os.makedirs(XATLAR_DIR, exist_ok=True)
        created = []
        errors = []
        for r in rows:
            try:
                path = self._generate_for_row(r)
                created.append(path)
            except Exception as e:
                errors.append(f"{r.get('anketa_raqami')}: {e}")

        out_dir = bugungi_papka()
        msg = f"{len(created)} ta xat yaratildi.\nJoylashuv: {out_dir}"
        if errors:
            msg += f"\n\n{len(errors)} ta xatoda:\n" + '\n'.join(errors[:5])
        messagebox.showinfo("Tayyor", msg)
        webbrowser.open(out_dir)
        self.app.tab_dashboard.refresh()
        self.app.tab_xatlar.refresh()
        self.refresh_stats()

    def generate_single(self):
        anketa = self.search_var.get().strip()
        if not anketa:
            messagebox.showinfo("Diqqat", "Anketa raqamini kiriting.")
            return
        rows = db.get_portfel_by_anketa(anketa)
        if not rows:
            messagebox.showinfo("Topilmadi", "Bu anketa raqami bo'yicha ma'lumot topilmadi.")
            return
        row = rows[0]
        os.makedirs(XATLAR_DIR, exist_ok=True)
        try:
            path = self._generate_for_row(row)
            messagebox.showinfo("Tayyor", f"Xat yaratildi:\n{path}")
            webbrowser.open(path)
        except Exception as e:
            messagebox.showerror("Xato", str(e))
        self.app.tab_dashboard.refresh()
        self.app.tab_xatlar.refresh()


class XatlarTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="Xatlar holati", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(20, 4))
        ttk.Label(self, text="Tayyorlangan xat 3 kun ichida yuborilmasa, 'muddati o'tgan' deb belgilanadi.",
                  style='Sub.TLabel').pack(anchor='w', padx=20, pady=(0, 14))

        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=20)
        ttk.Button(toolbar, text="🔄 Yangilash", command=self.refresh).pack(side='left')
        ttk.Button(toolbar, text="✓ Yuborildi deb belgilash", style='Accent.TButton',
                   command=self.mark_sent).pack(side='left', padx=10)
        ttk.Button(toolbar, text="📂 Faylni ochish", command=self.open_file).pack(side='left')

        ttk.Label(self, text="Xat 'Yuborildi' deb belgilangach, 'Davo ariza' bo'limida davo ariza "
                              "tayyorlashingiz mumkin bo'ladi.",
                  style='Sub.TLabel', wraplength=1000, justify='left').pack(anchor='w', padx=20, pady=(4, 8))

        cols = ('anketa', 'mijoz', 'turi', 'xat_turi', 'yaratilgan', 'muddat', 'holat', 'davo_ariza')
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=18)
        headings = {'anketa': 'Anketa №', 'mijoz': 'Mijoz', 'turi': 'Turi', 'xat_turi': 'Xat turi',
                    'yaratilgan': 'Yaratilgan', 'muddat': 'Yuborish muddati', 'holat': 'Holat',
                    'davo_ariza': 'Davo ariza'}
        widths = {'anketa': 90, 'mijoz': 230, 'turi': 80, 'xat_turi': 100,
                  'yaratilgan': 120, 'muddat': 120, 'holat': 110, 'davo_ariza': 110}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c])
        self.tree.tag_configure('otgan', foreground=ERR)
        self.tree.tag_configure('yuborildi', foreground=STAMP)
        self.tree.pack(fill='both', expand=True, padx=20, pady=10)

        self._id_map = {}
        self.refresh()

    def refresh(self):
        db.update_muddati_otganlar()
        for item in self.tree.get_children():
            self.tree.delete(item)
        rows = db.get_xatlar()
        for r in rows:
            tag = ''
            holat_label = r['holat']
            if r['holat'] == 'muddati_otgan':
                tag = 'otgan'
                holat_label = "⚠ Muddati o'tgan"
            elif r['holat'] == 'yuborildi':
                tag = 'yuborildi'
                holat_label = "✓ Yuborildi"
            else:
                holat_label = "Tayyor"

            def fmt_date(s):
                try:
                    return datetime.datetime.fromisoformat(s).strftime('%d.%m.%Y')
                except Exception:
                    return s or ''

            davo_label = "✓ Tayyor" if r.get('davo_ariza_fayl_yoli') else "—"

            iid = str(r['id'])
            self.tree.insert('', 'end', iid=iid, values=(
                r['anketa_raqami'], r['mijoz_nomi'], r['mijoz_turi'], r['xat_turi'],
                fmt_date(r['yaratilgan_sana']), fmt_date(r['muddat_sana']), holat_label, davo_label
            ), tags=(tag,))
            self._id_map[iid] = r

        self.app.tab_dashboard.refresh()

    def mark_sent(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Diqqat", "Xatni tanlang.")
            return
        for iid in selected:
            db.mark_xat_yuborildi(int(iid))
        self.refresh()

    def open_file(self):
        selected = self.tree.selection()
        if not selected:
            return
        r = self._id_map.get(selected[0])
        if r and r['fayl_yoli'] and os.path.exists(r['fayl_yoli']):
            webbrowser.open(r['fayl_yoli'])
        else:
            messagebox.showinfo("Topilmadi", "Fayl topilmadi.")


class TaminotDialog(tk.Toplevel):
    """Bitta mijoz uchun kafil/garov ma'lumotlarini qo'lda kiritish oynasi."""
    FIELDS = [
        ('taminot_turi', "Ta'minot turi", 'combo',
         ['yoq', 'kafillik', 'garov', 'kafillik_garov']),
        ('kafil_ism', 'Kafil F.I.Sh', 'text', None),
        ('kafil_manzil', 'Kafil manzili', 'text', None),
        ('kafil_pinfl', 'Kafil PINFL', 'text', None),
        ('kafil_passport', 'Kafil passport (seriya-raqam)', 'text', None),
        ('kafil_passport_sana', 'Kafil passport berilgan sana', 'text', None),
        ('kafil_passport_organ', 'Kafil passport bergan organ', 'text', None),
        ('kafil_tel', 'Kafil telefon', 'text', None),
        ('garov_tavsifi', 'Garov mulki tavsifi', 'multitext', None),
        ('garov_bahosi', "Garov bahosi (so'm)", 'text', None),
        ('pochta_xarajati', "Pochta xarajati (so'm)", 'text', None),
    ]

    def __init__(self, parent, anketa_raqami, mijoz_nomi):
        super().__init__(parent)
        self.title(f"Ta'minot ma'lumotlari — {mijoz_nomi}")
        self.geometry("560x620")
        self.configure(bg=BG)
        self.anketa_raqami = anketa_raqami
        self.result_saved = False

        ttk.Label(self, text=f"Anketa №{anketa_raqami} — {mijoz_nomi}",
                  style='Header.TLabel').pack(anchor='w', padx=16, pady=(16, 10))

        current = db.get_taminot(anketa_raqami) or {}

        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=canvas.yview)
        body = ttk.Frame(canvas)
        body.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=body, anchor='nw', width=520)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side='left', fill='both', expand=True, padx=(16, 0))
        scrollbar.pack(side='right', fill='y')

        self.vars = {}
        self.text_widgets = {}
        for field, label, kind, options in self.FIELDS:
            row = ttk.Frame(body)
            row.pack(fill='x', pady=5, padx=(0, 16))
            ttk.Label(row, text=label, width=28, wraplength=170).pack(side='left', anchor='n')
            val = current.get(field, '') or ''
            if kind == 'combo':
                var = tk.StringVar(value=str(val) or 'yoq')
                ttk.Combobox(row, textvariable=var, values=options, state='readonly', width=28).pack(side='left')
                self.vars[field] = var
            elif kind == 'multitext':
                txt = tk.Text(row, width=32, height=4, font=('Segoe UI', 9))
                txt.insert('1.0', str(val))
                txt.pack(side='left')
                self.text_widgets[field] = txt
            else:
                var = tk.StringVar(value=str(val))
                ttk.Entry(row, textvariable=var, width=32).pack(side='left')
                self.vars[field] = var

        btns = ttk.Frame(self)
        btns.pack(fill='x', padx=16, pady=14, side='bottom')
        ttk.Button(btns, text="Bekor qilish", command=self.destroy).pack(side='right', padx=4)
        ttk.Button(btns, text="💾 Saqlash", style='Accent.TButton', command=self.save).pack(side='right', padx=4)

        self.transient(parent)
        self.grab_set()

    def save(self):
        fields = {}
        for field, var in self.vars.items():
            fields[field] = var.get().strip()
        for field, txt in self.text_widgets.items():
            fields[field] = txt.get('1.0', 'end').strip()
        db.upsert_taminot(self.anketa_raqami, **fields)
        self.result_saved = True
        self.destroy()


class OlibKelindiDialog(tk.Toplevel):
    """Davo ariza Palata/suddan ish raqami va sana bilan qaytganini tasdiqlash oynasi."""
    def __init__(self, parent, mijoz_nomi):
        super().__init__(parent)
        self.title(f"Olib kelindi — {mijoz_nomi}")
        self.geometry("420x260")
        self.configure(bg=BG)
        self.result = None

        ttk.Label(self, text="Davo ariza olib kelinganini tasdiqlash",
                  style='Header.TLabel').pack(anchor='w', padx=16, pady=(16, 4))
        ttk.Label(self, text=mijoz_nomi, style='Sub.TLabel').pack(anchor='w', padx=16, pady=(0, 14))

        row1 = ttk.Frame(self)
        row1.pack(fill='x', padx=16, pady=6)
        ttk.Label(row1, text="Ish raqami:", width=16).pack(side='left')
        self.ish_raqami_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.ish_raqami_var, width=24).pack(side='left')

        row2 = ttk.Frame(self)
        row2.pack(fill='x', padx=16, pady=6)
        ttk.Label(row2, text="Imzo/kelgan sana:", width=16).pack(side='left')
        self.sana_var = tk.StringVar(value=datetime.date.today().strftime('%d.%m.%Y'))
        ttk.Entry(row2, textvariable=self.sana_var, width=24).pack(side='left')
        ttk.Label(self, text="(format: kun.oy.yil, masalan 14.08.2026)",
                  style='Sub.TLabel').pack(anchor='w', padx=16, pady=(0, 10))

        btns = ttk.Frame(self)
        btns.pack(fill='x', padx=16, pady=16, side='bottom')
        ttk.Button(btns, text="Bekor qilish", command=self.destroy).pack(side='right', padx=4)
        ttk.Button(btns, text="✓ Tasdiqlash", style='Accent.TButton', command=self.confirm).pack(side='right', padx=4)

        self.transient(parent)
        self.grab_set()

    def confirm(self):
        ish_raqami = self.ish_raqami_var.get().strip()
        sana = self.sana_var.get().strip()
        if not ish_raqami or not sana:
            messagebox.showerror("Xato", "Ish raqami va sanani kiriting.")
            return
        self.result = (ish_raqami, sana)
        self.destroy()


class DavoArizaTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Davo ariza tayyorlash", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(20, 4))
        ttk.Label(self, text="Faqat xati 'Yuborildi' deb belgilangan mijozlar ro'yxatda ko'rinadi.",
                  style='Sub.TLabel').pack(anchor='w', padx=20, pady=(0, 10))

        turi_frame = ttk.Frame(self)
        turi_frame.pack(fill='x', padx=20, pady=(0, 6))
        ttk.Label(turi_frame, text="Ariza turi:").pack(side='left')
        self.turi_var = tk.StringVar(value=list(letters.DAVO_ARIZA_NOMLARI.values())[0])
        self._turi_kalitlar = list(letters.DAVO_ARIZA_NOMLARI.keys())
        ttk.Combobox(turi_frame, textvariable=self.turi_var,
                     values=list(letters.DAVO_ARIZA_NOMLARI.values()),
                     state='readonly', width=48).pack(side='left', padx=8)

        format_frame = ttk.Frame(self)
        format_frame.pack(fill='x', padx=20, pady=(0, 8))
        ttk.Label(format_frame, text="Fayl formati:").pack(side='left')
        self.format_var = tk.StringVar(value='Word (.docx)')
        ttk.Combobox(format_frame, textvariable=self.format_var,
                     values=['Word (.docx)', 'PDF (.pdf)'], state='readonly', width=14).pack(side='left', padx=8)
        ttk.Label(format_frame, text="(PDF uchun Microsoft Word o'rnatilgan bo'lishi kerak)",
                  style='Sub.TLabel').pack(side='left', padx=6)

        taminot_frame = ttk.Frame(self)
        taminot_frame.pack(fill='x', padx=20, pady=(4, 6))
        ttk.Button(taminot_frame, text="✏ Kafil/garov ma'lumotini kiritish (tanlangan mijoz)",
                   command=self.open_taminot_dialog).pack(side='left')
        ttk.Button(taminot_frame, text="📊 Ta'minot Excel'ini eksport qilish",
                   command=self.export_taminot).pack(side='left', padx=8)
        ttk.Button(taminot_frame, text="📥 Tahrirlangan Excel'ni yuklash",
                   command=self.import_taminot).pack(side='left', padx=8)

        gen_frame = ttk.Frame(self)
        gen_frame.pack(fill='x', padx=20, pady=(4, 10))
        ttk.Button(gen_frame, text="⚖ Tanlanganlar uchun Davo ariza tayyorlash",
                   style='Accent.TButton', command=self.generate_bulk).pack(side='left')
        ttk.Button(gen_frame, text="✓ Olib kelindi deb belgilash (ish raqami bilan)",
                   command=self.mark_olib_kelindi).pack(side='left', padx=8)

        cols = ('anketa', 'mijoz', 'turi', 'jami_qarz', 'yuborilgan', 'davo_holati', 'ish_raqami', 'taminot')
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=16, selectmode='extended')
        headings = {'anketa': 'Anketa №', 'mijoz': 'Mijoz', 'turi': 'Turi', 'jami_qarz': "Jami qarz",
                    'yuborilgan': 'Xat yuborilgan', 'davo_holati': 'Davo ariza holati',
                    'ish_raqami': 'Ish raqami', 'taminot': "Ta'minot"}
        widths = {'anketa': 85, 'mijoz': 210, 'turi': 75, 'jami_qarz': 110,
                  'yuborilgan': 100, 'davo_holati': 150, 'ish_raqami': 100, 'taminot': 70}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c])
        self.tree.tag_configure('otgan', foreground=ERR)
        self.tree.tag_configure('tayyor', foreground=STAMP)
        self.tree.pack(fill='both', expand=True, padx=20, pady=6)

        self._rows_cache = {}
        self.refresh()

    def _turi_kaliti(self):
        label = self.turi_var.get()
        for k, v in letters.DAVO_ARIZA_NOMLARI.items():
            if v == label:
                return k
        return self._turi_kalitlar[0]

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._rows_cache = {}
        muddat_kun = int(db.get_setting('davo_ariza_muddati_kun', 5))
        xatlar = db.get_xatlar_yuborilgan_davo_kerak()
        for x in xatlar:
            prow = db.get_portfel_by_id(x['portfel_id'])
            if not prow:
                continue
            taminot = db.get_taminot(x['anketa_raqami'])
            taminot_label = "✓" if taminot and taminot.get('taminot_turi') not in (None, '', 'yoq') else "—"
            has_davo = bool(x.get('davo_ariza_fayl_yoli'))
            olib_kelindi = x.get('davo_ariza_holati') == 'olib_kelindi'
            jami = (prow.get('asosiy_qarz') or 0) + (prow.get('foiz_qarz') or 0) + (prow.get('jarima') or 0)
            try:
                yuborilgan = datetime.datetime.fromisoformat(x['yuborilgan_sana']).strftime('%d.%m.%Y')
            except Exception:
                yuborilgan = x.get('yuborilgan_sana', '') or ''

            tag = ''
            if olib_kelindi:
                davo_holati = "✓ Olib kelindi"
                tag = 'tayyor'
            elif has_davo:
                try:
                    davo_dt = datetime.datetime.fromisoformat(x['davo_ariza_sana'])
                    qolgan = muddat_kun - (datetime.datetime.now() - davo_dt).days
                    if qolgan < 0:
                        davo_holati = f"⚠ {abs(qolgan)} kun o'tib ketdi"
                        tag = 'otgan'
                    else:
                        davo_holati = f"Tayyor — {qolgan} kun qoldi"
                except Exception:
                    davo_holati = "Tayyor"
            else:
                davo_holati = "—"

            ish_raqami = x.get('davo_ariza_ish_raqami', '') or ''

            iid = str(x['id'])
            self.tree.insert('', 'end', iid=iid, values=(
                x['anketa_raqami'], x['mijoz_nomi'], x['mijoz_turi'],
                f"{jami:,.0f}".replace(',', ' '), yuborilgan, davo_holati, ish_raqami, taminot_label
            ), tags=(tag,))
            self._rows_cache[iid] = {'xat': x, 'portfel': prow}

    def _selected(self):
        return [self._rows_cache[i] for i in self.tree.selection() if i in self._rows_cache]

    def mark_olib_kelindi(self):
        selected = self._selected()
        if len(selected) != 1:
            messagebox.showinfo("Diqqat", "Aynan bitta mijozni tanlang.")
            return
        item = selected[0]
        xat = item['xat']
        if not xat.get('davo_ariza_fayl_yoli'):
            messagebox.showwarning("Diqqat", "Bu mijoz uchun hali Davo ariza tayyorlanmagan.")
            return
        dlg = OlibKelindiDialog(self, xat['mijoz_nomi'])
        self.wait_window(dlg)
        if dlg.result:
            ish_raqami, sana = dlg.result
            db.mark_davo_ariza_olib_kelindi(xat['id'], ish_raqami, sana)
            messagebox.showinfo("Saqlandi", "Davo ariza 'Olib kelindi' deb belgilandi.")
            self.refresh()

    def open_taminot_dialog(self):
        selected = self._selected()
        if len(selected) != 1:
            messagebox.showinfo("Diqqat", "Kafil/garov kiritish uchun aynan bitta mijozni tanlang.")
            return
        item = selected[0]
        dlg = TaminotDialog(self, item['xat']['anketa_raqami'], item['xat']['mijoz_nomi'])
        self.wait_window(dlg)
        self.refresh()

    def export_taminot(self):
        selected = self._selected()
        if not selected:
            messagebox.showinfo("Diqqat", "Avval ro'yxatdan mijozlarni tanlang.")
            return
        out_path = filedialog.asksaveasfilename(
            title="Excel faylni saqlash", defaultextension=".xlsx",
            initialfile="taminot_royxati.xlsx", filetypes=[("Excel", "*.xlsx")]
        )
        if not out_path:
            return
        rows = []
        for item in selected:
            anketa = item['xat']['anketa_raqami']
            existing = db.get_taminot(anketa) or {}
            row = {'anketa_raqami': anketa, 'mijoz_nomi': item['xat']['mijoz_nomi']}
            row.update(existing)
            rows.append(row)
        try:
            importer.export_taminot_excel(rows, out_path)
            messagebox.showinfo("Tayyor", f"{len(rows)} ta qator eksport qilindi:\n{out_path}")
            webbrowser.open(out_path)
        except Exception as e:
            messagebox.showerror("Xato", str(e))

    def import_taminot(self):
        filepath = filedialog.askopenfilename(
            title="Tahrirlangan ta'minot Excel faylini tanlang",
            filetypes=[("Excel", "*.xlsx *.xls")]
        )
        if not filepath:
            return
        try:
            result = importer.import_taminot_excel(filepath)
            messagebox.showinfo("Tayyor", f"{result['yangilandi']} ta mijoz ta'minot ma'lumoti saqlandi.\n\n"
                                           "Bu ma'lumotlar endi eslab qolindi — keyingi safar ham ishlatiladi.")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Xato", str(e))

    def generate_bulk(self):
        selected = self._selected()
        if not selected:
            messagebox.showinfo("Diqqat", "Iltimos, kamida bitta mijozni tanlang.")
            return

        turi = self._turi_kaliti()
        want_pdf = self.format_var.get().startswith('PDF')
        settings = db.get_all_settings()
        out_dir = bugungi_papka()

        created, errors = [], []
        for item in selected:
            xat = item['xat']
            prow = item['portfel']
            try:
                mijoz_turi, mijoz = resolve_mijoz(prow)
                taminot = db.get_taminot(xat['anketa_raqami'])
                fname = f"Davo_{turi}_{letters.safe_filename(xat['anketa_raqami'])}.docx"
                out_path = os.path.join(out_dir, fname)
                letters.generate_davo_ariza_v2(
                    turi, out_path, prow, mijoz, taminot, settings,
                    xat_sanasi=self._fmt_sana(xat.get('yaratilgan_sana')),
                    xat_turi_nomi=('Талабнома' if xat['xat_turi'] == 'Talabnoma' else 'Огохлантириш хати'),
                )
                if want_pdf:
                    out_path = letters.convert_docx_to_pdf(out_path, delete_docx=True)
                db.mark_davo_ariza_yaratildi(xat['id'], out_path, turi=turi)
                created.append(out_path)
            except Exception as e:
                errors.append(f"{xat.get('anketa_raqami')}: {e}")

        msg = f"{len(created)} ta Davo ariza yaratildi.\nJoylashuv: {out_dir}"
        if errors:
            msg += f"\n\n{len(errors)} ta xatoda:\n" + '\n'.join(errors[:5])
        messagebox.showinfo("Tayyor", msg)
        if created:
            webbrowser.open(out_dir)
        self.refresh()

    @staticmethod
    def _fmt_sana(iso_str):
        try:
            return datetime.datetime.fromisoformat(iso_str).strftime('%d.%m.%Y')
        except Exception:
            return iso_str or ''


class DavoHisobotTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="Davo ariza hisoboti", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(20, 4))
        ttk.Label(self, text="Barcha tayyorlangan Davo arizalar — qachon yaratilgani, qancha vaqtda "
                              "olib kelingani, ish raqami va mijoz qarzdorligi.",
                  style='Sub.TLabel', wraplength=1000).pack(anchor='w', padx=20, pady=(0, 10))

        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=20)
        ttk.Button(toolbar, text="🔄 Yangilash", command=self.refresh).pack(side='left')
        ttk.Button(toolbar, text="📊 Excel'ga eksport qilish", command=self.export_excel).pack(side='left', padx=8)

        cols = ('anketa', 'mijoz', 'turi', 'jami_qarz', 'yaratilgan', 'kutilgan_kun',
                'ish_raqami', 'imzo_sana', 'holati')
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=18)
        headings = {'anketa': 'Anketa №', 'mijoz': 'Mijoz', 'turi': 'Turi', 'jami_qarz': "Qarzdorlik",
                    'yaratilgan': 'Ariza yaratilgan', 'kutilgan_kun': 'Necha kun kutildi',
                    'ish_raqami': 'Ish raqami', 'imzo_sana': 'Olib kelingan sana', 'holati': 'Holati'}
        widths = {'anketa': 85, 'mijoz': 210, 'turi': 75, 'jami_qarz': 110, 'yaratilgan': 110,
                  'kutilgan_kun': 110, 'ish_raqami': 100, 'imzo_sana': 120, 'holati': 130}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c])
        self.tree.tag_configure('otgan', foreground=ERR)
        self.tree.tag_configure('tayyor', foreground=STAMP)
        self.tree.pack(fill='both', expand=True, padx=20, pady=10)

        self._rows_cache = []
        self.refresh()

    def _build_rows(self):
        muddat_kun = int(db.get_setting('davo_ariza_muddati_kun', 5))
        out = []
        for x in db.get_davo_ariza_hisoboti():
            prow = db.get_portfel_by_id(x['portfel_id'])
            jami = 0
            if prow:
                jami = (prow.get('asosiy_qarz') or 0) + (prow.get('foiz_qarz') or 0) + (prow.get('jarima') or 0)

            olib_kelindi = x.get('davo_ariza_holati') == 'olib_kelindi'
            try:
                davo_dt = datetime.datetime.fromisoformat(x['davo_ariza_sana'])
                yaratilgan = davo_dt.strftime('%d.%m.%Y')
            except Exception:
                davo_dt = None
                yaratilgan = x.get('davo_ariza_sana', '') or ''

            if olib_kelindi and davo_dt:
                try:
                    imzo_dt = datetime.datetime.strptime(x['davo_ariza_imzo_sana'], '%d.%m.%Y')
                    kutilgan_kun = max((imzo_dt.date() - davo_dt.date()).days, 0)
                except Exception:
                    kutilgan_kun = ''
                holati = "✓ Olib kelindi"
                tag = 'tayyor'
            elif davo_dt:
                kutilgan_kun = (datetime.datetime.now() - davo_dt).days
                if kutilgan_kun > muddat_kun:
                    holati = f"⚠ Muddati o'tgan ({kutilgan_kun} kun)"
                    tag = 'otgan'
                else:
                    holati = f"Kutilmoqda ({muddat_kun - kutilgan_kun} kun qoldi)"
                    tag = ''
            else:
                kutilgan_kun = ''
                holati = ''
                tag = ''

            out.append({
                'anketa_raqami': x['anketa_raqami'],
                'mijoz_nomi': x['mijoz_nomi'],
                'mijoz_turi': x['mijoz_turi'],
                'jami_qarz': jami,
                'yaratilgan': yaratilgan,
                'kutilgan_kun': kutilgan_kun,
                'ish_raqami': x.get('davo_ariza_ish_raqami', '') or '',
                'imzo_sana': x.get('davo_ariza_imzo_sana', '') or '',
                'holati': holati,
                'tag': tag,
            })
        return out

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._rows_cache = self._build_rows()
        for r in self._rows_cache:
            self.tree.insert('', 'end', values=(
                r['anketa_raqami'], r['mijoz_nomi'], r['mijoz_turi'],
                f"{r['jami_qarz']:,.0f}".replace(',', ' '), r['yaratilgan'],
                r['kutilgan_kun'], r['ish_raqami'], r['imzo_sana'], r['holati']
            ), tags=(r['tag'],))

    def export_excel(self):
        if not self._rows_cache:
            messagebox.showinfo("Diqqat", "Hisobotda ma'lumot yo'q.")
            return
        out_path = filedialog.asksaveasfilename(
            title="Excel faylni saqlash", defaultextension=".xlsx",
            initialfile="davo_ariza_hisoboti.xlsx", filetypes=[("Excel", "*.xlsx")]
        )
        if not out_path:
            return
        import pandas as pd
        cols = ['anketa_raqami', 'mijoz_nomi', 'mijoz_turi', 'jami_qarz', 'yaratilgan',
                'kutilgan_kun', 'ish_raqami', 'imzo_sana', 'holati']
        headers = ['Anketa raqami', 'Mijoz', 'Turi', 'Qarzdorlik', 'Ariza yaratilgan',
                   'Necha kun', 'Ish raqami', 'Olib kelingan sana', 'Holati']
        df = pd.DataFrame([[r.get(c, '') for c in cols] for r in self._rows_cache], columns=headers)
        df.to_excel(out_path, index=False)
        messagebox.showinfo("Tayyor", f"Hisobot eksport qilindi:\n{out_path}")
        webbrowser.open(out_path)


class SozlamalarTab(ttk.Frame):
    FIELDS = [
        ('bank_nomi', 'Bank nomi (to‘liq)'),
        ('bank_qisqa_nomi', 'Bank nomi (qisqa)'),
        ('bank_manzil', 'Bank manzili'),
        ('bank_email', 'Bank email'),
        ('bank_sayt', 'Bank sayti'),
        ('bank_tel', 'Bank markaziy tel'),
        ('bank_mobil_ilova', 'Mobil ilova nomi'),
        ('bank_kodi', 'Bank kodi'),
        ('aloqa_markazi_tel', 'Aloqa markazi tel'),
        ('filial_nomi', 'Filial nomi'),
        ('filial_tel', 'Filial telefon'),
        ('rahbar_ism', 'Filial rahbari F.I.Sh (standart)'),
        ('tolov_muddati_kun', "To'lov uchun beriladigan muddat (bank ish kuni)"),
        ('eslatma_muddati_kun', "Xat yuborish uchun ichki muddat (kun)"),
        ('davo_ariza_muddati_kun', "Xat yuborilgandan keyin Davo ariza tayyorlash muddati (kun)"),
        ('dpd_chegara_kun', "Tahlil uchun DPD chegarasi (kun)"),

        ('viloyat_nomi', 'Viloyat nomi (davo ariza uchun)'),
        ('sud_fuqarolik_nomi', 'Fuqarolik sudi nomi (jismoniy shaxslar uchun)'),
        ('sud_iqtisodiy_nomi', 'Iqtisodiy sudi nomi (yuridik shaxslar uchun)'),
        ('palata_nomi', 'Savdo-Sanoat Palatasi bo\'limi nomi'),
        ('bank_stir', 'Bank STIR'),
        ('bank_hisob_raqami_filial', 'Bank hisob raqami (filial)'),
        ('bank_kodi_filial', 'Bank kodi (filial)'),
        ('bank_hisob_raqami_bosh', 'Bank hisob raqami (bosh ofis)'),
        ('bank_kodi_bosh', 'Bank kodi (bosh ofis)'),
        ('bank_rasmiy_manzil_filial', "Bank rasmiy manzili (filial, sud hujjatlari uchun)"),
        ('pochta_xarajati_standart', "Standart pochta xarajati (so'm)"),
        ('sud_ariza_imzo_ism', 'Davo ariza imzolovchisi F.I.Sh'),
        ('sud_ariza_imzo_lavozimi', 'Davo ariza imzolovchisi lavozimi'),
    ]

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        scroll = ScrollableFrame(self)
        scroll.pack(fill='both', expand=True)
        body = scroll.body

        ttk.Label(body, text="Sozlamalar", style='Header.TLabel').pack(anchor='w', padx=20, pady=(20, 14))

        canvas_frame = ttk.Frame(body)
        canvas_frame.pack(fill='both', expand=True, padx=20)

        self.vars = {}
        current = db.get_all_settings()
        for key, label in self.FIELDS:
            row = ttk.Frame(canvas_frame)
            row.pack(fill='x', pady=5)
            ttk.Label(row, text=label, width=42).pack(side='left')
            var = tk.StringVar(value=current.get(key, ''))
            ttk.Entry(row, textvariable=var, width=50).pack(side='left')
            self.vars[key] = var

        ttk.Button(body, text="💾 Saqlash", style='Accent.TButton',
                   command=self.save).pack(anchor='w', padx=20, pady=16)

        # ---- Xat shabloni ----
        sep = ttk.Frame(body, height=2)
        sep.pack(fill='x', padx=20, pady=(4, 14))
        ttk.Label(body, text="Xat shabloni (Word)", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(0, 4))
        ttk.Label(body, text="Yangi shablon yuklasangiz, hali yuborilmagan ('Tayyor' holatidagi) "
                              "xatlar avtomatik shu yangi shablon bilan qayta tayyorlanadi.",
                  style='Sub.TLabel', wraplength=800, justify='left').pack(
            anchor='w', padx=20, pady=(0, 10))

        tpl_frame = ttk.Frame(body)
        tpl_frame.pack(anchor='w', padx=20, pady=(0, 30))
        ttk.Button(tpl_frame, text="📄 Joriy shablonni ochish",
                   command=self.open_template).pack(side='left')
        ttk.Button(tpl_frame, text="📤 Yangi shablon yuklash (.docx)", style='Accent.TButton',
                   command=self.upload_template).pack(side='left', padx=10)

        # ---- Davo ariza shablonlari ----
        sep2 = ttk.Frame(body, height=2)
        sep2.pack(fill='x', padx=20, pady=(4, 14))
        ttk.Label(body, text="Davo ariza shablonlari (Word)", style='Header.TLabel').pack(
            anchor='w', padx=20, pady=(0, 4))
        ttk.Label(body, text="6 xil Davo ariza turidan birini tanlab, uning shablonini yangilashingiz "
                              "mumkin. Yangilagach, shu turdagi, hali 'Olib kelindi' deb belgilanmagan "
                              "arizalarni yangi shablon bilan qayta tayyorlash so'raladi.",
                  style='Sub.TLabel', wraplength=800, justify='left').pack(
            anchor='w', padx=20, pady=(0, 10))

        davo_tpl_frame = ttk.Frame(body)
        davo_tpl_frame.pack(anchor='w', padx=20, pady=(0, 30))
        ttk.Label(davo_tpl_frame, text="Ariza turi:").pack(side='left')
        self.davo_turi_var = tk.StringVar(value=list(letters.DAVO_ARIZA_NOMLARI.values())[0])
        ttk.Combobox(davo_tpl_frame, textvariable=self.davo_turi_var,
                     values=list(letters.DAVO_ARIZA_NOMLARI.values()),
                     state='readonly', width=44).pack(side='left', padx=8)

        davo_tpl_btns = ttk.Frame(body)
        davo_tpl_btns.pack(anchor='w', padx=20, pady=(0, 30))
        ttk.Button(davo_tpl_btns, text="📄 Joriy shablonni ochish",
                   command=self.open_davo_template).pack(side='left')
        ttk.Button(davo_tpl_btns, text="📤 Yangi shablon yuklash (.docx)", style='Accent.TButton',
                   command=self.upload_davo_template).pack(side='left', padx=10)

    def _davo_turi_kaliti(self):
        label = self.davo_turi_var.get()
        for k, v in letters.DAVO_ARIZA_NOMLARI.items():
            if v == label:
                return k
        return list(letters.DAVO_ARIZA_NOMLARI.keys())[0]

    def open_davo_template(self):
        turi = self._davo_turi_kaliti()
        tpl_path = os.path.join(os.path.dirname(letters.TEMPLATE_PATH), letters.DAVO_ARIZA_TEMPLATES[turi])
        if os.path.exists(tpl_path):
            webbrowser.open(tpl_path)
        else:
            messagebox.showerror("Topilmadi", "Shablon fayli topilmadi.")

    def upload_davo_template(self):
        turi = self._davo_turi_kaliti()
        tpl_path = os.path.join(os.path.dirname(letters.TEMPLATE_PATH), letters.DAVO_ARIZA_TEMPLATES[turi])
        filepath = filedialog.askopenfilename(
            title=f"Yangi shablon faylini tanlang — {self.davo_turi_var.get()}",
            filetypes=[("Word hujjati", "*.docx")]
        )
        if not filepath:
            return
        try:
            import shutil
            os.makedirs(os.path.dirname(tpl_path), exist_ok=True)
            if os.path.exists(tpl_path):
                backup = tpl_path + '.' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.bak'
                shutil.copy2(tpl_path, backup)
            shutil.copy2(filepath, tpl_path)
        except Exception as e:
            messagebox.showerror("Xato", f"Shablonni saqlashda xato: {e}")
            return

        javob = messagebox.askyesno(
            "Qayta tayyorlash",
            f"Shablon yangilandi ({self.davo_turi_var.get()}).\n\n"
            "Shu turdagi, hali 'Olib kelindi' deb belgilanmagan Davo arizalarni "
            "hozir yangi shablon bilan qayta tayyorlaymi?"
        )
        if javob:
            self._regenerate_davo_pending(turi)

    def _regenerate_davo_pending(self, turi):
        pending = db.get_davo_ariza_pending_by_turi(turi)
        settings = db.get_all_settings()
        updated = 0
        errors = []
        for xat in pending:
            try:
                prow = db.get_portfel_by_id(xat['portfel_id'])
                if not prow:
                    continue
                mijoz_turi, mijoz = util.resolve_mijoz(prow)
                taminot = db.get_taminot(xat['anketa_raqami'])
                try:
                    xat_sanasi = datetime.datetime.fromisoformat(xat['yaratilgan_sana']).strftime('%d.%m.%Y')
                except Exception:
                    xat_sanasi = ''
                letters.generate_davo_ariza_v2(
                    turi, xat['davo_ariza_fayl_yoli'], prow, mijoz, taminot, settings,
                    xat_sanasi=xat_sanasi,
                    xat_turi_nomi=('Талабнома' if xat['xat_turi'] == 'Talabnoma' else 'Огохлантириш хати'),
                )
                updated += 1
            except Exception as e:
                errors.append(f"{xat.get('anketa_raqami')}: {e}")

        msg = f"{updated} ta Davo ariza yangi shablon bilan qayta tayyorlandi."
        if errors:
            msg += f"\n\n{len(errors)} ta xatoda:\n" + '\n'.join(errors[:5])
        messagebox.showinfo("Tayyor", msg)

    def save(self):
        for key, var in self.vars.items():
            db.set_setting(key, var.get())
        messagebox.showinfo("Saqlandi", "Sozlamalar saqlandi.")

    def open_template(self):
        if os.path.exists(letters.TEMPLATE_PATH):
            webbrowser.open(letters.TEMPLATE_PATH)
        else:
            messagebox.showerror("Topilmadi", "Shablon fayli topilmadi.")

    def upload_template(self):
        filepath = filedialog.askopenfilename(
            title="Yangi shablon faylini tanlang",
            filetypes=[("Word hujjati", "*.docx")]
        )
        if not filepath:
            return
        try:
            import shutil
            os.makedirs(os.path.dirname(letters.TEMPLATE_PATH), exist_ok=True)
            if os.path.exists(letters.TEMPLATE_PATH):
                backup = letters.TEMPLATE_PATH + '.' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.bak'
                shutil.copy2(letters.TEMPLATE_PATH, backup)
            shutil.copy2(filepath, letters.TEMPLATE_PATH)
        except Exception as e:
            messagebox.showerror("Xato", f"Shablonni saqlashda xato: {e}")
            return

        javob = messagebox.askyesno(
            "Qayta tayyorlash",
            "Shablon yangilandi.\n\nHali yuborilmagan ('Tayyor' holatidagi) xatlarni "
            "yangi shablon bilan hozir qayta tayyorlaymi?"
        )
        if javob:
            self._regenerate_pending()

    def _regenerate_pending(self):
        pending = db.get_xatlar('tayyor')
        settings = db.get_all_settings()
        updated = 0
        errors = []
        for xat in pending:
            try:
                prow = db.get_portfel_by_id(xat['portfel_id'])
                if not prow:
                    continue
                turi, mijoz = util.resolve_mijoz(prow)
                mijoz_ism = mijoz['ism'] if mijoz else prow.get('mijoz_nomi', '')
                mijoz_manzil = mijoz['manzil'] if mijoz else ''
                rahbar_ism = mijoz.get('rahbar_ism') if mijoz else ''
                letters.generate_letter(
                    output_path=xat['fayl_yoli'],
                    xat_turi=xat['xat_turi'],
                    mijoz_ism=mijoz_ism,
                    mijoz_manzil=mijoz_manzil,
                    portfel_row=prow,
                    settings=settings,
                    anketa_raqami=xat['anketa_raqami'],
                    rahbar_ism=rahbar_ism,
                )
                updated += 1
            except Exception as e:
                errors.append(f"{xat.get('anketa_raqami')}: {e}")

        msg = f"{updated} ta xat yangi shablon bilan qayta tayyorlandi."
        if errors:
            msg += f"\n\n{len(errors)} ta xatoda:\n" + '\n'.join(errors[:5])
        messagebox.showinfo("Tayyor", msg)


def main():
    os.makedirs(XATLAR_DIR, exist_ok=True)
    db.init_db()
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
