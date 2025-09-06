
Awesome idea. Let’s blueprint a clean, scalable backend you can start coding right away.

# Technical Design – Restaurant Platform (Backend)

**Stack**

* **API**: FastAPI (Python 3.11+), Pydantic v2, Uvicorn
* **DB**: PostgreSQL 14+
* **ORM/Migrations**: SQLAlchemy 2.x + Alembic
* **Auth**: JWT (access+refresh), OAuth2 password flow
* **Other**: Redis (optional, for rate limiting/sessions), S3-compatible storage for images

**Key requirements**

* One **Owner (User)** can manage **multiple Restaurants**
* Manage **tables**, **menus**, **orders**, and **customers**
* Track **order lifecycle** and **payments**
* Clean tenant boundaries (data per restaurant)

---

## 1) High-level Domain Model

* **User**: login identity (Owner, Staff, Admin)
* **Restaurant**: belongs to exactly one Owner
* **Table**: physical table in a restaurant, QR-enabled
* **Customer**: per-restaurant customer record
* **Menu**: Categories → Items → Option Groups → Options
* **Order**: order header, with Order Items and chosen Options
* **Payment**: payment attempts/receipts for an order

---

## 2) Database Schema (PostgreSQL)

> Includes enums, constraints, indexes, and snapshotting of prices/names for historical accuracy.

