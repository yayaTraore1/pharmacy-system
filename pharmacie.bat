@echo off
cd C:\pharmacy_app

call venv\Scripts\activate

start http://127.0.0.1:8000

uvicorn app.main:app --reload