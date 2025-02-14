import sqlite3

def add_expense(user_phone, valor, categoria, data, descricao=""):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenses (user_phone, valor, categoria, data, descricao)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_phone, valor, categoria, data, descricao))
    conn.commit()
    conn.close()

def set_renda(user_phone, renda):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE phone = ?', (user_phone,))
    user = cursor.fetchone()
    if user:
        cursor.execute('UPDATE users SET renda = ? WHERE phone = ?', (renda, user_phone))
    else:
        cursor.execute('INSERT INTO users (phone, renda) VALUES (?, ?)', (user_phone, renda))
    conn.commit()
    conn.close()

def get_summary(user_phone, periodo="mensal"):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(valor) FROM expenses WHERE user_phone = ?', (user_phone,))
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total

def reset_all():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Remove todos os registros da tabela de despesas
    cursor.execute("DELETE FROM expenses")
    # Remove todos os registros da tabela de usuários
    cursor.execute("DELETE FROM users")
    conn.commit()
    conn.close()

import sqlite3

def get_renda(user_phone):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT renda FROM users WHERE phone = ?", (user_phone,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return 0.0

def get_summary_by_category(user_phone):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT categoria, SUM(valor) FROM expenses WHERE user_phone = ? GROUP BY categoria",
        (user_phone,)
    )
    results = cursor.fetchall()
    conn.close()
    summary = {}
    for categoria, total in results:
        summary[categoria] = total
    return summary