```sql
-- Enums
CREATE TYPE user_role AS ENUM ('OWNER','STAFF','ADMIN');
CREATE TYPE table_status AS ENUM ('AVAILABLE','OCCUPIED','RESERVED','INACTIVE');
CREATE TYPE order_status AS ENUM ('CREATED','CONFIRMED','IN_PROGRESS','SERVED','COMPLETED','CANCELED');
CREATE TYPE order_type AS ENUM ('DINE_IN','TAKEAWAY','DELIVERY');
CREATE TYPE payment_method AS ENUM ('CASH','CARD','UPI','OTHER');
CREATE TYPE payment_status AS ENUM ('PENDING','CAPTURED','REFUNDED','FAILED');

-- Users
CREATE TABLE users (
  id              BIGSERIAL PRIMARY KEY,
  email           CITEXT UNIQUE NOT NULL,
  password_hash   TEXT NOT NULL,
  full_name       TEXT,
  phone           TEXT,
  role            user_role NOT NULL DEFAULT 'OWNER',
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_users_email ON users (email);

-- Restaurants
CREATE TABLE restaurants (
  id              BIGSERIAL PRIMARY KEY,
  owner_user_id   BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  name            TEXT NOT NULL,
  legal_name      TEXT,
  description     TEXT,
  phone           TEXT,
  address_line1   TEXT,
  address_line2   TEXT,
  city            TEXT,
  state           TEXT,
  postal_code     TEXT,
  country         TEXT,
  timezone        TEXT NOT NULL DEFAULT 'Asia/Kolkata',
  currency        TEXT NOT NULL DEFAULT 'INR',
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_restaurants_owner ON restaurants (owner_user_id);

-- Tables
CREATE TABLE restaurant_tables (
  id              BIGSERIAL PRIMARY KEY,
  restaurant_id   BIGINT NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
  label           TEXT NOT NULL, -- e.g., T1, A-05
  capacity        INT NOT NULL DEFAULT 2,
  status          table_status NOT NULL DEFAULT 'AVAILABLE',
  qr_code_url     TEXT,
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (restaurant_id, label)
);
CREATE INDEX idx_tables_restaurant ON restaurant_tables (restaurant_id);

-- Customers (per restaurant)
CREATE TABLE customers (
  id              BIGSERIAL PRIMARY KEY,
  restaurant_id   BIGINT NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
  name            TEXT,
  phone           TEXT,
  email           CITEXT,
  notes           TEXT,
  loyalty_points  INT NOT NULL DEFAULT 0,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (restaurant_id, phone),
  UNIQUE (restaurant_id, email)
);
CREATE INDEX idx_customers_restaurant ON customers (restaurant_id);

-- Menu Categories
CREATE TABLE menu_categories (
  id              BIGSERIAL PRIMARY KEY,
  restaurant_id   BIGINT NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
  name            TEXT NOT NULL,
  display_order   INT NOT NULL DEFAULT 0,
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (restaurant_id, name)
);

-- Menu Items
CREATE TABLE menu_items (
  id              BIGSERIAL PRIMARY KEY,
  restaurant_id   BIGINT NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
  category_id     BIGINT REFERENCES menu_categories(id) ON DELETE SET NULL,
  name            TEXT NOT NULL,
  description     TEXT,
  sku             TEXT,
  base_price      NUMERIC(10,2) NOT NULL,
  image_url       TEXT,
  is_available    BOOLEAN NOT NULL DEFAULT TRUE,
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (restaurant_id, name)
);
CREATE INDEX idx_menu_items_restaurant ON menu_items (restaurant_id);
CREATE INDEX idx_menu_items_category ON menu_items (category_id);

-- Option Groups (e.g., "Size", "Extras")
CREATE TABLE option_groups (
  id              BIGSERIAL PRIMARY KEY,
  restaurant_id   BIGINT NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
  name            TEXT NOT NULL,
  selection_type  TEXT NOT NULL CHECK (selection_type IN ('SINGLE','MULTI')),
  min_select      INT NOT NULL DEFAULT 0,
  max_select      INT NOT NULL DEFAULT 1,
  required        BOOLEAN NOT NULL DEFAULT FALSE,
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (restaurant_id, name)
);

-- Options (e.g., "Cheese +₹20")
CREATE TABLE options (
  id              BIGSERIAL PRIMARY KEY,
  option_group_id BIGINT NOT NULL REFERENCES option_groups(id) ON DELETE CASCADE,
  name            TEXT NOT NULL,
  price_delta     NUMERIC(10,2) NOT NULL DEFAULT 0,
  is_available    BOOLEAN NOT NULL DEFAULT TRUE,
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Link Item ↔ Option Groups (item can reference many groups)
CREATE TABLE item_option_groups (
  menu_item_id    BIGINT NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
  option_group_id BIGINT NOT NULL REFERENCES option_groups(id) ON DELETE CASCADE,
  PRIMARY KEY (menu_item_id, option_group_id)
);

-- Orders
CREATE TABLE orders (
  id              BIGSERIAL PRIMARY KEY,
  restaurant_id   BIGINT NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
  table_id        BIGINT REFERENCES restaurant_tables(id) ON DELETE SET NULL,
  customer_id     BIGINT REFERENCES customers(id) ON DELETE SET NULL,
  order_type      order_type NOT NULL DEFAULT 'DINE_IN',
  status          order_status NOT NULL DEFAULT 'CREATED',
  source          TEXT NOT NULL DEFAULT 'WAITER_APP', -- or CUSTOMER_QR
  opened_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  confirmed_at    TIMESTAMPTZ,
  closed_at       TIMESTAMPTZ,
  notes           TEXT,
  subtotal        NUMERIC(10,2) NOT NULL DEFAULT 0,
  tax_total       NUMERIC(10,2) NOT NULL DEFAULT 0,
  discount_total  NUMERIC(10,2) NOT NULL DEFAULT 0,
  grand_total     NUMERIC(10,2) NOT NULL DEFAULT 0,
  created_by_user BIGINT REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX idx_orders_restaurant ON orders (restaurant_id);
CREATE INDEX idx_orders_status ON orders (restaurant_id, status);

-- Order Items (snapshot prices & names)
CREATE TABLE order_items (
  id                  BIGSERIAL PRIMARY KEY,
  order_id            BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  menu_item_id        BIGINT REFERENCES menu_items(id) ON DELETE SET NULL,
  name_snapshot       TEXT NOT NULL,
  unit_price_snapshot NUMERIC(10,2) NOT NULL,
  quantity            INT NOT NULL CHECK (quantity > 0),
  instructions        TEXT,
  line_subtotal       NUMERIC(10,2) NOT NULL DEFAULT 0
);
CREATE INDEX idx_order_items_order ON order_items (order_id);

-- Chosen Options (snapshot names & price deltas)
CREATE TABLE order_item_options (
  id                      BIGSERIAL PRIMARY KEY,
  order_item_id           BIGINT NOT NULL REFERENCES order_items(id) ON DELETE CASCADE,
  option_id               BIGINT REFERENCES options(id) ON DELETE SET NULL,
  name_snapshot           TEXT NOT NULL,
  price_delta_snapshot    NUMERIC(10,2) NOT NULL DEFAULT 0
);

-- Payments
CREATE TABLE payments (
  id              BIGSERIAL PRIMARY KEY,
  order_id        BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  method          payment_method NOT NULL,
  status          payment_status NOT NULL DEFAULT 'PENDING',
  amount          NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
  txn_ref         TEXT,
  paid_at         TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_payments_order ON payments (order_id);
```

