# 🚀 PyTrends API - Deployment Guide for cPanel

## 📋 Prerequisites

- cPanel hosting account with Python support
- SSH access (optional but recommended)
- Python 3.8 or higher
- At least 512MB RAM

---

## 🔧 Step-by-Step Deployment

### 1. **Create Python Application in cPanel**

1. Log into your cPanel account
2. Navigate to **"Setup Python App"** (under Software section)
3. Click **"Create Application"**
4. Configure the application:
   - **Python version**: Select 3.8 or higher
   - **Application root**: `/home/YOUR_USERNAME/pytrends_api`
   - **Application URL**: Choose your desired subdomain or path
   - **Application startup file**: `passenger_wsgi.py`
   - **Application Entry point**: `application`

5. Click **"Create"** and wait for the environment to be created

### 2. **Upload Files to cPanel**

Upload these files to `/home/YOUR_USERNAME/pytrends_api/`:

```
pytrends_api/
├── pytrends_api.py          # Main API application
├── cache_manager.py          # Caching system
├── passenger_wsgi.py         # WSGI entry point
├── requirements.txt          # Python dependencies
├── .htaccess                 # Apache configuration
└── logs/                     # Create this directory
```

**Methods to upload:**
- **File Manager**: Use cPanel File Manager
- **FTP**: Use FileZilla or any FTP client
- **SSH**: Use `scp` or `rsync`

### 3. **Configure Environment Variables**

#### **Option A: Via .htaccess (Recommended)**

Edit `.htaccess` and update:

```apache
# Replace USERNAME with your cPanel username
PassengerAppRoot /home/USERNAME/pytrends_api
PassengerPython /home/USERNAME/virtualenv/pytrends_api/3.8/bin/python3

# IMPORTANT: Generate a secure API key
SetEnv API_SECRET_KEY "YOUR-SECURE-KEY-HERE-MIN-32-CHARS"
```

#### **Option B: Via passenger_wsgi.py**

Edit `passenger_wsgi.py` and update:

```python
# Line 15: Update with your cPanel username
CPANEL_USERNAME = "your_actual_username"

# Line 38: Set your secure API key
os.environ['API_SECRET_KEY'] = 'your-secure-key-here'
```

#### **Generate Secure API Key:**

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. **Install Dependencies**

#### **Via cPanel Terminal (Recommended)**

1. Go to **Terminal** in cPanel
2. Activate virtual environment:

```bash
source ~/virtualenv/pytrends_api/3.8/bin/activate
cd ~/pytrends_api
pip install -r requirements.txt
```

#### **Via SSH**

```bash
ssh your_username@your_domain.com
source ~/virtualenv/pytrends_api/3.8/bin/activate
cd ~/pytrends_api
pip install -r requirements.txt
```

### 5. **Create Logs Directory**

```bash
mkdir -p ~/pytrends_api/logs
chmod 755 ~/pytrends_api/logs
```

### 6. **Set Proper Permissions**

```bash
cd ~/pytrends_api
chmod 644 *.py
chmod 644 requirements.txt
chmod 644 .htaccess
chmod 755 logs
```

### 7. **Restart the Application**

#### **Method 1: Via cPanel**
1. Go to **"Setup Python App"**
2. Find your application
3. Click **"Restart"** button

#### **Method 2: Via Terminal/SSH**
```bash
touch ~/pytrends_api/tmp/restart.txt
```

### 8. **Verify Installation**

Visit your API URL in a browser:

```
https://yourdomain.com/your-app-path/
```

You should see:

```json
{
  "service": "Google Trends API - Comprehensive Edition",
  "version": "2.0.0",
  "status": "active",
  ...
}
```

---

## 🧪 Testing Your API

### Test Health Endpoint

```bash
curl https://yourdomain.com/your-app-path/health
```

### Test with API Key

```bash
curl -X POST https://yourdomain.com/your-app-path/api/related-queries \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"keyword": "python programming", "timeframe": "today 12-m", "geo": ""}'
```

