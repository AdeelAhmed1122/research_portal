# University Research Opportunity Portal

Flask + MySQL backend, plain HTML/CSS/JS frontend. Deployable on Vercel.

## Structure
```
api/index.py        Vercel entry point (imports the Flask app)
backend/            app.py, db.py, config.py, schema.sql
public/             index.html, script.js, style.css (served as static files)
requirements.txt    Python dependencies (must be in the project root)
vercel.json         routes /api/* to the Flask function
```

## Run locally
```
pip install -r requirements.txt
export DB_USER=root DB_PASSWORD=your_password   # PowerShell: $env:DB_USER="root"; ...
cd backend && python app.py
```
Open http://localhost:5000

## Deploy to Vercel
1. Create a cloud MySQL database (Aiven, TiDB Cloud, Railway, etc.) and note host, port, user, password, database name.
2. Push this folder to GitHub (`.gitignore` already excludes `venv`).
3. Vercel -> Add New -> Project -> import the repo.
4. Add Environment Variables: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, DB_SSL=true
   (optional DB_SSL_CA if your provider gives you a CA file).
5. Deploy. The `opportunities` table is created automatically on the first request.
