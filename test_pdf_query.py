#!/usr/bin/env python3
import sqlite3
import urllib.parse

# Точный путь который приходит из API
encoded_path = "olympiads/downloads/МГУ_Ломоносов/Философия/2021/Олимпиада%20по%20философии_Отборочный%20этап%20(младшие%20классы).pdf"
decoded_path = urllib.parse.unquote(encoded_path)

print(f"Encoded: {encoded_path}")
print(f"Decoded: {decoded_path}")
print()

# Проверяем в api БД
conn = sqlite3.connect('api/olympiad_questions.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM questions WHERE source_pdf = ?", [decoded_path])
count = cursor.fetchone()[0]
print(f"Questions found with decoded path: {count}")

# Проверим первые 5 записей
cursor.execute("SELECT DISTINCT source_pdf FROM questions WHERE source_pdf LIKE '%Философия%2021%' LIMIT 5")
paths = cursor.fetchall()
print(f"\nActual paths in DB:")
for path in paths:
    print(f"  - {path[0]}")
    print(f"    Match: {path[0] == decoded_path}")

conn.close()
