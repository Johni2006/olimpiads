#!/usr/bin/env python3
"""
Список доступных моделей Gemini
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("❌ GEMINI_API_KEY not found")
    exit(1)

genai.configure(api_key=api_key)

print("📋 Доступные модели Gemini:")
print("=" * 60)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"\n✅ {model.name}")
        print(f"   Описание: {model.description}")
        print(f"   Методы: {', '.join(model.supported_generation_methods)}")
