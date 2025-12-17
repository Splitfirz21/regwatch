# Deployment Guide for RegWatch SG

This guide helps you deploy the RegWatch SG application to the cloud. We recommend **Vercel** for the frontend and **Render** for the backend.

## Prerequisites
- A **GitHub** account.
- **Node.js** and **Python** installed locally (which you have).

## Step 1: Push to GitHub
1. Create a new repository on GitHub (e.g., `regwatch-sg`).
2. Initialize git and push your code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/regwatch-sg.git
   git push -u origin main
   ```

## Step 2: Deploy Backend (Render)
1. Sign up/Login to [Render](https://render.com).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repo.
4. Configure the service:
   - **Name**: `regwatch-backend`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt` (Render usually detects this automatically)
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Click **Deploy Web Service**.
6. **Wait** for deployment. Copy the **Service URL** (e.g., `https://regwatch-backend.onrender.com`).

## Step 3: Deploy Frontend (Vercel)
1. Sign up/Login to [Vercel](https://vercel.com).
2. Click **Add New** -> **Project**.
3. Import your `regwatch-sg` repo.
4. Configure the project:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Environment Variables**:
     - Key: `VITE_API_URL`
     - Value: `https://regwatch-backend.onrender.com` (The URL you copied from Render, **without** a trailing slash).
5. Click **Deploy**.

## Step 4: Verification
- Visit the Vercel URL.
- The dashboard should load.
- Click "Scan" to verify the backend connection.

## Troubleshooting
- **CORS Error**: If you see network errors, check `backend/main.py`. Currently it allows all origins (`*`), which is permissive.
- **Database**: The SQLite database (`news.db`) is stored *ephemerally* on Render's free tier. Use a persistent disk or a managed PostgreSQL database (like Supabase or Neon) for production persistence.
