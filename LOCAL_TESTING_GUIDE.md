# 🧪 Local Testing Guide - PyTrends API

Complete step-by-step guide to test your PyTrends API locally before deploying to cPanel.

---

## 📋 **Prerequisites**

- ✅ Python 3.8+ installed
- ✅ All project files in your directory
- ✅ Internet connection (for Google Trends data)

---

## 🚀 **Step-by-Step Testing Process**

### **Step 1: Activate Virtual Environment**

#### **On Windows (PowerShell):**
```powershell
# Navigate to your project directory
cd path\to\your\project

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# You should see (venv) in your prompt
```

#### **On Windows (Command Prompt):**
```cmd
# Navigate to your project directory
cd path\to\your\project

# Activate virtual environment
venv\Scripts\activate.bat

# You should see (venv) in your prompt
```

#### **On macOS/Linux:**
```bash
# Navigate to your project directory
cd path/to/your/project

# Activate virtual environment
source venv/bin/activate

# You should see (venv) in your prompt
```

**✅ Success Indicator:** Your terminal prompt should show `(venv)` at the beginning.

---

### **Step 2: Install/Verify Dependencies**

```powershell
# Make sure virtual environment is activated (you see (venv))

# Install all dependencies
pip install -r requirements.txt

# Verify key packages are installed
pip list | Select-String -Pattern "fastapi|pytrends|uvicorn"
```

**Expected Output:**
```
fastapi                      0.109.2
pytrends                     4.9.2
uvicorn                      0.27.1
```

---

### **Step 3: Set API Secret Key (Security)**

#### **Option A: Using Environment Variable (Recommended for Testing)**

**Windows PowerShell:**
```powershell
$env:API_SECRET_KEY = "test-secret-key-for-local-development-12345"
```

**Windows CMD:**
```cmd
set API_SECRET_KEY=test-secret-key-for-local-development-12345
```

**macOS/Linux:**
```bash
export API_SECRET_KEY="test-secret-key-for-local-development-12345"
```

#### **Option B: Create .env File (Recommended for Development)**

Create a file named `.env` in your project root:
```env
API_SECRET_KEY=test-secret-key-for-local-development-12345
```

---

### **Step 4: Start the API Server**

```powershell
# Make sure virtual environment is activated and you're in project directory

# Start the server
python pytrends_api.py
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**✅ Success Indicator:** You see "Uvicorn running on http://127.0.0.1:8000"

---

### **Step 5: Test the API**

Keep the server running in one terminal, open a **NEW terminal/PowerShell window** for testing.

---

#### **Test 1: Health Check (No Authentication Required)**

**Windows PowerShell:**
```powershell
curl http://localhost:8000/health | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Windows CMD / macOS / Linux:**
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2024-02-18T10:30:00Z",
  "cache": {
    "type": "in-memory",
    "status": "active"
  }
}
```

✅ **If you see this, your API is running!**

---

#### **Test 2: API Root/Documentation (No Authentication Required)**

**Open in Browser:**
```
http://localhost:8000/
```

**Or via command line:**
```powershell
curl http://localhost:8000/
```

**Expected Response:**
```json
{
  "message": "Google Trends API",
  "version": "2.0.0",
  "documentation": "/docs",
  "endpoints": {
    "health": "/health",
    "interest_over_time": "/api/interest-over-time",
    "related_queries": "/api/related-queries",
    "comprehensive": "/api/research"
  }
}
```

---

#### **Test 3: Interactive API Documentation**

**Open in Browser:**
```
http://localhost:8000/docs
```

This opens **Swagger UI** where you can:
- See all endpoints
- Test them interactively
- See request/response examples

---

#### **Test 4: Test Related Queries Endpoint (Requires Authentication)**

**Windows PowerShell:**
```powershell
$headers = @{
    "X-API-Key" = "test-secret-key-for-local-development-12345"
    "Content-Type" = "application/json"
}

$body = @{
    keyword = "artificial intelligence"
    timeframe = "today 3-m"
    geo = ""
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/related-queries" -Headers $headers -Body $body | ConvertTo-Json -Depth 10
```

**Windows CMD / macOS / Linux (using curl):**
```bash
curl -X POST "http://localhost:8000/api/related-queries" \
  -H "X-API-Key: test-secret-key-for-local-development-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "artificial intelligence",
    "timeframe": "today 3-m",
    "geo": ""
  }'
```

**Expected Response:**
```json
{
  "keyword": "artificial intelligence",
  "timeframe": "today 3-m",
  "geo": "worldwide",
  "top": [
    {
      "query": "generative ai",
      "value": 100
    },
    {
      "query": "chatgpt",
      "value": 85
    }
  ],
  "rising": [
    {
      "query": "ai tools 2024",
      "value": 450
    }
  ],
  "cached": false,
  "timestamp": "2024-02-18T10:35:00Z"
}
```

✅ **If you see real data, Google Trends integration is working!**

---

#### **Test 5: Test Interest Over Time**

**Windows PowerShell:**
```powershell
$headers = @{
    "X-API-Key" = "test-secret-key-for-local-development-12345"
    "Content-Type" = "application/json"
}

