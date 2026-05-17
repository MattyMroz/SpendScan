--
-- File generated with SQLiteStudio v3.4.21 on sob. maj 16 11:52:26 2026
--
-- Text encoding used: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: budget_receipts
CREATE TABLE IF NOT EXISTS budget_receipts (id INTEGER PRIMARY KEY AUTOINCREMENT, budget_id INTEGER REFERENCES budgets (id) ON DELETE CASCADE ON UPDATE CASCADE NOT NULL, receipt_id INTEGER REFERENCES receipts (id) ON DELETE CASCADE ON UPDATE CASCADE NOT NULL, created_at TEXT DEFAULT (CURRENT_TIMESTAMP));

-- Table: budgets
CREATE TABLE IF NOT EXISTS budgets (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE NOT NULL, name TEXT NOT NULL, description TEXT, category_id INTEGER REFERENCES categories (id) ON DELETE SET NULL ON UPDATE CASCADE, amount_limit REAL NOT NULL CHECK (amount_limit >= 0), period_type TEXT NOT NULL CHECK (period_type IN ('weekly', 'monthly', 'quarterly', 'yearly')), alert_threshold_percent INTEGER NOT NULL DEFAULT (80) CHECK (alert_threshold_percent BETWEEN 1 AND 100), is_active INTEGER CHECK (is_active IN (0, 1)) DEFAULT (1), created_at TEXT DEFAULT (CURRENT_TIMESTAMP));

-- Table: categories
CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE);

-- Table: folder_receipts
CREATE TABLE IF NOT EXISTS folder_receipts (id INTEGER PRIMARY KEY AUTOINCREMENT, folder_id INTEGER NOT NULL REFERENCES folders (id) ON DELETE CASCADE ON UPDATE CASCADE, receipt_id INTEGER NOT NULL REFERENCES receipts (id) ON DELETE CASCADE ON UPDATE CASCADE, created_at TEXT DEFAULT (CURRENT_TIMESTAMP));

-- Table: folders
CREATE TABLE IF NOT EXISTS folders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE, name TEXT NOT NULL, description TEXT, created_at TEXT DEFAULT (CURRENT_TIMESTAMP));

-- Table: receipt_items
CREATE TABLE IF NOT EXISTS receipt_items (id INTEGER PRIMARY KEY AUTOINCREMENT, receipt_id INTEGER NOT NULL REFERENCES receipts (id) ON DELETE CASCADE ON UPDATE CASCADE, product_name TEXT NOT NULL, price REAL NOT NULL CHECK (price >= 0), quantity REAL NOT NULL DEFAULT (1) CHECK (quantity > 0), category_id INTEGER REFERENCES categories (id) ON DELETE SET NULL ON UPDATE CASCADE);

-- Table: receipts
CREATE TABLE IF NOT EXISTS receipts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE, image_path TEXT, shop_name TEXT NOT NULL, purchase_date TEXT NOT NULL, total_amount REAL CHECK (total_amount >= 0) NOT NULL, description TEXT, importance_level INTEGER CHECK (importance_level BETWEEN 1 AND 3), created_at TEXT DEFAULT (CURRENT_TIMESTAMP));

-- Table: subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE ON UPDATE CASCADE, name TEXT NOT NULL, amount REAL NOT NULL CHECK (amount >= 0), billing_cycle TEXT NOT NULL CHECK (billing_cycle IN ('weekly', 'monthly', 'quarterly', 'yearly')), next_payment_date TEXT NOT NULL, category_id INTEGER REFERENCES categories (id) ON DELETE SET NULL ON UPDATE CASCADE, is_active INTEGER CHECK (is_active IN (0, 1)) DEFAULT (1), created_at TEXT DEFAULT (CURRENT_TIMESTAMP));

-- Table: users
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT DEFAULT (CURRENT_TIMESTAMP));

-- Index: idx_budget_receipts_unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_budget_receipts_unique
ON budget_receipts(budget_id, receipt_id);

-- Index: idx_budgets_user_name_unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_budgets_user_name_unique
ON budgets(user_id, name);

-- Index: idx_folder_receipts_unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_folder_receipts_unique
ON folder_receipts(folder_id, receipt_id);

-- Index: idx_folders_user_name_unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_folders_user_name_unique
ON folders(user_id, name);

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
