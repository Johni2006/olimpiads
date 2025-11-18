#!/usr/bin/env python3
"""
Исправление кодировки с помощью библиотеки ftfy
"""
from ftfy import fix_text

# Читаем файл
with open('web/index.html', 'r', encoding='utf-8') as f:
    broken_text = f.read()

# Исправляем кодировку
fixed_text = fix_text(broken_text)

# Показываем пример исправления
title_start = fixed_text.find('<title>')
title_end = fixed_text.find('</title>') + 8

print("Проверка title:")
print(f"До:  {broken_text[title_start:title_end]}")
print(f"После: {fixed_text[title_start:title_end]}")

# Сохраняем исправленный файл
with open('web/index.html', 'w', encoding='utf-8') as f:
    f.write(fixed_text)

print("\n✅ Файл успешно исправлен!")