### Test Comprehensive Research Endpoint

```bash
curl -X POST https://yourdomain.com/your-app-path/api/research \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "keywords": ["AI", "machine learning"],
    "timeframe": "today 12-m",
    "geo": "US",
    "include_related": true,
    "include_regional": true,
    "include_trending": false
  }'
```

---

## 📚 All Available Endpoints

### **Health & Info**
- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Swagger documentation

### **Core Endpoints**
- `POST /api/interest-over-time` - Historical trend data
- `POST /api/interest-by-region` - Geographic breakdown
- `POST /api/related-queries` - Related search queries
- `POST /api/related-topics` - Related topics
- `POST /api/trending-searches` - Daily trending searches
- `GET /api/today-searches` - Today's trending searches
- `GET /api/realtime-trending` - Realtime trending data
- `POST /api/suggestions` - Keyword suggestions
- `GET /api/categories` - Available categories

### **AI Blog Writer Optimized**
- `POST /api/research` - **Comprehensive research endpoint** (ALL data in one request)

### **Cache Management**
- `GET /api/cache/stats` - Cache statistics
- `POST /api/cache/clear` - Clear all cache

---

## 🔐 Security Best Practices

### 1. **Secure API Key**
- Never use default API key
- Use 32+ character random string
- Store in environment variables, not in code
- Rotate keys periodically

### 2. **Enable HTTPS**
- Uncomment HTTPS enforcement in `.htaccess`:
```apache
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```

### 3. **Configure CORS**
- Update CORS origins in `.htaccess` to allow only your Laravel domain:
```apache
Header always set Access-Control-Allow-Origin "https://yourlaravelapp.com"
```

### 4. **Protect Sensitive Files**
- `.htaccess` already denies access to:
  - `passenger_wsgi.py`
  - `requirements.txt`
  - `.log` files

### 5. **Monitor Logs**
- Check logs regularly: `~/pytrends_api/logs/pytrends_api.log`
- Set up log rotation (already configured in code)

---

## 🚀 Performance Optimization

### 1. **Caching (Already Enabled)**
- In-memory caching works out of the box
- Default TTL: 1 hour for most requests
- Trending data: 30 minutes TTL

### 2. **Optional: Enable Redis**
Set environment variable:
```apache
SetEnv REDIS_URL "redis://localhost:6379/0"
```

### 3. **Monitor Cache Performance**
```bash
curl -H "X-API-Key: YOUR_KEY" https://yourdomain.com/your-app-path/api/cache/stats
```

---

## 🔄 Updating the Application

### 1. **Update Code Files**
1. Upload new files via FTP/File Manager
2. Restart application:
```bash
touch ~/pytrends_api/tmp/restart.txt
```

### 2. **Update Dependencies**
```bash
source ~/virtualenv/pytrends_api/3.8/bin/activate
cd ~/pytrends_api
pip install -r requirements.txt --upgrade
touch ~/pytrends_api/tmp/restart.txt
```

### 3. **Clear Cache After Updates**
```bash
curl -X POST -H "X-API-Key: YOUR_KEY" \
  https://yourdomain.com/your-app-path/api/cache/clear
```

---

## 🐛 Troubleshooting

### **Application Not Starting**

1. **Check Python version:**
```bash
source ~/virtualenv/pytrends_api/3.8/bin/activate
python --version
```

2. **Check error logs:**
```bash
tail -100 ~/pytrends_api/logs/pytrends_api.log
```

3. **Check cPanel error logs:**
- cPanel → Metrics → Errors

4. **Verify file permissions:**
```bash
ls -la ~/pytrends_api/
```

### **Dependencies Installation Fails**