### Notes

* **Snapshots** inside `order_items` and `order_item_options` preserve history even if menu prices later change.
* **Uniqueness** constraints avoid duplicates (e.g., table label per restaurant).
* Add **Row Level Security (RLS)** later if you expose direct SQL (not needed with API-only access).
* Consider **soft deletes** (`deleted_at`) if you want reversible deletes.

---

## 3) Diagrams (Mermaid)

### 3.1 ER Diagram

```mermaid
erDiagram
  USERS ||--o{ RESTAURANTS : owns
  RESTAURANTS ||--o{ RESTAURANT_TABLES : has
  RESTAURANTS ||--o{ CUSTOMERS : serves
  RESTAURANTS ||--o{ MENU_CATEGORIES : groups
  MENU_CATEGORIES ||--o{ MENU_ITEMS : contains
  RESTAURANTS ||--o{ MENU_ITEMS : offers
  MENU_ITEMS ||--o{ ITEM_OPTION_GROUPS : links
  OPTION_GROUPS ||--o{ ITEM_OPTION_GROUPS : linked
  OPTION_GROUPS ||--o{ OPTIONS : includes
  RESTAURANTS ||--o{ ORDERS : receives
  RESTAURANT_TABLES ||--o{ ORDERS : seats
  CUSTOMERS ||--o{ ORDERS : places
  ORDERS ||--o{ ORDER_ITEMS : contains
  ORDER_ITEMS ||--o{ ORDER_ITEM_OPTIONS : chooses
  ORDERS ||--o{ PAYMENTS : paid_by

  USERS {
    bigserial id PK
    citext email
    text password_hash
    user_role role
  }

  RESTAURANTS {
    bigserial id PK
    bigint owner_user_id FK
    text name
    text timezone
    text currency
  }

  RESTAURANT_TABLES {
    bigserial id PK
    bigint restaurant_id FK
    text label
    table_status status
  }

  CUSTOMERS {
    bigserial id PK
    bigint restaurant_id FK
    text name
    text phone
    citext email
  }

  MENU_CATEGORIES {
    bigserial id PK
    bigint restaurant_id FK
    text name
  }

  MENU_ITEMS {
    bigserial id PK
    bigint restaurant_id FK
    bigint category_id FK
    text name
    numeric base_price
  }

  OPTION_GROUPS {
    bigserial id PK
    bigint restaurant_id FK
    text name
    text selection_type
    int min_select
    int max_select
  }

  OPTIONS {
    bigserial id PK
    bigint option_group_id FK
    text name
    numeric price_delta
  }

  ITEM_OPTION_GROUPS {
    bigint menu_item_id FK
    bigint option_group_id FK
  }

  ORDERS {
    bigserial id PK
    bigint restaurant_id FK
    bigint table_id FK
    bigint customer_id FK
    order_type order_type
    order_status status
    numeric grand_total
  }

  ORDER_ITEMS {
    bigserial id PK
    bigint order_id FK
    bigint menu_item_id FK
    text name_snapshot
    numeric unit_price_snapshot
    int quantity
  }

  ORDER_ITEM_OPTIONS {
    bigserial id PK
    bigint order_item_id FK
    bigint option_id FK
    text name_snapshot
    numeric price_delta_snapshot
  }

  PAYMENTS {
    bigserial id PK
    bigint order_id FK
    payment_method method
    payment_status status
    numeric amount
  }
```

### 3.2 Sequence – Place an Order (Dine-In via Waiter App)

```mermaid
sequenceDiagram
  autonumber
  participant W as Waiter App
  participant API as FastAPI
  participant DB as PostgreSQL

  W->>API: POST /auth/login (JWT)
  API->>DB: Verify user
  API-->>W: 200 (access_token)

  W->>API: POST /orders {restaurant_id, table_id, items...}
  API->>DB: INSERT order (status=CREATED)
  API->>DB: INSERT order_items & options (snapshots)
  API-->>W: 201 {order_id, status=CREATED, totals...}

  W->>API: POST /orders/{id}/confirm
  API->>DB: UPDATE orders SET status=CONFIRMED, confirmed_at=now()
  API-->>W: 200 {status=CONFIRMED}

  W->>API: POST /payments {order_id, method, amount}
  API->>DB: INSERT payment (status=CAPTURED)
  API->>DB: UPDATE orders SET status=COMPLETED, closed_at=now()
  API-->>W: 200 {order_status=COMPLETED, receipt...}
```

