# Evently (Backend API) — Bajarilgan Ishlar Hisoboti (Report)

> **Loyiha nomi:** Evently — Tadbirlarni boshqarish platformasi (Backend REST API)  
> **Holati:** 100% Yakunlangan (Completed)  
> **Testlar natijasi:** 28 / 28 ta test muvaffaqiyatli o'tgan (100% OK)  
> **Asosiy Postman to'plami:** `postman/evently.postman_collection.json`  

---

## 📋 Mundarija

1. [Umumiy xulosa](#1-umumiy-xulosa)
2. [Loyiha arxitekturasi va texnologiyalar](#2-loyiha-arxitekturasi-va-texnologiyalar)
3. [Foydalanuvchilar va Autentifikatsiya moduli (`apps/users`)](#3-foydalanuvchilar-va-autentifikatsiya-moduli-appsusers)
4. [Tadbirlar va Ro'yxatdan o'tish moduli (`apps/events`)](#4-tadbirlar-va-royxatdan-otish-moduli-appsevents)
5. [Majburiy biznes qoidalari (BR-1 … BR-10) yechimi](#5-majburiy-biznes-qoidalari-br-1--br-10-yechimi)
6. [Telegram Bot va Bildirishnomalar moduli (`apps/notifications` & `bot/`)](#6-telegram-bot-va-bildirishnomalar-moduli-appsnotifications--bot)
7. [Postman Collection va API'ni testlash qoidalari](#7-postman-collection-va-apini-testlash-qoidalari)
8. [Avtomatik testlar hisoboti](#8-avtomatik-testlar-hisoboti)
9. [Boshqaruv buyruqlari (Management Commands)](#9-boshqaruv-buyruqlari-management-commands)
10. [API Hujjatlashtirish (Swagger / OpenAPI)](#10-api-hujjatlashtirish-swagger--openapi)
11. [Docker va Konteynerlashtirish](#11-docker-va-konteynerlashtirish-barcha-qismlarni-bir-vaqtda-ishga-tushirish)

---

## 1. Umumiy xulosa

Evently — o‘quv markazi va konferensiyalar uchun tadbirlarni boshqarish, ishtirokchilarni ro‘yxatga olish, joylar sonini avtomatik nazorat qilish va Telegram orqali xabarnomalar/eslatmalar yuborish imkoniyatiga ega bo'lgan to'liq REST API platformasidir.

Loyiha davomida barcha talablar noldan to'liq bajarildi, biznes qoidalari qat'iy himoyalandi, barcha 28 ta avtomatik testlar 100% muvaffaqiyatli ishga tushirildi va sinovdan o'tkazish uchun yagona asosiy Postman to'plami yaratildi.

---

## 2. Loyiha arxitekturasi va texnologiyalar

### Texnik stek:
- **Dasturlash tili:** Python 3.13
- **Veb freymvork:** Django 6.0
- **API freymvork:** Django REST Framework (DRF) 3.15+
- **Autentifikatsiya:** `djangorestframework-simplejwt` (JWT Access & Refresh tokenlar)
- **Hujjatlashtirish:** `drf-spectacular` (OpenAPI 3.0 / Swagger UI)
- **Ma'lumotlar bazasi:** PostgreSQL (`psycopg[binary]`) hamda tezkor test va lokal ishlab chiqish uchun avtomatik SQLite fallback
- **Telegram Bot:** `aiogram 3.x` (alohida asinxron mikroservis jarayoni)
- **Filtrlash:** `django-filter`
- **Vaqt mintaqasi:** `Asia/Tashkent` (`USE_TZ = True`, barcha amallar `timezone.now()` asosida)

### Loyiha tuzilmasi:
```
evently/
├── apps/
│   ├── users/                 # Custom User, JWT auth, permissions, admin
│   ├── events/                # Event, Registration, business logic services, filters
│   │   └── management/
│   │       └── commands/      # send_event_reminders.py, seed_data.py
│   └── notifications/         # Telegram API endpointlari va xabarnoma servis xizmati
├── bot/                       # aiogram 3.x Telegram bot jarayoni
│   ├── main.py                # Botni ishga tushirish
│   ├── handlers.py            # Buyruqlar (/start, /help)
│   ├── config.py              # Bot sozlamalari
│   └── api_client.py          # Django backend bilan xavfsiz HTTP aloqa
├── config/                    # Django konfiguratsiyasi (settings, urls, asgi, wsgi)
├── postman/                   # Asosiy Postman to'plami
│   └── evently.postman_collection.json
├── INSTRUCTIONS.md            # Bajarilgan ishlar hisoboti (ushbu hujjat)
├── README.md                  # Umumiy loyiha tanishtiruvi va ishga tushirish qo'llanmasi
└── pyproject.toml / uv.lock   # Paketlar boshqaruvi
```

---

## 3. Foydalanuvchilar va Autentifikatsiya moduli (`apps/users`)

### Amalga oshirilgan ishlar:
1. **Custom User modeli (`User`)**:
   - `AbstractUser` asosida qurilgan.
   - `USERNAME_FIELD = "email"` qilib belgilandi (foydalanuvchilar email orqali tizimga kiradi).
   - Maydonlar: `email` (unikal), `first_name`, `last_name`, `phone_number` (+998 formati validatsiyasi), `role` (`admin` yoki `user`).
   - Xavfsizlik: Ro'yxatdan o'tish paytida `role` maydoni `read_only` qilingan (foydalanuvchi o'zini admin qilib ro'yxatdan o'tkaza olmaydi).
2. **Serializerlar**:
   - `RegisterSerializer`: Parol murakkabligini tekshiradi (`validate_password`), telefon raqamini tekshiradi va parolni xavfsiz `set_password` orqali heshlaydi.
   - `UserSerializer`: Foydalanuvchi profil ma'lumotlarini taqdim etadi (`id`, `email`, `first_name`, `last_name`, `phone_number`, `role`, `is_telegram_linked`).
   - `CustomTokenObtainPairSerializer`: JWT token generatsiya qiladi va qo'shimcha tarzda foydalanuvchi ma'lumotlarini qaytaradi.
3. **Huquqlar (Permissions)**:
   - `IsAdmin`: Faqat `role == 'admin'` yoki `is_staff` bo'lgan foydalanuvchilarga ruxsat beradi.
   - `IsAdminOrReadOnly`: Xavfsiz metodlar (GET, HEAD, OPTIONS) uchun hamma foydalanuvchilarga ruxsat, yozish amallariga faqat adminga ruxsat.
4. **Endpointlar**:
   - `POST /api/v1/auth/register/` — Yangi foydalanuvchini ro'yxatdan o'tkazish (201 Created).
   - `POST /api/v1/auth/login/` — Tizimga kirish (JWT Access va Refresh tokenlarni qaytaradi).
   - `POST /api/v1/auth/token/refresh/` — Access tokenni yangilash.
   - `GET /api/v1/auth/me/` — Joriy foydalanuvchi profilini ko'rish.
   - `PATCH /api/v1/auth/me/` — Joriy foydalanuvchi ism, familiya va telefonini yangilash.
5. **Django Admin**:
   - `apps/users/admin.py` orqali Custom User boshqaruvi to'liq integratsiya qilingan.

---

## 4. Tadbirlar va Ro'yxatdan o'tish moduli (`apps/events`)

### Amalga oshirilgan ishlar:
1. **Modellar**:
   - **`Event`**:
     - `title`, `description`, `event_type` (`conference`, `workshop`, `seminar`, `masterclass`), `location`, `start_at`, `end_at`, `capacity`, `status` (`upcoming`, `ongoing`, `finished`, `closed`), `created_by`.
     - Dinamik maydonlar: `registered_count` (faol ro'yxatdan o'tganlar soni), `available_seats` (bo'sh joylar soni), `is_finished` (tadbir o'tib bo'lganligi), `is_registered` (joriy so'rov yuborgan user ro'yxatdan o'tganmi).
   - **`Registration`**:
     - `user`, `event`, `registered_at`, `status` (`active`, `cancelled`), `reminder_sent` (bool).
     - Ma'lumotlar bazasi darajasida cheklov: `UniqueConstraint(fields=['user', 'event'], name='unique_user_event_registration')`.
2. **N+1 muammosini hal qilish va so'rovlarni optimallashtirish**:
   - Tadbirlar ro'yxatini olishda (`EventListCreateView`) har bir tadbir uchun alohida COUNT so'rovlari ketmasligi uchun `annotate(registered_count_annotated=Count('registrations', filter=Q(registrations__status='active')))` qo'llandi.
   - Autentifikatsiyadan o'tgan foydalanuvchilar uchun `is_registered` maydoni `Exists` subquery orqali bitta SQL so'rovda hisoblanadi.
3. **Filtrlash, qidirish va tartiblash**:
   - `django-filter` orqali `EventFilter` sinfi yaratildi:
     - `search` (title, description, location bo'yicha `icontains`),
     - `event_type`, `status`,
     - `start_at__gte` va `start_at__lte`,
     - `ordering` (start_at, capacity, created_at).
4. **Biznes mantiq xizmati (`RegistrationService`)**:
   - Barcha murakkab biznes qoidalari view'dan ajratilib, `apps/events/services.py` dagi `RegistrationService` ga joylashtirildi.
   - Race condition (bir vaqtda bir nechta so'rov kelishi) oldini olish uchun:
     - `transaction.atomic()` bloklari;
     - `Event.objects.select_for_update().get(id=event_id)` qatori orqali qator qulflash (row-level locking) qo'llandi.
5. **Endpointlar**:
   - `GET /api/v1/events/` — Tadbirlar ro'yxati (Pagination 10 ta, filter va search bilan).
   - `POST /api/v1/events/` — Yangi tadbir yaratish (Faqat Admin).
   - `GET /api/v1/events/{id}/` — Tadbir tafsilotlari.
   - `PATCH /api/v1/events/{id}/` — Tadbirni tahrirlash (Faqat Admin).
   - `DELETE /api/v1/events/{id}/` — Tadbirni o'chirish (Faqat Admin, 204 No Content).
   - `POST /api/v1/events/{id}/close/` — Tadbirni muddatidan oldin yopish (Faqat Admin).
   - `GET /api/v1/events/{id}/participants/` — Tadbir qatnashuvchilari ro'yxati (Faqat Admin).
   - `POST /api/v1/events/{id}/register/` — Tadbirga yozilish (Foydalanuvchi).
   - `POST /api/v1/events/{id}/unregister/` — Tadbirdan chiqish / bekor qilish (Foydalanuvchi).
   - `GET /api/v1/me/registrations/` — Foydalanuvchining o'z ro'yxatdan o'tishlari ro'yxati.

---

## 5. Majburiy biznes qoidalari (BR-1 … BR-10) yechimi

| Qoida kodi | Biznes qoidasi mazmuni | Amalga oshirilgan yechim | Qaytariladigan xato kodi |
| :--- | :--- | :--- | :--- |
| **BR-1** | Bir foydalanuvchi bir tadbirga faqat 1 marta yoziladi | DB `UniqueConstraint` + `RegistrationService.register()` da faol ro'yxatdan o'tishni tekshirish | `400 Bad Request` (`code: already_registered`) |
| **BR-2** | Cheklangan joylar nazorati (capacity) | `active_count >= event.capacity` bo'lganda yangi qabul to'xtatiladi | `400 Bad Request` (`code: event_full`) |
| **BR-3** | Tugagan yoki boshlangan tadbirga yozilish taqiqlanadi | `event.start_at <= timezone.now()` yoki `event.is_finished` holati tekshiriladi | `400 Bad Request` (`code: event_started`) |
| **BR-4** | Faqat admin tadbir yarata, tahrirlay va o'chira oladi | `IsAdminOrReadOnly` va `IsAdmin` permissionlari orqali ta'minlangan | `403 Forbidden` (`code: permission_denied`) |
| **BR-5** | Yopilgan tadbirga yozilish taqiqlanadi | `event.status == 'closed'` holati tekshiriladi | `400 Bad Request` (`code: event_closed`) |
| **BR-6** | Boshlangan yoki tugagan tadbirdan chiqib bo'lmaydi | `event.start_at <= timezone.now()` bo'lsa unregister qilish rad etiladi | `400 Bad Request` (`code: event_started`) |
| **BR-7** | `end_at` har doim `start_at` dan keyin bo'lishi shart | `EventSerializer.validate()` da `end_at > start_at` qat'iy tekshiriladi | `400 Bad Request` (`field: end_at`) |
| **BR-8** | O'tgan sanaga tadbir yaratib bo'lmaydi | `EventSerializer.validate()` da `start_at >= timezone.now()` tekshiriladi | `400 Bad Request` (`field: start_at`) |
| **BR-9** | `capacity` ni faol qatnashuvchilar sonidan kamaytirib bo'lmaydi | `EventSerializer.validate()` tahrirlash paytida `new_capacity >= active_count` shartini tekshiradi | `400 Bad Request` (`field: capacity`) |
| **BR-10**| Foydalanuvchi faqat o'z ro'yxatdan o'tishlarini ko'radi | `/api/v1/me/registrations/` da faqat `user=request.user` bo'yicha filter qo'llangan | To'liq ajratilgan |

*Barcha xatoliklar yagona standart formatda qaytadi:*
```json
{
  "detail": "Tushunarli xabar matni",
  "code": "xato_kodi"
}
```

---

## 6. Telegram Bot va Bildirishnomalar moduli (`apps/notifications` & `bot/`)

### Integratsiya mexanizmi:
1. **Xavfsiz hisob bog'lash (Account Linking)**:
   - `POST /api/v1/telegram/link/`: Foydalanuvchiga vaqtinchalik kriptografik `link_token` (UUID4) va `bot_url` (`https://t.me/<bot_username>?start=<token>`) yaratib beradi.
   - Foydalanuvchi botga o'tib `/start <token>` bosadi.
   - Telegram bot backendga `POST /api/v1/telegram/confirm/` so'rovini yuboradi. Ushbu endpoint xavfsizlik uchun `.env` dagi `X-Bot-Secret` maxfiy headeri orqali himoyalangan.
   - Tasdiqlangach, foydalanuvchining `telegram_chat_id` va `telegram_username` saqlanadi hamda `is_telegram_linked = True` bo'ladi.
2. **T1 — Ro'yxatdan o'tish xabarnomasi**:
   - Foydalanuvchi tadbirga muvaffaqiyatli yozilganda, uning o'ziga va barcha tizim adminlariga Telegram xabar yuboriladi.
   - Xabarda tadbir nomi, vaqti, manzili va joriy bo'sh joylar ko'rsatiladi.
   - Telegram API'da uzilish yoki tarmoq xatosi yuz bersa ham, asosiy ro'yxatdan o'tish operatsiyasi buzilmasligi uchun xavfsiz `try/except` xatolik tutuvchi mexanizmi o'rnatilgan.
3. **T2 — Eslatmalar yuborish mexanizmi**:
   - Buyruq: `python manage.py send_event_reminders`
   - Boshlanishiga 24 soatdan kam vaqt qolgan tadbirlarni aniqlaydi.
   - `reminder_sent=False` bo'lgan barcha faol qatnashuvchilarga Telegram orqali eslatma yuboradi va takrorlanmasligi uchun `reminder_sent=True` qiladi.

---

## 7. Postman Collection va API'ni testlash qoidalari

> ⚠️ **Muhim qoida:** Har safar yangi endpoint yaratilganda yoki mavjud endpoint o'zgartirilganda `postman/evently.postman_collection.json` fayli ham darhol mos ravishda yangilanadi. Bu biznes mantiqni to'liq tekshirib boruvchi yagona asosiy test to'plami hisoblanadi.

### Postman to'plami xususiyatlari:
- Fayl joylashuvi: [postman/evently.postman_collection.json](file:///C:/Users/user/NT/evently/postman/evently.postman_collection.json)
- To'plam formati: Postman Collection v2.1.0
- Taqdim etilgan modullar:
  1. `1. Authentication & Profil` (Register, Login user, Login admin, Refresh, Me GET, Me PATCH)
  2. `2. Events (Tadbirlar) - Admin Boshqaruvi` (Create, Patch, Participants, Close, Delete)
  3. `3. Events (Tadbirlar) - Ommaviy ko'rish & Qidiruv` (List, Filter, Detail)
  4. `4. Registration (Ro'yxatdan o'tish) & Biznes Qoidalar` (Register, Duplicate check BR-1, My Registrations, Unregister)
  5. `5. Telegram Integratsiyasi` (Link generate, Bot confirm)
  6. `6. Swagger & Hujjatlashtirish` (OpenAPI Schema, Swagger UI)

### Avtomatlashtirilgan o'zgaruvchilar (Variables) va Test Scriptlar:
To'plam o'z ichiga avtomatik Postman skriptlarini oladi:
- `Login (Oddiy foydalanuvchi)` so'rovi muvaffaqiyatli o'tgach, javobdagi `access` va `refresh` avtomatik tarzda `{{accessToken}}` va `{{refreshToken}}` to'plam o'zgaruvchilariga yoziladi.
- `Login (Admin)` so'rovi javobdagi tokenni avtomatik tarzda `{{adminAccessToken}}` ga saqlaydi.
- `Tadbir yaratish` so'rovi yangi yaratilgan tadbir ID sini `{{eventId}}` ga saqlaydi.
- `Telegram link` so'rovi generatsiya qilingan tokenni `{{telegramLinkToken}}` ga joylaydi.
- Har bir so'rovda status kodi va biznes natijasi uchun `pm.test(...)` tekshiruvlari kiritilgan.

---

## 8. Avtomatik testlar hisoboti

Barcha biznes mantiq va xavfsizlik qoidalari uchun avtomatik testlar yozildi va muvaffaqiyatli topshirildi:

```bash
python manage.py test
```

### Test natijasi:
```text
Creating test database for alias 'default'...
............................
----------------------------------------------------------------------
Ran 28 tests in 0.670s

OK
Destroying test database for alias 'default'...
```

### Qamrab olingan test to'plamlari:
1. **`apps/users/tests/` (Autentifikatsiya testlari)**:
   - Ro'yxatdan o'tish validatsiyalari (email mavjudligi, noto'g'ri parol formati);
   - Role maydonini foydalanuvchi o'zgartira olmasligi (`role='admin'` deb yuborilsa ham `user` bo'lib saqlanishi);
   - Login, token olish va token yangilash (Refresh);
   - Profilni ko'rish va yangilash huquqlari.
2. **`apps/events/tests/` (Tadbirlar va Ro'yxatdan o'tish testlari)**:
   - Tadbirlarni yaratish, tahrirlash, o'chirish va yopishda admin huquqlari;
   - O'tgan sanaga tadbir yaratib bo'lmasligi (BR-8);
   - `end_at` ning `start_at` dan oldin bo'la olmasligi (BR-7);
   - Tadbirga muvaffaqiyatli ro'yxatdan o'tish va bo'sh joylar sonining kamayishi;
   - Bir tadbirga ikkinchi marta yozilishning taqiqlanishi (BR-1);
   - To'lgan tadbirga yozilishning taqiqlanishi (BR-2);
   - Boshlangan tadbirga yozilish yoki undan chiqishning taqiqlanishi (BR-3, BR-6);
   - Yopilgan tadbirga yozilishning taqiqlanishi (BR-5);
   - `capacity` ni faol qatnashuvchilar sonidan kamaytirib bo'lmasligi (BR-9);
   - Foydalanuvchi faqat o'z ro'yxatdan o'tishlarini ko'rishi (BR-10).
3. **`apps/notifications/tests/` (Telegram xabarnomalar testlari)**:
   - Foydalanuvchi uchun unikal Telegram bog'lash tokeni generatsiyasi;
   - Bot tomonidan `X-Bot-Secret` maxfiy kaliti orqali chat_id bog'lanishi;
   - Noto'g'ri maxfiy kalitda kirishning rad etilishi (`403 Forbidden`);
   - `send_event_reminders` management komandasi orqali 24 soat ichidagi tadbirlarga eslatma yuborilishi va takroriy xabar yuborilmasligi kafolati.

---

## 9. Boshqaruv buyruqlari (Management Commands)

1. **Namunaviy test ma'lumotlarini bazaga kiritish**:
   ```bash
   python manage.py seed_data
   ```
   *Vazifasi: Tizimga 2 ta admin, 10 ta oddiy foydalanuvchi, 15 ta turli xil holatdagi tadbirlar va ro'yxatdan o'tishlarni avtomatik joylaydi.*

2. **Tadbirlar bo'yicha Telegram eslatmalarini yuborish**:
   ```bash
   python manage.py send_event_reminders
   ```
   *Vazifasi: Boshlanishiga 24 soat qolgan barcha faol tadbirlar qatnashuvchilariga xabarnoma yuboradi va statusini yangilaydi.*

3. **Eslatmalarni davriy ravishda tekshiruvchi fon xizmati (Worker)**:
   ```bash
   python manage.py run_reminder_worker --interval 60
   ```
   *Vazifasi: Belgilangan vaqt oralig'ida (masalan, har 60 soniyada) avtomatik ravishda eslatmalar yuborilishini tekshiradi va Docker konteynerida fon xizmati sifatida uzluksiz ishlaydi.*

---

## 10. API Hujjatlashtirish (Swagger / OpenAPI)

API to'liq interaktiv Swagger UI va OpenAPI 3.0 sxemasi orqali hujjatlashtirilgan:
- **Swagger interaktiv interfeysi:** `http://localhost:8000/api/docs/`
- **OpenAPI Schema (JSON formatida):** `http://localhost:8000/api/schema/`

---

## 11. Docker va Konteynerlashtirish (Barcha qismlarni bir vaqtda ishga tushirish)

Loyiha to'liq Docker muhitiga o'tkazildi:
- **`Dockerfile`**: `python:3.13-slim` bazasida optimallashtirilgan, Gunicorn WSGI serveri va `entrypoint.sh` orqali ishlaydi.
- **`entrypoint.sh`**: PostgreSQL bazasi to'liq tayyor bo'lishini kutadi, migratsiyalarni avtomatik o'tkazadi va statik fayllarni yig'adi.
- **`docker-compose.yml`**: Bitta `docker compose up --build` buyrug'i orqali tizimning barcha 4 ta qismi avtomatik parallel ishga tushadi:
  1. `db`: PostgreSQL 16 ma'lumotlar bazasi (avtomatik sog'lomlik tekshiruvi / healthcheck bilan);
  2. `web`: Django REST API (Gunicorn, port 8000);
  3. `bot`: aiogram 3.x Telegram bot servisi;
  4. `reminder-worker`: Eslatmalarni muntazam tekshiruvchi davriy fon xizmati.
