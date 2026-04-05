# Finance Dashboard API

A role-based REST API built with **FastAPI** and **MySQL** for managing financial records. It supports user authentication via JWT tokens, three user roles with different access levels, and a full financial dashboard with income/expense tracking.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (Python) |
| Database | MySQL via SQLAlchemy + PyMySQL |
| Auth | JWT tokens (python-jose) |
| Password Hashing | bcrypt via passlib + SHA-256 pre-hash |
| Validation | Pydantic v2 |
| API Docs | Swagger UI at `/docs` |

---

## Project Structure

```
app/
├── auth.py        # Register & login endpoints
├── users.py       # User management endpoints
├── records.py     # Financial record CRUD endpoints
├── dashboard.py   # Summary & analytics endpoints
├── security.py    # JWT logic, password hashing, role guards
├── models.py      # SQLAlchemy DB models (User, FinancialRecord)
├── schemas.py     # Pydantic request/response schemas
└── database.py    # DB connection and session setup
```

---

## Setup

### 1. Install dependencies

```bash
pip install fastapi uvicorn sqlalchemy pymysql python-jose passlib bcrypt==4.0.1 passlib[bcrypt]==1.7.4 python-dotenv pydantic[email]
```

> **Important:** Use exactly `bcrypt==4.0.1` and `passlib[bcrypt]==1.7.4`. Newer bcrypt versions are incompatible with passlib.

### 2. Create `.env` file

```env
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=finance_dashboard
```

### 3. Create the MySQL database

```sql
CREATE DATABASE finance_dashboard;
```

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

API will be live at `http://127.0.0.1:8000`
Swagger docs at `http://127.0.0.1:8000/docs`

---

## User Roles

There are three roles with increasing levels of access:

```
viewer  →  analyst  →  admin
```

| Permission | Viewer | Analyst | Admin |
|---|:---:|:---:|:---:|
| View financial records | ✅ | ✅ | ✅ |
| View quick balance | ✅ | ✅ | ✅ |
| View recent activity | ✅ | ✅ | ✅ |
| View full dashboard summary | ❌ | ✅ | ✅ |
| Create / edit / delete records | ❌ | ❌ | ✅ |
| Manage users | ❌ | ❌ | ✅ |

> The **first user to register** is automatically assigned the `admin` role. All subsequent users default to `viewer`.

---

## Authentication Flow

### How it works

```
1. Register   →  POST /api/auth/register   →  account created
2. Login      →  POST /api/auth/login      →  receive JWT token
3. Use token  →  Add header: Authorization: Bearer <token>
4. Access     →  Protected routes validate token automatically
```

### Register

`POST /api/auth/register`

```json
{
  "name": "Ramya",
  "email": "ramya@gmail.com",
  "password": "yourpassword",
  "role": "viewer"
}
```

- First user registered becomes `admin` regardless of the role field.
- Duplicate emails are rejected.

### Login (JSON — for apps / Postman)

`POST /api/auth/login`

```json
{
  "email": "ramya@gmail.com",
  "password": "yourpassword"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Copy the `access_token` and include it in all further requests:

```
Authorization: Bearer eyJhbGci...
```

### Login via Swagger UI

Swagger UI has a built-in Authorize dialog that requires form-based login. A separate endpoint handles this:

`POST /api/auth/token`

1. Open `http://127.0.0.1:8000/docs`
2. Click the 🔒 **Authorize** button at the top
3. Enter your **email** in the `username` field and your password
4. Click **Authorize** — all protected endpoints in Swagger will now work automatically

---

## Password Security

Passwords go through two layers before being stored:

```
plain password
     ↓
SHA-256 hash  (always 32 bytes — bypasses bcrypt's 72-byte limit)
     ↓
base64 encode (always 44 ASCII chars)
     ↓
bcrypt hash   (stored in DB)
```

This pattern means passwords of any length are handled safely, and the same preparation is applied during both registration and login so they always match.

---

## API Endpoints

### Auth — `/api/auth`

| Method | Endpoint | Description | Auth required |
|---|---|---|:---:|
| POST | `/register` | Create a new account | No |
| POST | `/login` | Login with JSON, get JWT | No |
| POST | `/token` | Login via Swagger UI form | No |

---

### Users — `/api/users`

