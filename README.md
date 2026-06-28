# Pure Nest API

Lightweight Django REST Framework API with mobile-number login and email OTP verification.

## Quick Setup

1. Create and activate a Python virtualenv, then install:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configure `.env` (DB, email settings). Example for Gmail SMTP:

```env
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
```

3. Run database migrations and start the server:

```bash
python manage.py migrate
python manage.py runserver
```

This project uses DRF Token Authentication. Run `python manage.py migrate authtoken` if needed.

## Auth & Endpoints

- Authentication: `Authorization: Token <token>` for protected endpoints.
- All auth-related endpoints are implemented as individual `ModelViewSet` POST endpoints (no `@action`).

Base API path example: `http://127.0.0.1:8000/api/`

Endpoints:

- `POST /api/users/signup/` — Register (sends verification token)
- `POST /api/users/verify-otp/` — Verify OTP (email/mobile)
- `POST /api/users/login/` — Login (returns token)
- `POST /api/users/send-otp/` — Resend verification OTP
- `POST /api/users/forgot-password/` — Send password reset OTP
- `POST /api/users/reset-password/` — Reset password using OTP
- `GET/POST/PUT/PATCH/DELETE /api/users/` — Standard user CRUD (token required)
- `GET /api/otp-verifications/` — OTP records (token required)

## Short examples

Signup (curl):

```bash
curl -X POST http://127.0.0.1:8000/api/users/signup/ \
  -H "Content-Type: application/json" \
  -d '{"first_name":"John","last_name":"Doe","email":"john@example.com","mobile_number":"+123456789","password":"secret123"}'
```

Login (curl):

```bash
curl -X POST http://127.0.0.1:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"mobile_number":"+123456789","password":"secret123"}'
```

Protected request example:

```
Authorization: Token <your_token_here>
```

If you'd like, I can also run the test suite or start the server in this workspace to verify the endpoints.

Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Email is not verified. Please verify your email token before logging in.` | Login before verifying | Complete Step 2 first |
| `Invalid or expired verification token.` | Wrong token or token expired (10 min) | Use `send-otp` or `forgot-password` to get a new token |
| `A user with this mobile number already exists.` | Duplicate signup | Use a different mobile number or login instead |
| `A user with this email already exists.` | Duplicate email | Use a different email or login instead |
| `Failed to send verification email` | Gmail SMTP not configured | Check `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in `.env` |
| `Invalid mobile number or password.` | Wrong credentials | Check mobile number and password |

---

## Quick Reference — All curl Commands

```bash
# 1. Signup
curl -X POST http://127.0.0.1:8000/api/users/signup/ \
  -H "Content-Type: application/json" \
  -d '{"first_name":"John","last_name":"Doe","email":"haseeb.bhp@gmail.com","mobile_number":"+923068760177","password":"Nateglass@123"}'

# 2. Verify OTP
curl -X POST http://127.0.0.1:8000/api/users/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{"mobile_number":"+923068760177","otp":"YOUR_TOKEN_FROM_EMAIL"}'

# 3. Login
curl -X POST http://127.0.0.1:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"mobile_number":"+923068760177","password":"Nateglass@123"}'

# 4. Resend OTP (optional)
curl -X POST http://127.0.0.1:8000/api/users/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{"mobile_number":"+923068760177"}'

# 5. Forgot Password
curl -X POST http://127.0.0.1:8000/api/users/forgot-password/ \
  -H "Content-Type: application/json" \
  -d '{"mobile_number":"+923068760177"}'

# 6. Reset Password
curl -X POST http://127.0.0.1:8000/api/users/reset-password/ \
  -H "Content-Type: application/json" \
  -d '{"mobile_number":"+923068760177","otp":"YOUR_TOKEN_FROM_EMAIL","new_password":"NewPassword@123"}'
```

## Admin APIs

Admins (users with `role: "admin"`) can manage riders and customers via token-authenticated endpoints.

Authentication: include header `Authorization: Token <admin-token>` obtained from the normal login endpoint.

- `GET /api/admin/customers/` — list all customers
- `GET /api/admin/riders/` — list all riders
- `POST /api/admin/riders/` — create a new rider (sends verification OTP to rider email)
 - `POST /api/admin/riders/` — create a new rider (sends verification OTP to rider email)
 - `POST /api/admin/create-rider/` — alias endpoint to create a new rider (same as above)

Example: create a rider as admin

```bash
curl -X POST http://127.0.0.1:8000/api/admin/riders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <ADMIN_TOKEN>" \
  -d '{"first_name":"Rider","last_name":"One","email":"rider1@example.com","mobile_number":"+923001112233","password":"RiderPass123","address":"City"}'
```

List customers and riders by role (single endpoint)

```bash
# list customers
curl -X GET 'http://127.0.0.1:8000/api/admin/users/?role=customer' \
  -H "Authorization: Token <ADMIN_TOKEN>"

# list riders
curl -X GET 'http://127.0.0.1:8000/api/admin/users/?role=rider' \
  -H "Authorization: Token <ADMIN_TOKEN>"

# list both (comma-separated)
curl -X GET 'http://127.0.0.1:8000/api/admin/users/?role=customer,rider' \
  -H "Authorization: Token <ADMIN_TOKEN>"

# list both (repeated params)
curl -X GET 'http://127.0.0.1:8000/api/admin/users/?role=customer&role=rider' \
  -H "Authorization: Token <ADMIN_TOKEN>"
```

Notes:
- Riders, customers and admins all use the same `POST /api/users/login/` endpoint to authenticate.
- Riders must complete OTP verification (`POST /api/users/verify-otp/`) before they can log in — the API enforces `is_mobile_verified` on login.
- When an admin creates a rider, an OTP is sent automatically to the rider's email; the rider must verify to log in.

Security considerations:
- Currently OTP expiry was removed per request; consider reintroducing expiry (e.g., 10 minutes) for improved security.
- Admin endpoints are protected by token auth and a role check (`role == 'admin'`). Ensure your admin accounts have `role` set to `admin`.

