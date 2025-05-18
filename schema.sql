CREATE TABLE IF NOT EXISTS users (
    id	INTEGER NOT NULL,
    sex	TEXT DEFAULT 0,
    weight TEXT DEFAULT 0,
    height	TEXT DEFAULT 0,
    bithday    TEXT DEFAULT 0,
    email	TEXT NOT NULL,
    login	TEXT,
    password TEXT NOT NULL,
    name  TEXT,
    surname TEXT,
    phone TEXT,
    is_active	TEXT DEFAULT 1,
    PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS subscriptions (
    user_id TEXT NOT NULL,
    is_active TEXT DEfAULT 1,
    start_date TEXT DEFAULT 0
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    status TEXT DEFAULT 0,
    PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS admins (
    user_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS goals (
    user_id TEXT NOT NULL,
    calories TEXT DEFAULT 0,
    protein TEXT DEFAULT 0,
    fat TEXT DEFAULT 0,
    carbohydrate TEXT DEFAULT 0,
    weight TEXT DEFAULT 0,
    PRIMARY KEY("user_id")
);
CREATE TABLE "dishes" (
	"id"	INTEGER,
	"food_id"	TEXT,
	"dish"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE "food_data" (
	"id"	INTEGER NOT NULL UNIQUE,
	"user_id"	TEXT NOT NULL,
	"table_path"	TEXT,
	"kc"	TEXT,
	"date"	TEXT,
	"protein"	TEXT,
	"fat"	TEXT,
	"carbohydrate"	TEXT,
	"weight"	TEXT,
	"is_photo"	INTEGER,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE "weight_data" (
	"id"	INTEGER NOT NULL,
	"user_id"	TEXT NOT NULL,
	"date"	TEXT DEFAULT 0,
	"weight"	TEXT NOT NULL DEFAULT 0,
	PRIMARY KEY("id" AUTOINCREMENT)
);