---

## 4) API Design (FastAPI)

### Auth

* `POST /auth/register-owner` → create Owner user + (optional) first restaurant
* `POST /auth/login` → JWT tokens
* `POST /auth/refresh` → new access token

### Restaurants

* `GET /restaurants` (owner-only, list own)
* `POST /restaurants`
* `GET /restaurants/{id}`
* `PATCH /restaurants/{id}` (name, contact, is\_active)

### Tables

* `GET /restaurants/{rid}/tables`
* `POST /restaurants/{rid}/tables`
* `PATCH /tables/{id}` (status, label, capacity)
* `POST /tables/{id}/qr` (returns signed URL/PNG)
* `GET /tables/{id}/orders?status=OPEN` (current order on table)

### Customers

* `GET /restaurants/{rid}/customers?query=...`
* `POST /restaurants/{rid}/customers`
* `PATCH /customers/{id}`
* `GET /customers/{id}`
* `DELETE /customers/{id}` (soft delete recommended)

### Menu

* `GET /restaurants/{rid}/menu` (denormalized tree)
* `POST /restaurants/{rid}/categories`
* `POST /restaurants/{rid}/items`
* `PATCH /menu/items/{id}`
* `POST /menu/items/{id}/option-groups/{gid}` (link)
* `POST /restaurants/{rid}/option-groups`
* `POST /option-groups/{gid}/options`
* `POST /restaurants/{rid}/menu:bulk-upload` (CSV/JSON)

### Orders

* `POST /orders` (creates header + items)
* `GET /orders/{id}`
* `POST /orders/{id}/confirm`
* `POST /orders/{id}/status` (IN\_PROGRESS/SERVED/CANCELED)
* `POST /orders/{id}/items` (add more)
* `DELETE /order-items/{id}`
* `POST /orders/{id}/recompute-totals` (server calculates totals)
* `GET /restaurants/{rid}/orders?from=&to=&status=`

### Payments

* `POST /payments` (order\_id, method, amount)
* `GET /orders/{id}/payments`
* (Optional) `POST /payments/{id}/refund`

### Public (QR flow)

* `GET /public/menus/{restaurant_slug}` (read-only)
* `POST /public/orders` (if you enable customer self-ordering)

---

## 5) Request/Response Examples

### Create Order

```http
POST /orders
Authorization: Bearer <token>
Content-Type: application/json

{
  "restaurant_id": 101,
  "table_id": 55,
  "order_type": "DINE_IN",
  "customer_id": null,
  "items": [
    {
      "menu_item_id": 9001,
      "quantity": 2,
      "instructions": "Less spicy",
      "options": [12001, 12003]  // option IDs
    }
  ],
  "notes": "Serve hot"
}
```

**Server computes snapshots & totals**:

```json
{
  "id": 777,
  "status": "CREATED",
  "subtotal": 540.00,
  "tax_total": 27.00,
  "discount_total": 0.00,
  "grand_total": 567.00,
  "items": [
    {
      "id": 1,
      "name": "Paneer Tikka",
      "unit_price": 250.00,
      "quantity": 2,
      "options": [
        {"name":"Extra Cheese","delta":20.00}
      ],
      "line_subtotal": 540.00
    }
  ]
}
```

### Capture Payment

```http
POST /payments
{
  "order_id": 777,
  "method": "UPI",
  "amount": 567.00,
  "txn_ref": "UPI-AXIS-ABC123"
}
```

Response:

```json
{"id": 321, "status": "CAPTURED", "paid_at": "2025-08-14T13:10:00Z"}
```

---

## 6) Validation & Business Rules

* **Cross-restaurant isolation**: Every write must check `restaurant_id` belongs to the authenticated owner.
* **Option selection**: Enforce `min_select/max_select` & `required` per option group when adding order items.
* **Totals**: Always recompute server-side:
  `line_subtotal = quantity * (unit_price_snapshot + Σ option price_delta_snapshot)`
  `subtotal = Σ line_subtotal` → apply `tax` and `discount` → `grand_total`.
