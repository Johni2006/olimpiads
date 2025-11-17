#!/usr/bin/env python3
"""Test the by-pdf endpoint logic directly"""
import sqlite3
import urllib.parse

# The path from the API request
source_pdf_from_url = urllib.parse.unquote("olympiads/downloads/МГУ_Ломоносов/Философия/2021/Олимпиада%20по%20философии_Отборочный%20этап%20(младшие%20классы).pdf")

print(f"Path from URL (decoded): {repr(source_pdf_from_url)}")
print()

# Connect to the database the API uses
conn = sqlite3.connect('olympiad_questions.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Run the exact same query as the API
cursor.execute("SELECT * FROM questions WHERE source_pdf = ? ORDER BY id LIMIT 10000", [source_pdf_from_url])
rows = cursor.fetchall()

print(f"Query result: {len(rows)} questions found")
print()

if len(rows) == 0:
    # Let's see what paths actually exist
    cursor.execute("SELECT DISTINCT source_pdf FROM questions WHERE source_pdf LIKE '%Философия%2021%' LIMIT 10")
    paths = cursor.fetchall()
    print(f"Sample paths in DB matching Философия/2021:")
    for path in paths:
        p = dict(path)['source_pdf']
        print(f"  {repr(p)}")
        print(f"  Match: {p == source_pdf_from_url}")
        print()

conn.close()
