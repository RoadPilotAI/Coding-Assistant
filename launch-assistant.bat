@echo off
cd C:\Users\norma\coding-assistant
call venv\Scripts\activate
pip install -q requests beautifulsoup4 2>nul
python assistant.py
pause