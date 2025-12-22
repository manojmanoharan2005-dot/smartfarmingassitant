# Render Deployment Guide for Smart Farming Assistant

## Why Render?
- ✅ No 250MB size limit (unlike Vercel)
- ✅ Perfect for ML/AI applications
- ✅ Free tier available
- ✅ Easy GitHub integration
- ✅ Persistent file storage option

## Deployment Steps

### 1. Create Render Account
- Go to [render.com](https://render.com)
- Sign up with GitHub (recommended)

### 2. Create New Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Select `manojmanoharan2005-dot/smartfarming`

### 3. Configure Service

**Basic Settings:**
- **Name**: `smartfarming` (or your choice)
- **Region**: Choose closest to you
- **Branch**: `main`
- **Root Directory**: `smartfarming` (if repository root is different)
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

**Instance Type:**
- **Free**: Good for testing
- **Starter ($7/month)**: Better for production with ML models

### 4. Environment Variables
Add these in **Environment** section:

```
GEMINI_API_KEY=AIzaSyAjLAYYhocxG8jrWAw_aY4xa8_yE303MOk
MONGODB_URI=mongodb://manoj:manoj28@atlas-sql-694288270ca3172bbde45a59-ytslre.a.query.mongodb.net/myVirtualDatabase?ssl=true&authSource=admin
MONGODB_DB=myVirtualDatabase
FLASK_ENV=production
PYTHON_VERSION=3.11.0
```

### 5. Advanced Settings (Optional)

**Health Check Path:** `/`

**Auto-Deploy:** Enable (deploys automatically on git push)

### 6. Deploy
- Click **"Create Web Service"**
- Wait for build and deployment (5-10 minutes)
- Your app will be live at: `https://smartfarming.onrender.com`

## Alternative: Railway Deployment

### Railway Steps:
1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select your repository
5. Railway auto-detects Python and Flask
6. Add environment variables
7. Deploy!

**Railway automatically:**
- Detects `requirements.txt`
- Installs dependencies
- Runs `gunicorn app:app`

## Alternative: PythonAnywhere

### PythonAnywhere Steps:
1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Go to **Web** tab → **Add a new web app**
3. Choose **Flask** and Python version
4. Upload your code via Git or Files
5. Configure WSGI file to point to `app:app`
6. Set environment variables in WSGI file
7. Reload web app

## Comparison

| Platform | Free Tier | ML Support | Deployment | Best For |
|----------|-----------|------------|------------|----------|
| **Render** | ✅ 750hrs/month | ⭐⭐⭐⭐⭐ | GitHub | Production ML apps |
| **Railway** | ✅ $5 credit | ⭐⭐⭐⭐⭐ | GitHub | Fast deployment |
| **PythonAnywhere** | ✅ Limited | ⭐⭐⭐⭐ | Git/Upload | Python-specific |
| **Heroku** | ❌ Paid only | ⭐⭐⭐⭐ | Git | Enterprise |
| **Vercel** | ✅ | ⭐⭐ | GitHub | Frontend/small apps |

## Recommended: Render

**Pros:**
- Handles large ML models easily
- Free tier is generous
- Automatic deployments from GitHub
- Easy environment variable management
- Good documentation

**Cons:**
- Free tier has cold starts (50 seconds)
- Free services sleep after 15 mins of inactivity

## Post-Deployment

### Monitor Logs
- Render Dashboard → Your Service → Logs
- Check for any errors

### Custom Domain (Optional)
- Render Settings → Custom Domains
- Add your domain and configure DNS

### Database
- Your MongoDB Atlas connection will work
- Consider Render's PostgreSQL if needed

## Troubleshooting

### Build Fails
- Check `requirements.txt` for version conflicts
- View build logs in Render dashboard

### App Crashes
- Check runtime logs
- Verify environment variables are set
- Ensure `gunicorn` is in requirements.txt

### Slow First Load
- Free tier sleeps after inactivity
- Upgrade to paid tier for always-on service

## Cost Estimate

**Free Tier:**
- 750 hours/month
- Automatic sleep after 15 mins inactivity
- Good for development/testing

**Starter ($7/month):**
- Always on
- Better performance
- Recommended for production

## Files Created for Deployment

✅ `Procfile` - Tells Render how to start app
✅ `requirements.txt` - Updated with gunicorn
✅ `runtime.txt` - Specifies Python version

## Ready to Deploy!

1. Push changes to GitHub
2. Go to Render.com
3. Follow steps above
4. Your app will be live in ~10 minutes

---

**Recommended Platform**: Render
**Estimated Build Time**: 5-10 minutes
**Free Tier**: Available
**Last Updated**: December 19, 2025
