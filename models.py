import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Tabela de usuários
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE,
        renda REAL DEFAULT 0
    )
    ''')
    # Tabela de despesas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_phone TEXT,
        valor REAL,
        categoria TEXT,
        data TEXT,
        descricao TEXT
    )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
