# Qarz Nazorat va Talabnoma Tizimi

Bitta kompyuterda, internetsiz (oflayn) ishlaydigan dastur. Portfelni tahlil
qiladi, 45 kundan ko'p muddati o'tgan mijozlarni ajratadi va ularga
Ogohlantirish xati (jismoniy shaxs) / Talabnoma (yuridik shaxs) tayyorlaydi.

## 1. Kompyuterda ishga tushirish (test uchun, .exe siz)

Kompyuteringizda **Python 3.10+** o'rnatilgan bo'lishi kerak
(https://python.org — o'rnatishda "Add Python to PATH" belgisini bosing).

```
pip install -r requirements.txt
python main.py
```

Dastur ochiladi. Birinchi marta ishga tushganda `qarz_nazorat.db` fayli
avtomatik yaratiladi — bu sizning bazangiz, uni o'chirmang.

## 2. .EXE qilib yig'ish (Windows'da)

1. Ushbu papkani (`qarz_nazorat`) Windows kompyuteringizga ko'chiring.
2. Python o'rnatilganini tekshiring (`cmd` da `python --version`).
3. Papka ichida `build_exe.bat` faylini ikki marta bosing.
4. Bir necha daqiqadan so'ng `dist\QarzNazorat.exe` fayli tayyor bo'ladi.
5. Shu `.exe` faylni istalgan joyga (masalan Desktop'ga) ko'chirib, ishlatishingiz mumkin — endi Python ham, internet ham kerak emas.

**Muhim:** `.exe` ishga tushganda, u joylashgan papkada `qarz_nazorat.db`
va `yaratilgan_xatlar` papkasi avtomatik hosil bo'ladi — shu papkani
zaxira nusxalashni unutmang.

## 3. Ishlatish tartibi

1. **Portfel** bo'limi — IFRS portfel hisobotini (`.xlsb`) yuklang.
2. **Mijozlar bazasi** — ikkita usul bor:
   - **Tavsiya etiladi:** bank tizimidan olingan xom matn (`.txt` yoki uni
     ichiga olgan `.zip`) faylni to'g'ridan-to'g'ri yuklang. Bu fayl Excel
     orqali o'tmagani uchun ma'lumot buzilmaydi, ustunlarni moslashtirish
     shart emas — dastur o'zi jismoniy/yuridik shaxsni aniqlaydi va
     ID_CLIENT/STIR/PINFL orqali avtomatik portfel bilan bog'laydi.
   - Muqobil: Excel (.xlsx) fayl — ustunlarni qo'lda moslashtirasiz.
3. **Tahlil / Talabnoma** — "Tahlil qilish" tugmasi 45+ kun (sozlamalarda
   o'zgartirish mumkin) muddati o'tgan mijozlarni ro'yxat qilib beradi.
   Ro'yxatda, standart holatda, faqat hali xati yaratilmagan yoki
   muddati o'tib ketgan mijozlar ko'rinadi — xat yaratilganlar avtomatik
   chiqib ketadi (checkbox orqali barchasini ko'rish mumkin).

   **Paketlarga bo'lib ishlash** (masalan 150 tani 30 tadan 5 paket qilib):
   - "Paket hajmi" (10/30/50/100/Barchasi) tanlang
   - "① Birinchi paketni belgilash" — ro'yxatdagi birinchi N tani avtomatik
     belgilaydi (yoki Ctrl/Shift bosib o'zingiz ham tanlashingiz mumkin)

   **Manzilni tekshirish/to'g'irlash** (xat yaratishdan oldin):
   - "📊 Excel'ga eksport qilish" — tanlangan mijozlar ro'yxatini (Ism,
     Manzil, Telefon va h.k.) Excel qilib beradi
   - Excel'da kerakli manzil/telefonni to'g'irlaysiz
   - "📥 Tahrirlangan Excel'ni yuklash" — tuzatilgan faylni qaytarib
     yuklaysiz, dastur o'zgargan manzilni **mijozlar bazasiga saqlab qoladi**
     (keyingi safar ham eslab qoladi)
   - So'ng "✉ Tanlanganlar uchun xat yaratish (ommaviy)" bosasiz — endi
     to'g'irlangan manzil bilan tayyorlanadi

   Yoki anketa raqami bo'yicha qidirib, bitta mijozga alohida xat
   yaratishingiz mumkin. Xatlar `yaratilgan_xatlar` papkasiga saqlanadi.

   **Fayl formati (Word / PDF):** shu bo'limda "Xat fayl formati" ochiladigan
   ro'yxatidan tanlaysiz. PDF formatini ishlatish uchun kompyuterda
   **Microsoft Word o'rnatilgan bo'lishi shart** (PDF Word orqali generatsiya
   qilinadi). Agar Word bo'lmasa, "Word (.docx)" ni tanlang.
4. **Xatlar holati** — yaratilgan barcha xatlar va ularning holati
   (Tayyor / Yuborildi / Muddati o'tgan) shu yerda ko'rinadi. Xat jo'natilgach
   "Yuborildi deb belgilash" tugmasini bosing. Agar xodim **3 kun** ichida
   belgilamasa, dastur ochilganda avtomatik ogohlantirish chiqadi.

5. **Davo ariza** — xati "Yuborildi" deb belgilangan barcha mijozlar shu
   bo'limda avtomatik ro'yxatga tushadi (agar xat hali yuborilmagan bo'lsa,
   Davo ariza tayyorlash imkonsiz — dastur buni aniq xabar bilan bildiradi
   va avval xatni yuborishni so'raydi).

   - **Ariza turi** tanlaysiz — 6 xil variant mavjud (real namunalaringiz
     asosida tayyorlangan):
     1. Jismoniy shaxs — oddiy (kafilsiz)
     2. Jismoniy shaxs — kafil bilan
     3. Yuridik/Ф.Х — oddiy (kafilsiz, Savdo-Sanoat Palatasiga)
     4. Yuridik shaxs — kafil bilan (foiz-penya undirish)
     5. Yuridik shaxs — kafil + garov mulkiga qaratish
     6. Shartnomani bekor qilish (muddatidan oldin undirish)
   - **Kafil/garov ma'lumotlari** (2, 4, 5, 6-turlar uchun kerak) — chunki
     bu ma'lumot portfelda yo'q, xodim **"✏ Kafil/garov ma'lumotini
     kiritish"** oynasi orqali qo'lda kiritadi (kafil F.I.Sh, manzil,
     PINFL, passport, garov mulki tavsifi va bahosi). Bir marta kiritilgan
     ma'lumot **anketa raqami bo'yicha saqlanib qoladi** — keyingi safar
     qayta kiritish shart emas.
   - **Excel orqali ommaviy tekshirish**: "📊 Ta'minot Excel'ini eksport
     qilish" — tanlangan mijozlar ro'yxatini (kafil/garov ustunlari bilan)
     Excel qilib beradi, siz to'ldirib/tuzatib, "📥 Tahrirlangan Excel'ni
     yuklash" orqali qaytarasiz — **saqlanib qoladi va eslab qolinadi**.
   - **Paket yoki bittalab**: Ctrl/Shift bilan bir nechta mijozni tanlab
     "⚖ Tanlanganlar uchun Davo ariza tayyorlash" bosasiz — barchasi bir
     vaqtda, tanlangan turdagi shablon bilan tayyorlanadi. Yoki bitta
     mijozni tanlab, alohida ham tayyorlash mumkin.
   - **Format**: Word yoki PDF — xuddi oddiy xatlardagi kabi tanlanadi.

   **"Olib kelindi" tasdiqlash va muddat kuzatuvi:** Davo ariza tayyorlab,
   Palata/sudga topshirilgandan (imzodan chiqarilgandan) keyin, uni
   **5 kun ichida qaytarib olib kelish** kerak. Olib kelingach, **"✓ Olib
   kelindi deb belgilash"** tugmasini bosing — shunda **ish raqami** va
   **imzodan chiqqan sana**ni kiritish so'raladi. Agar 5 kun ichida "Olib
   kelindi" deb belgilanmasa, ro'yxatda qator **qizil rangda** va "⚠ N kun
   o'tib ketdi" deb ko'rinadi, dastur ochilganda avtomatik ogohlantirish
   chiqadi, Bosh sahifada ham alohida ko'rsatkich sifatida ko'rinadi.

   ⚠️ **Muhim:** Davo ariza matnlari sizning **haqiqiy namunalaringiz**
   asosida tayyorlangan (aynan matni saqlab qolingan, faqat o'zgaruvchi
   qismlar — ism, sana, summa — avtomatlashtirilgan). Shunga qaramay,
   ayniqsa **5 va 6-turlar** (garov mulki, shartnomani bekor qilish)
   har bir holat uchun individual bo'lgani sabab, yaratilgan hujjatni
   sudga/Palataga yuborishdan oldin **yuridik bo'lim albatta tekshirib
   chiqishi tavsiya etiladi**.

6. **Davo ariza hisoboti** — barcha tayyorlangan Davo arizalar bo'yicha
   umumiy jadval: mijoz, qarzdorlik summasi, ariza qachon tayyorlangani,
   necha kun kutilgani (yoki hali kutilayotgani), ish raqami, olib kelingan
   sana va joriy holati. "📊 Excel'ga eksport qilish" orqali bu hisobotni
   Excel faylga ham olishingiz mumkin.

7. **Sozlamalar** — bank nomi, filial nomi, telefon, 45 kunlik chegara,
   3 kunlik xat yuborish muddati, 5 kunlik Davo ariza "olib kelish" muddati,
   sud nomlari, Savdo-Sanoat Palatasi rekvizitlari va davo ariza
   imzolovchisi shu yerdan o'zgartiriladi.

   **Shablonni yangilash** — xat shabloni (Word) o'zgarsa, shu yerdan yangi
   `.docx` faylni yuklaysiz. Yuklagach, hali yuborilmagan ("Tayyor"
   holatidagi) barcha xatlar avtomatik ravishda yangi shablon bilan
   qayta tayyorlanadi (savol chiqadi — "Ha" desangiz).

   **Davo ariza shablonlarini yangilash** — shu bo'limning pastida, 6 xil
   Davo ariza turidan birini tanlab, uning shablonini alohida yangilashingiz
   mumkin ("Davo ariza shablonlari" qismi). Yangilagach, shu turdagi, hali
   "Olib kelindi" deb belgilanmagan arizalarni yangi shablon bilan qayta
   tayyorlash so'raladi (savol chiqadi — "Ha" desangiz).

## 3.1. Fayllar qanday saqlanadi

Yaratilgan barcha xatlar va Davo arizalar `yaratilgan_xatlar` papkasi ichida,
**tayyorlangan kuniga mos sana bo'yicha alohida papkalarga** saqlanadi.
Masalan, 14.08.2026 kuni tayyorlangan xatlar `yaratilgan_xatlar/14.08.2026/`
papkasiga, 15.08.2026 kuni tayyorlanganlari esa `yaratilgan_xatlar/15.08.2026/`
papkasiga tushadi. Bu kunlar bo'yicha qidirish/hisobotni osonlashtiradi.

## 4. Hozircha ochiq qolgan masalalar

- **Mijozlar bazasi**: endi bank tizimidan olingan xom matn (`.txt`/`.zip`)
  fayldan to'g'ridan-to'g'ri, aniq import qilinadi (`CODE_SUBJECT` ustuni
  orqali jismoniy/yuridik avtomatik aniqlanadi; ID_CLIENT, STIR va PINFL —
  uchalasi bo'yicha ham saqlanadi, shunda portfel bilan bog'lanish ehtimoli
  maksimal bo'ladi). Test qilingan real ma'lumotda 45+ kun muddati o'tgan
  mijozlarning ~16% i uchun real manzil/telefon topildi — bu ko'rsatkich
  mijozlar bazasi qanchalik to'liq bo'lishiga bog'liq (baza qanchalik keng
  bo'lsa, moslik foizi shunchalik oshadi).
- **Talabnoma matni**: hozircha Ogohlantirish xatiga o'xshab, faqat sarlavha
  "ТАЛАБНОМА" deb almashtirilgan. Matn boshqacha bo'lishi kerak bo'lsa,
  ayting — alohida shablon tuzib beraman.

## 5. Fayl tuzilishi

```
qarz_nazorat/
├── main.py              # Dastur oynasi (GUI)
├── database.py          # SQLite baza
├── importer.py          # Excel/XLSB import
├── letters.py           # Word xat generatsiyasi
├── templates/
│   └── xat_shablon.docx # Xat shabloni
├── requirements.txt
├── build_exe.bat        # .exe yig'ish uchun
└── README.md
```