| Method | Endpoint | Description | Role required |
|---|---|---|---|
| GET | `/me` | Get your own profile | Any |
| GET | `/` | List all users | Admin |
| GET | `/{user_id}` | Get user by ID | Admin |
| PATCH | `/{user_id}` | Update name, role, or status | Admin |
| DELETE | `/{user_id}` | Delete a user | Admin |

**Safety rules enforced:**
- An admin cannot deactivate their own account
- An admin cannot delete their own account

---

### Financial Records — `/api/records`

| Method | Endpoint | Description | Role required |
|---|---|---|---|
| GET | `/` | List records (with filters + pagination) | Any |
| GET | `/{record_id}` | Get a single record | Any |
| POST | `/` | Create a new record | Admin |
| PATCH | `/{record_id}` | Update a record | Admin |
| DELETE | `/{record_id}` | Soft-delete a record | Admin |

**Filtering options for GET `/`:**

| Parameter | Type | Description |
|---|---|---|
| `type` | `income` or `expense` | Filter by record type |
| `category` | string | Partial match on category name |
| `start_date` | datetime | Records from this date |
| `end_date` | datetime | Records up to this date |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Records per page (default: 10, max: 100) |

> Deleted records are soft-deleted — they stay in the database with `is_deleted = true` and are hidden from all responses.

---

### Dashboard — `/api/dashboard`

| Method | Endpoint | Description | Role required |
|---|---|---|---|
| GET | `/summary` | Full analytics dashboard | Analyst, Admin |
| GET | `/balance` | Quick income/expense/net totals | Any |
| GET | `/recent` | Most recent records (up to 50) | Any |

**Dashboard summary response includes:**
- Total income, total expenses, net balance
- Record count
- Category totals (sorted by highest amount)
- Last 5 records
- Monthly income vs expense trends (last 6 months)

---

## Database Models

### User

| Column | Type | Notes |
|---|---|---|
| `id` | BIGINT (unsigned) | Primary key, auto-increment |
| `name` | VARCHAR(100) | Required |
| `email` | VARCHAR(150) | Unique, indexed |
| `hashed_password` | VARCHAR(255) | bcrypt hash |
| `role` | ENUM | `viewer`, `analyst`, `admin` |
| `is_active` | BOOLEAN | Default `true` |
| `created_at` | DATETIME | Set on insert |
| `updated_at` | DATETIME | Set on update |

### FinancialRecord

| Column | Type | Notes |
|---|---|---|
| `id` | BIGINT (unsigned) | Primary key, auto-increment |
| `created_by` | BIGINT (FK) | References `users.id` |
| `amount` | DECIMAL(10,2) | Must be greater than 0 |
| `type` | ENUM | `income` or `expense` |
| `category` | VARCHAR(100) | Required, non-empty |
| `date` | DATETIME | Required |
| `notes` | TEXT | Optional |
| `is_deleted` | BOOLEAN | Soft-delete flag |
| `created_at` | DATETIME | Set on insert |
| `updated_at` | DATETIME | Set on update |

---

## Common Errors

| Code | Meaning | Common cause |
|---|---|---|
| 401 Unauthorized | Token missing or invalid | Forgot to add `Authorization: Bearer` header, or token expired |
| 403 Forbidden | Role too low | Your role doesn't have permission for this action |
| 404 Not Found | Resource doesn't exist | Wrong ID, or record was soft-deleted |
| 400 Bad Request | Validation failed | Duplicate email, invalid amount, empty category |
| 422 Unprocessable | Wrong request format | Sending form-data to a JSON endpoint or vice versa |

---

## Quick Start Example

```bash
# 1. Register (first user becomes admin)
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Ramya", "email": "ramya@gmail.com", "password": "mypassword", "role": "viewer"}'

# 2. Login and get token
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "ramya@gmail.com", "password": "mypassword"}'

# 3. Use the token (replace TOKEN with the access_token value)
curl -X GET http://127.0.0.1:8000/api/users/me \
  -H "Authorization: Bearer TOKEN"

# 4. Create a financial record (admin only)
curl -X POST http://127.0.0.1:8000/api/records/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 5000, "type": "income", "category": "Salary", "date": "2026-04-01T00:00:00"}'

# 5. View dashboard balance (any role)
curl -X GET http://127.0.0.1:8000/api/dashboard/balance \
  -H "Authorization: Bearer TOKEN"
```
