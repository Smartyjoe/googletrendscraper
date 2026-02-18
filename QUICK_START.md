# 🚀 Quick Start Guide - PyTrends API

The fastest way to get your PyTrends API running locally!

---

## ⚡ **Super Quick Start (3 Steps)**

### **Step 1: Start the Server**

Open PowerShell in your project directory and run:

```powershell
.\start_server.ps1
```

That's it! The script will:
- ✅ Create virtual environment (if needed)
- ✅ Install all dependencies
- ✅ Set test API key
- ✅ Start the server

**Wait for:** `Uvicorn running on http://127.0.0.1:8000`

---

### **Step 2: Test the API**

Open a **NEW PowerShell window** and run:

```powershell
.\test_api.ps1
```

This will automatically test all endpoints and show results!

---

### **Step 3: Use the API**

**Option A: Browser (Interactive)**
```
http://localhost:8000/docs
```
Click "Try it out" on any endpoint!

**Option B: PowerShell (Programmatic)**
```powershell
$headers = @{ "X-API-Key" = "test-secret-key-for-local-development-12345" }
$body = @{ keyword = "AI"; timeframe = "today 3-m" } | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/related-queries" `
  -Headers $headers -Body $body | ConvertTo-Json -Depth 10
```

---

## 📖 **Manual Start (If Scripts Don't Work)**

### **Windows PowerShell:**
```powershell
# 1. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 2. Set API key
$env:API_SECRET_KEY = "test-secret-key-for-local-development-12345"

# 3. Start server
python pytrends_api.py
```

### **Windows CMD:**
```cmd
# 1. Activate virtual environment
venv\Scripts\activate.bat

# 2. Set API key
set API_SECRET_KEY=test-secret-key-for-local-development-12345

# 3. Start server
python pytrends_api.py
```

### **macOS/Linux:**
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Set API key
export API_SECRET_KEY="test-secret-key-for-local-development-12345"

# 3. Start server
python pytrends_api.py
```

---

## ✅ **Verify It's Working**

Open browser: http://localhost:8000/health

You should see:
```json
{
  "status": "healthy",
  "version": "2.0.0"
}
```

✅ **If you see this, you're ready to go!**

---

## 🎯 **Quick Test Examples**

### **1. Get Related Queries**
```powershell
$headers = @{ "X-API-Key" = "test-secret-key-for-local-development-12345" }
$body = @{ keyword = "chatgpt" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/related-queries" -Headers $headers -Body $body
```

### **2. Get Trending Topics**
```powershell
$headers = @{ "X-API-Key" = "test-secret-key-for-local-development-12345" }
$body = @{ geo = "US" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/trending" -Headers $headers -Body $body
```

### **3. Comprehensive Research (For AI Blog Writer)**
```powershell
$headers = @{ "X-API-Key" = "test-secret-key-for-local-development-12345" }
$body = @{
    keywords = @("AI", "machine learning")
    timeframe = "today 3-m"
    geo = "US"
    include_interest_over_time = $true
    include_related_queries = $true
    include_suggestions = $true
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/research" -Headers $headers -Body $body
```

---

## 📚 **Next Steps**

### **For Testing:**
- 📖 See [LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md) for comprehensive testing
- 🔍 Use http://localhost:8000/docs for interactive API exploration

### **For Development:**
- 📖 See [README.md](README.md) for all endpoint documentation
- 🔍 See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for code examples

### **For Deployment:**
- 📖 See [DEPLOYMENT.md](DEPLOYMENT.md) for cPanel deployment guide
- 🔒 Generate secure API key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

---

## 🐛 **Common Issues**

### **"Cannot activate virtual environment"**
**Solution:**
```powershell
# Recreate it
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### **"Module not found" errors**
**Solution:**
```powershell
# Make sure virtual env is activated (you see "(venv)" in prompt)
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### **"urllib3 compatibility error"**
**Solution:**
```powershell
pip install 'urllib3<2.0' 'requests<2.32'
```

### **"401 Unauthorized"**
**Solution:** Make sure you're sending the `X-API-Key` header with the correct key

---

## 💡 **Pro Tips**

1. **Keep server running** in one terminal, test in another
2. **Use /docs** for easy interactive testing
3. **Check cache** - 2nd request should be much faster
4. **Monitor logs** - server shows cache hits and errors
5. **Test different keywords** - popular ones work best

---

## 🎉 **You're Ready!**

When all tests pass, you're ready to:
1. 🚀 Deploy to cPanel
2. 🔗 Integrate with Laravel
3. ✍️ Build your AI blog writer

**Happy coding!** 🎯