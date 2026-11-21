# evently-api — Tadbirlarni Boshqarish Platformasi (Backend API)

> **Backend Practice Program · 1-loyiha**  
> REST API (Django + DRF) + JWT Auth + PostgreSQL/SQLite + Swagger + Telegram Bot (aiogram) + Avtomatik Testlar (28 ta test — 100% OK).

---

## 📌 Loyiha haqida

**Evently** — o‘quv markazlari, konferensiyalar va treninglar uchun tadbirlarni boshqarish, ishtirokchilarni ro‘yxatga olish, joylarni avtomatik nazorat qilish va Telegram orqali xabarnoma/eslatma yuborish imkoniyatini beruvchi backend REST API platformasi.

Loyihaning to'liq bajarilgan ishlar hisoboti: [INSTRUCTIONS.md](file:///C:/Users/user/NT/evently/INSTRUCTIONS.md)  
Biznes mantiqni tekshirish uchun asosiy Postman to'plami: [postman/evently.postman_collection.json](file:///C:/Users/user/NT/evently/postman/evently.postman_collection.json)

---

## 📊 Loyiha Holati va Progress Checklist (Check bo'ldimi?)

### 1. Arxitektura va Muhit
- [x] Python 3.13 + uv virtual muhit va paketlar boshqaruvi
- [x] Django 6.x + Django REST Framework loyiha tuzilmasi (`config/`, `apps/`, `bot/`)
- [x] 12-factor `.env` va `.env.example` sozlamalari
- [x] PostgreSQL drayveri (`psycopg[binary]`) va lokal qulaylik uchun SQLite fallback sozlamasi
- [x] CORS konfiguratsiyasi (`django-cors-headers`)
- [x] Timezone: `Asia/Tashkent` va vaqt bilan ishlashda `timezone.now()`

### 2. Authentication va Foydalanuvchilar (`apps/users`)
- [x] Custom User modeli (`AbstractUser` asosida, `USERNAME_FIELD = "email"`)
- [x] `role` maydoni (`admin` / `user`), xavfsizlik uchun API orqali rol oshirish cheklangan (`read_only`)
- [x] `POST /api/v1/auth/register/` — Ro'yxatdan o'tish (parol validatsiyasi, telefon raqami formati)
- [x] `POST /api/v1/auth/login/` — JWT access va refresh token olish (SimpleJWT)
- [x] `POST /api/v1/auth/token/refresh/` — Access tokenni yangilash
- [x] `GET /api/v1/auth/me/` va `PATCH /api/v1/auth/me/` — Profil ma'lumotlarini olish va yangilash
- [x] Django Admin panelda Custom UserAdmin integratsiyasi

### 3. Tadbirlar tizimi (`apps/events`)
- [x] `Event` modeli (`title`, `description`, `event_type`, `location`, `start_at`, `end_at`, `capacity`, `status`, `created_by`)
- [x] Permissionlar (`IsAdmin`, `IsAdminOrReadOnly`) — tadbir CRUD faqat admin uchun
- [x] `GET /api/v1/events/` — Tadbirlar ro'yxati (Pagination 10 ta, `django-filter`, search, ordering)
- [x] N+1 muammosi oldi olingan: `annotate(Count('registrations', filter=Q(status='active')))` va `Exists` orqali `is_registered`
- [x] Dinamik maydonlar: `registered_count`, `available_seats`, `is_finished`, `is_registered`
- [x] `GET /api/v1/events/{id}/` — Tadbir haqida batafsil ma'lumot
- [x] `POST /api/v1/events/` — Yangi tadbir yaratish (Admin)
- [x] `PATCH /api/v1/events/{id}/` — Tadbirni tahrirlash (Admin)
- [x] `DELETE /api/v1/events/{id}/` — Tadbirni o'chirish (Admin)
- [x] `POST /api/v1/events/{id}/close/` — Tadbirni yopish (Admin)
- [x] `GET /api/v1/events/{id}/participants/` — Qatnashuvchilar ro'yxati (Admin)

