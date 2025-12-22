# Vercel Deployment Guide for Smart Farming Assistant

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI** (optional): `npm install -g vercel`
3. **GitHub Repository**: Push your code to GitHub (recommended)

## Deployment Steps

### Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Login to Vercel**
   - Go to [vercel.com](https://vercel.com) and login

2. **Import Project**
   - Click "Add New" → "Project"
   - Import your GitHub repository
   - Select the `smartfarming` folder as the root directory

3. **Configure Project**
   - Framework Preset: **Other**
   - Root Directory: `./` (or `smartfarming` if needed)
   - Build Command: (leave empty)
   - Output Directory: (leave empty)

4. **Environment Variables**
   Add these in Vercel Dashboard (Settings → Environment Variables):
   ```
   GEMINI_API_KEY=AIzaSyAjLAYYhocxG8jrWAw_aY4xa8_yE303MOk
   MONGODB_URI=mongodb://manoj:manoj28@atlas-sql-694288270ca3172bbde45a59-ytslre.a.query.mongodb.net/myVirtualDatabase?ssl=true&authSource=admin
   MONGODB_DB=myVirtualDatabase
   FLASK_ENV=production
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete
   - Your app will be live at `https://your-project.vercel.app`

### Option 2: Deploy via CLI

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy from Project Directory**
   ```bash
   cd d:\smartfarming\smartfarming
   vercel
   ```

4. **Follow the prompts:**
   - Set up and deploy? **Y**
   - Which scope? (Select your account)
   - Link to existing project? **N**
   - What's your project's name? **smartfarming**
   - In which directory is your code located? **./

5. **Add Environment Variables**
   ```bash
   vercel env add GEMINI_API_KEY
   vercel env add MONGODB_URI
   vercel env add MONGODB_DB
   vercel env add FLASK_ENV
   ```

6. **Deploy to Production**
   ```bash
   vercel --prod
   ```

## Important Notes

### File Storage Limitations
- Vercel is **serverless** - file uploads won't persist between requests
- Consider using:
  - **Cloudinary** for image uploads
  - **AWS S3** for file storage
  - **Vercel Blob** for file storage

### Database
- MongoDB Atlas connection is configured
- File-based storage won't work in production (serverless environment)
- Ensure MongoDB has full CRUD access (not just SQL read-only endpoint)

### Static Files
- Static files in `/static` folder will be served automatically
- ML models in `/models` and `/ml_models` will be included

### Cold Starts
- First request may be slow (cold start)
- Subsequent requests will be faster

## Troubleshooting

### Issue: Application Error
- Check Vercel logs: Dashboard → Project → Deployments → View Function Logs
- Verify all environment variables are set

### Issue: Module Not Found
- Ensure `requirements.txt` includes all dependencies
- Check if specific versions cause issues on Vercel

### Issue: File Upload Fails
- Implement cloud storage (Cloudinary/S3)
- Update upload routes to use cloud storage API

### Issue: ML Model Loading Fails
- Models might be too large for serverless
- Consider:
  - Using smaller models
  - Loading models from external storage
  - Using Vercel Pro for larger function sizes

## Post-Deployment Checklist

- [ ] Test all routes and features
- [ ] Verify database connectivity
- [ ] Check chatbot functionality
- [ ] Test crop prediction
- [ ] Verify disease detection
- [ ] Test fertilizer recommendation
- [ ] Check authentication flow
- [ ] Monitor Vercel logs for errors

## Custom Domain (Optional)

1. Go to Project Settings → Domains
2. Add your custom domain
3. Configure DNS settings as instructed
4. Wait for SSL certificate provisioning

## Continuous Deployment

- Any push to your main branch will trigger automatic deployment
- Use branches for testing before merging to main

## Cost

- **Hobby (Free)**: 
  - 100GB bandwidth/month
  - Serverless Function Execution: 100GB-Hours
  - Good for development and small projects

- **Pro**: 
  - Unlimited bandwidth
  - More function execution time
  - Larger function size limits

## Next Steps

1. Deploy to Vercel
2. Test thoroughly
3. Set up custom domain (optional)
4. Monitor usage and logs
5. Consider upgrading storage solution for production

---

**Deployment Status**: Ready to deploy
**Last Updated**: December 19, 2025