$body = @{
    keyword = "python programming"
    timeframe = "today 12-m"
    geo = ""
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/interest-over-time" -Headers $headers -Body $body | ConvertTo-Json -Depth 10
```

**Expected Response:**
```json
{
  "keyword": "python programming",
  "timeframe": "today 12-m",
  "data": [
    {
      "date": "2023-02-01",
      "value": 75
    },
    {
      "date": "2023-03-01",
      "value": 82
    }
  ],
  "isPartial": false,
  "cached": false
}
```

---

#### **Test 6: Test Comprehensive Research Endpoint (THE BIG ONE!)**

**Windows PowerShell:**
```powershell
$headers = @{
    "X-API-Key" = "test-secret-key-for-local-development-12345"
    "Content-Type" = "application/json"
}

$body = @{
    keywords = @("AI", "machine learning")
    timeframe = "today 3-m"
    geo = "US"
    include_interest_over_time = $true
    include_interest_by_region = $true
    include_related_queries = $true
    include_related_topics = $true
    include_trending = $false
    include_suggestions = $true
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/research" -Headers $headers -Body $body | ConvertTo-Json -Depth 10
```

**This returns comprehensive data for AI blog writing!**

---

#### **Test 7: Test Caching**

**Run the same request twice:**

```powershell
# First request (will fetch from Google)
$headers = @{ "X-API-Key" = "test-secret-key-for-local-development-12345" }
$body = @{ keyword = "blockchain"; timeframe = "today 1-m" } | ConvertTo-Json

# Time this
Measure-Command { 
    Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/related-queries" -Headers $headers -Body $body 
}

# Second request (should be MUCH faster from cache)
Measure-Command { 
    Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/related-queries" -Headers $headers -Body $body 
}
```

**Expected Results:**
- First request: 3-8 seconds
- Second request: <100ms (cached)

---

#### **Test 8: Test Different Countries**

```powershell
$headers = @{ "X-API-Key" = "test-secret-key-for-local-development-12345" }

# Test US
$body = @{ keyword = "pizza"; geo = "US" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/interest-by-region" -Headers $headers -Body $body

# Test UK
$body = @{ keyword = "football"; geo = "GB" } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/interest-by-region" -Headers $headers -Body $body
```

---

## 🎯 **Complete Test Checklist**

- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] API secret key set
- [ ] Server starts without errors
- [ ] Health check returns healthy status
- [ ] Root endpoint returns API info
- [ ] Swagger docs accessible at /docs
- [ ] Related queries returns real Google data
- [ ] Interest over time returns historical data
- [ ] Geographic data works for different countries
- [ ] Comprehensive research endpoint works
- [ ] Caching speeds up repeated requests
- [ ] Trending searches endpoint works
- [ ] Suggestions endpoint works

---

## 🐛 **Troubleshooting**

### **Problem: "Cannot activate virtual environment"**

**Solution:**
```powershell
# If activation fails, recreate the virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

---

### **Problem: "urllib3 compatibility error"**

**Solution:**
```powershell
# Downgrade to compatible versions
pip install 'urllib3<2.0' 'requests<2.32'
```

---

### **Problem: "401 Unauthorized"**

**Solution:**
- Make sure you're sending the `X-API-Key` header
- Make sure the key matches your environment variable
- Check: `echo $env:API_SECRET_KEY` (PowerShell) or `echo $API_SECRET_KEY` (bash)

---

### **Problem: "Too Many Requests" or rate limiting**

**Solution:**
- Google rate limits aggressive requests
- Wait 30-60 seconds between unique requests
- Use caching for repeated queries
- Don't test with too many different keywords rapidly

---

### **Problem: "No data returned" or empty results**

**Possible Causes:**
1. Keyword too specific/obscure
2. Geographic region has no data
3. Timeframe too narrow
4. Google Trends temporarily unavailable

**Solution:**
- Try popular keywords like "covid", "bitcoin", "python"
- Use broader timeframes like "today 12-m"
- Leave geo empty for worldwide data

---

## 📊 **Performance Benchmarks**

**Expected Response Times:**

| Endpoint | First Request | Cached Request |
|----------|--------------|----------------|
| Health Check | <10ms | <10ms |
| Related Queries | 3-8 seconds | <100ms |
| Interest Over Time | 3-8 seconds | <100ms |
| Geographic Data | 3-8 seconds | <100ms |
| Comprehensive Research | 8-15 seconds | <200ms |
| Trending Searches | 2-5 seconds | <100ms |

---

## ✅ **Ready for Production?**

If all tests pass, you're ready to deploy! Check these final items:

- [ ] All endpoints return real data
- [ ] Caching works (2nd request is fast)
- [ ] Error handling works (try invalid keywords)
- [ ] Different countries/timeframes work
- [ ] No console errors or warnings
- [ ] API responds quickly to cached requests
- [ ] Comprehensive endpoint returns complete data

**Once all checked, you're ready for cPanel deployment!**

---

## 🚀 **Next Steps**

1. **Test Complete?** → Follow [DEPLOYMENT.md](DEPLOYMENT.md) for cPanel setup
2. **Found Issues?** → Check troubleshooting section above
3. **Want More Features?** → Check [README.md](README.md) for all endpoints
4. **Ready to Integrate?** → Use examples in [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

---

## 💡 **Pro Tips**

1. **Keep one terminal open** with the server running during all tests
2. **Use the /docs interface** at http://localhost:8000/docs for easier testing
3. **Test caching** by running the same request twice - should be MUCH faster
4. **Try different keywords** to see various types of results
5. **Monitor the server logs** - they show caching behavior and errors
6. **Test error scenarios** - try invalid API keys, missing parameters, etc.

---

**Happy Testing! 🎉**

Your API is production-ready when all tests pass!