* **Table status**: When an order is **CONFIRMED**, set table `status=OCCUPIED`. When **COMPLETED/CANCELED** and no other open orders, set `AVAILABLE`.
* **Uniqueness**: `(restaurant_id, phone)` for customers, `(restaurant_id, label)` for tables.
* **Idempotency**: For payment capture endpoints, accept an `Idempotency-Key` header.

---

## 7) Project Structure

```
app/
  main.py
  core/
    config.py          # settings from env
    security.py        # JWT utils
    deps.py            # FastAPI Depends utilities
  db/
    base.py            # SQLAlchemy Base
    session.py         # engine/session
    migrations/        # Alembic
  models/              # SQLAlchemy models
  schemas/             # Pydantic models (request/response)
  crud/                # DB operations
  api/
    routers/
      auth.py
      restaurants.py
      tables.py
      customers.py
      menu.py
      orders.py
      payments.py
    dependencies.py
  services/
    orders.py          # totals, validation
    payments.py        # payment handling
  utils/
    qrcode.py          # generate QR images (optional)
```

**Example `settings` (.env)**

```
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/restaurant
JWT_SECRET=supersecret
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
S3_BUCKET_URL=https://s3.example.com/bucket
```

---

## 8) Sample SQLAlchemy Models (condensed)

```python
# app/models/restaurant.py
class Restaurant(Base):
    __tablename__ = "restaurants"
    id = sa.Column(sa.BigInteger, primary_key=True)
    owner_user_id = sa.Column(sa.BigInteger, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    name = sa.Column(sa.Text, nullable=False)
    timezone = sa.Column(sa.Text, default="Asia/Kolkata", nullable=False)
    currency = sa.Column(sa.Text, default="INR", nullable=False)
    is_active = sa.Column(sa.Boolean, default=True, nullable=False)

    owner = sa.orm.relationship("User", back_populates="restaurants")
    tables = sa.orm.relationship("RestaurantTable", back_populates="restaurant", cascade="all, delete")
```

```python
# app/services/orders.py (core totals)
def recompute_totals(order: Order) -> None:
    subtotal = Decimal("0")
    for item in order.items:
        unit = item.unit_price_snapshot + sum(opt.price_delta_snapshot for opt in item.options)
        item.line_subtotal = (unit * item.quantity).quantize(Decimal("0.01"))
        subtotal += item.line_subtotal
    order.subtotal = subtotal
    order.tax_total = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))  # example 5% GST split later
    order.grand_total = (order.subtotal + order.tax_total - order.discount_total).quantize(Decimal("0.01"))
```

---

## 9) Security & Multi-Tenancy

* **JWT** with role claims (`role`, `owner_user_id`).
* For every endpoint with `restaurant_id`, verify ownership:
  `restaurant.owner_user_id == current_user.id` (unless `ADMIN`).
* Use **Pydantic** models to whitelist/validate inputs.
* Add **rate limiting** for public endpoints.
* Store passwords with **Argon2** or **bcrypt**.
* Optionally enable **CORS** for your frontends.

---

## 10) Testing Strategy

* **Unit**: services (totals, selection rules).
* **Integration**: CRUD endpoints with a test DB (pytest + httpx + FastAPI test client).
* **Migration**: generate via Alembic; test `upgrade`/`downgrade`.
* **Fixtures**: seed owner → restaurant → menu → table → order.

---

## 11) Roadmap (phased)

**Phase 1 (MVP)**

* Auth, Restaurants, Tables, Menu (basic), Orders (create/confirm/complete), Payments (record only), Customers CRUD.

**Phase 2**

* Bulk menu upload, QR self-ordering (public endpoints), receipts/PDF, GST breakup.

**Phase 3**

* Staff roles/permissions, reports (daily sales, top items), loyalty rules, webhooks (KPIs to Slack), inventory hooks.

---

## 12) Quick Start (commands)

```bash
# Create project
uv venv && source .venv/bin/activate
pip install fastapi uvicorn "sqlalchemy>=2.0" psycopg[binary] alembic pydantic bcrypt python-jose

# Alembic init & first migration
alembic init app/db/migrations
# configure env.py to use settings.DATABASE_URL
alembic revision --autogenerate -m "init schema"
alembic upgrade head

# Run
uvicorn app.main:app --reload
```