```bash
# Use specific pip version
source ~/virtualenv/pytrends_api/3.8/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### **API Returns 500 Errors**

1. Check logs: `~/pytrends_api/logs/pytrends_api.log`
2. Verify API key is set correctly
3. Test imports:
```bash
source ~/virtualenv/pytrends_api/3.8/bin/activate
python -c "from pytrends.request import TrendReq; print('OK')"
```

### **Rate Limiting Issues**

Google Trends may rate limit requests. Solutions:
- Enable caching (already enabled)
- Reduce request frequency
- Use longer cache TTL
- Implement request queuing in your Laravel app

### **Memory Issues**

If you encounter memory errors:
1. Reduce concurrent requests
2. Enable Redis for distributed caching
3. Contact hosting provider for RAM upgrade

---

## 📊 Laravel Integration Example

### **Laravel HTTP Client Usage**

```php
<?php

use Illuminate\Support\Facades\Http;

class GoogleTrendsService
{
    private $apiUrl;
    private $apiKey;

    public function __construct()
    {
        $this->apiUrl = config('services.pytrends.url');
        $this->apiKey = config('services.pytrends.key');
    }

    /**
     * Get comprehensive research data for AI blog writer
     */
    public function comprehensiveResearch(array $keywords, string $timeframe = 'today 12-m', string $geo = 'US')
    {
        $response = Http::withHeaders([
            'X-API-Key' => $this->apiKey,
            'Content-Type' => 'application/json',
        ])->post($this->apiUrl . '/api/research', [
            'keywords' => $keywords,
            'timeframe' => $timeframe,
            'geo' => $geo,
            'include_related' => true,
            'include_regional' => true,
            'include_trending' => false,
        ]);

        if ($response->successful()) {
            return $response->json();
        }

        throw new \Exception('Failed to fetch trends data: ' . $response->body());
    }

    /**
     * Get related queries for a keyword
     */
    public function getRelatedQueries(string $keyword, string $timeframe = 'today 12-m')
    {
        $response = Http::withHeaders([
            'X-API-Key' => $this->apiKey,
        ])->post($this->apiUrl . '/api/related-queries', [
            'keyword' => $keyword,
            'timeframe' => $timeframe,
            'geo' => '',
        ]);

        return $response->json();
    }
}
```

### **Config File (config/services.php)**

```php
'pytrends' => [
    'url' => env('PYTRENDS_API_URL', 'https://yourdomain.com/pytrends'),
    'key' => env('PYTRENDS_API_KEY'),
],
```

### **.env File**

```env
PYTRENDS_API_URL=https://yourdomain.com/pytrends
PYTRENDS_API_KEY=your-secure-api-key-here
```

---

## 📈 Monitoring & Maintenance

### **Daily Checks**
- Monitor error logs
- Check cache hit rate
- Verify API response times

### **Weekly Checks**
- Review access logs
- Check disk space
- Analyze most requested endpoints

### **Monthly Maintenance**
- Update dependencies
- Rotate API keys if needed
- Review and optimize cache TTL values

---

## 🆘 Support & Resources

### **Documentation**
- PyTrends GitHub: https://github.com/GeneralMills/pytrends
- FastAPI Docs: https://fastapi.tiangolo.com
- API Swagger Docs: `https://yourdomain.com/your-app-path/docs`

### **Common Issues**
- **429 Too Many Requests**: Google is rate limiting → Enable caching, reduce frequency
- **Connection Timeout**: Increase timeout in `get_pytrends_client()`
- **Empty Results**: Keyword may have no data → Try different timeframe/geo

---

## ✅ Post-Deployment Checklist

- [ ] API accessible via browser
- [ ] Health endpoint returns "healthy"
- [ ] API key authentication works
- [ ] Test all major endpoints
- [ ] HTTPS enabled and enforced
- [ ] Logs directory writable
- [ ] Cache working (check stats endpoint)
- [ ] Laravel integration tested
- [ ] Error handling verified
- [ ] Documentation accessible

---

**🎉 Congratulations! Your PyTrends API is now deployed and ready for your AI blog writer!**

For issues or questions, check the logs first, then review this guide.
