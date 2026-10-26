import aiosqlite
from datetime import datetime

DB_NAME = "bot.db"


async def init_db():
	async with aiosqlite.connect(DB_NAME) as db:
		await db.execute("""
			CREATE TABLE IF NOT EXISTS users (
				user_id INTEGER PRIMARY KEY,
				username TEXT,
				balance REAL DEFAULT 0,
				created_at TEXT
			)
		""")
		await db.execute("""
			CREATE TABLE IF NOT EXISTS orders (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				user_id INTEGER,
				amount REAL,
				currency TEXT,
				network TEXT,
				status TEXT DEFAULT 'pending',
				tx_id TEXT,
				created_at TEXT,
				UNIQUE(tx_id)
			)
		""")
		await db.commit()


async def add_user(user_id: int, username: str = None):
	async with aiosqlite.connect(DB_NAME) as db:
		await db.execute(
			"INSERT OR IGNORE INTO users (user_id, username, created_at) VALUES (?, ?, ?)",
			(user_id, username, datetime.now().isoformat())
		)
		await db.commit()


async def get_balance(user_id: int) -> float:
	async with aiosqlite.connect(DB_NAME) as db:
		async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
			row = await cursor.fetchone()
			return row[0] if row else 0.0


async def create_order(user_id: int, amount: float, currency: str, network: str, tx_id: str):
	async with aiosqlite.connect(DB_NAME) as db:
		await db.execute(
			"INSERT INTO orders (user_id, amount, currency, network, tx_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
			(user_id, amount, currency, network, tx_id, datetime.now().isoformat())
		)
		await db.commit()