### 4. Ro'yxatdan o'tish va Biznes Qoidalar (BR-1 … BR-10)
- [x] `Registration` modeli (`UniqueConstraint(user, event)`, `status=active|cancelled`, `reminder_sent`)
- [x] **BR-1**: Bir foydalanuvchi bir tadbirga faqat 1 marta yoziladi (DB constraint + xizmat darajasida tekshiruv)
- [x] **BR-2**: Cheklangan joylar nazorati (`capacity` limit, to'lganda `event_full` xatosi)
- [x] **BR-3**: Tugagan yoki boshlangan tadbirga yozilish taqiqlangan (`event_started`)
- [x] **BR-4**: Faqat admin tadbir yarata, tahrirlay va o'chira oladi
- [x] **BR-5**: Yopilgan tadbirga yozilish taqiqlangan (`event_closed`)
- [x] **BR-6**: Tadbir boshlangandan keyin undan chiqib bo'lmaydi (`start_at <= now` -> rad etiladi)
- [x] **BR-7**: `end_at` har doim `start_at` dan keyin bo'lishi shart
- [x] **BR-8**: O'tgan sanaga tadbir yaratib bo'lmaydi
- [x] **BR-9**: `capacity` ni faol qatnashuvchilar sonidan kamaytirib bo'lmaydi
- [x] **BR-10**: Foydalanuvchi faqat o'zining ro'yxatdan o'tishlarini ko'radi (`/api/v1/me/registrations/`)
- [x] Poyga holatiga (race condition) qarshi `transaction.atomic()` va `select_for_update()` qo'llangan
- [x] Yagona xato formati: `{"detail": "...", "code": "..."}`

### 5. Telegram Integratsiyasi va Bot (`apps/notifications` & `bot/`)
- [x] `POST /api/v1/telegram/link/` — Foydalanuvchiga unikal token va t.me bot havolasi generatsiyasi
- [x] `POST /api/v1/telegram/confirm/` — Bot tomonidan `X-Bot-Secret` orqali chat_id ni tasdiqlash
- [x] `bot/` alohida jarayoni (aiogram 3.x asosida `/start <token>`, `/start`, `/help`)
- [x] **T1**: Tadbirga yozilganda foydalanuvchiga va barcha adminlarga Telegram xabarnoma yuborish
- [x] **T2**: Eslatma yuborish mexanizmi: `python manage.py send_event_reminders`
- [x] Eslatma takrorlanmasligi kafolati (`reminder_sent=True`)
- [x] Telegram API uzilishi ro'yxatdan o'tish so'rovini yiqitmaydi (`try/except` himoyasi)

### 6. Testlash va Hujjatlashtirish
- [x] OpenAPI 3.0 / Swagger UI (`drf-spectacular` orqali `/api/docs/` va `/api/schema/`)
- [x] Avtomatik testlar (28 ta testning barchasi muvaffaqiyatli o'tgan, tezkor password hasher optimizatsiyasi)
- [x] Test ma'lumotlarini to'ldirish uchun `python manage.py seed_data` buyrug'i

---

## 🛠 Texnologiyalar

| Texnologiya | Vazifasi |
| --- | --- |
| **Python 3.13** | Asosiy dasturlash tili |
| **Django 6.x** | Veb-freymvork |
| **Django REST Framework** | REST API vositasi |
| **PostgreSQL / SQLite** | Ma'lumotlar bazasi (`psycopg[binary]`) |
| **SimpleJWT** | JWT autentifikatsiya |
| **drf-spectacular** | OpenAPI / Swagger hujjatlari |
| **aiogram 3.x** | Telegram Bot |
| **httpx** | Asinxron HTTP so'rovlar |
| **Docker & Docker Compose** | Konteynerlashtirish va barcha qismlarni parallel ishga tushirish |
| **Gunicorn** | Ishlab chiqarish darajasidagi WSGI server |

---

## 🐳 Docker orqali ishga tushirish (Barcha qismlar bir vaqtda ishlaydi)

Loyiha to'liq konteynerlashtirilgan bo'lib, bitta buyruq orqali tizimning barcha 4 ta komponenti bir vaqtda ishga tushadi:

```bash
# 1. Muhit faylini yaratish (zarur bo'lsa sozlang)
cp .env.example .env

# 2. Docker orqali barcha qismlarni ko'tarish
docker compose up --build
```

### Ishga tushadigan komponentlar:
1. **`evently_db`** — PostgreSQL 16 ma'lumotlar bazasi (avtomatik healthcheck bilan).
2. **`evently_web`** — Django REST API (Gunicorn WSGI server, migratsiyalar avtomatik qo'llaniladi, port: `8000`).
3. **`evently_bot`** — aiogram 3.x Telegram bot servisi (backend bilan ichki tarmoq orqali bog'langan).
4. **`evently_reminder_worker`** — Tadbirlar eslatmalarini muntazam (har 60s) fonda tekshiruvchi avtomatik servis.

---

## 🚀 Lokal muhitda qo'lda ishga tushirish

### 1. Repozitoriyni klonlash va virtual muhitni faollashtirish
```bash
git clone https://github.com/<username>/evently.git
cd evently

# uv orqali (tavsiya qilinadi):
uv sync

# Yoki standart venv orqali:
python -m venv .venv
.venv\Scripts\activate   # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Muhit o'zgaruvchilari (.env)
```bash
cp .env.example .env
```
`.env` faylida o'zingizning ma'lumotlaringizni sozlang (PostgreSQL yoki `USE_SQLITE=True`, bot token va h.k.).

### 3. Migratsiyalar va Admin
```bash
python manage.py migrate
# Standart admin ma'lumotlari (.env faylida ham saqlangan):
# Email: admin@example.com | Parol: Admin123!
```

### 4. Namunaviy ma'lumotlar yaratish (Ixtiyoriy)
```bash
python manage.py seed_data
```
*(2 ta admin, 10 ta user, 15 ta tadbir yaratadi)*

### 5. Backend Serverni ishga tushirish
```bash
python manage.py runserver
```

- **Swagger UI**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **OpenAPI Schema**: [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)
- **Django Admin**: [http://localhost:8000/admin/](http://localhost:8000/admin/)

### 6. Telegram Botni ishga tushirish (alohida terminalda)
```bash
python -m bot.main
```

### 7. Eslatmalarni yuborish buyrug'i
```bash
python manage.py send_event_reminders
```

---

## 🧪 Avtomatik Testlarni Ishga Tushirish

Barcha 28 ta majburiy test holatlarini tekshirish:
```bash
python manage.py test
```
Natija:
```
Ran 28 tests in 0.87s
OK
```

---

## 📁 Loyiha Strukturasi

```
evently/
├── apps/
│   ├── users/                 # Custom User, JWT auth, permissions
│   ├── events/                # Event, Registration, services, filters
│   │   └── management/
│   │       └── commands/      # send_event_reminders, seed_data
│   └── notifications/         # Telegram API integratsiyasi
├── bot/                       # aiogram bot (alohida jarayon)
├── config/                    # Django loyiha sozlamalari (settings, urls)
├── .env.example               # Muhit o'zgaruvchilari namunasi
├── INSTRUCTIONS.md            # Asl topshiriq qo'llanmasi
├── README.md                  # Loyiha hujjati va checklist
└── requirements.txt           # Loyiha qaramliklari
```
