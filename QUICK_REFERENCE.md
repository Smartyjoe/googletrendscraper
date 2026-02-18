# 🚀 Quick Reference Guide - PyTrends API

## 📋 Table of Contents
- [Installation](#installation)
- [API Endpoints](#api-endpoints)
- [Request Examples](#request-examples)
- [Laravel Integration](#laravel-integration)
- [Common Timeframes](#common-timeframes)
- [Country Codes](#country-codes)
- [Troubleshooting](#troubleshooting)

---

## 🔧 Installation

### **Local Development**
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API key
export API_SECRET_KEY="your-secure-key-here"

# 3. Run server
python pytrends_api.py

# API runs at: http://localhost:8000
```

### **cPanel Deployment**
See [DEPLOYMENT.md](DEPLOYMENT.md) for complete guide.

---

## 📡 API Endpoints

### **🎯 Recommended for AI Blog Writer**

```http
POST /api/research
```
**Returns:** Everything in one request - interest over time, related queries, related topics, regional data, and trending searches.

### **📊 Individual Data Endpoints**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/interest-over-time` | POST | Historical trend data |
| `/api/interest-by-region` | POST | Geographic breakdown |
| `/api/related-queries` | POST | Related search queries |
| `/api/related-topics` | POST | Related topics |
| `/api/trending-searches` | POST | Daily trending searches |
| `/api/today-searches` | GET | Today's trending |
| `/api/realtime-trending` | GET | Realtime trends |
| `/api/suggestions` | POST | Keyword suggestions |
| `/api/categories` | GET | Available categories |

### **🔧 Utility Endpoints**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check (no auth) |
| `/` | GET | API info (no auth) |
| `/docs` | GET | Swagger UI (no auth) |
| `/api/cache/stats` | GET | Cache statistics |
| `/api/cache/clear` | POST | Clear cache |

---

## 📝 Request Examples

### **1. Comprehensive Research (AI Optimized)**

```bash
curl -X POST http://localhost:8000/api/research \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["artificial intelligence", "machine learning"],
    "timeframe": "today 12-m",
    "geo": "US",
    "include_related": true,
    "include_regional": true,
    "include_trending": false
  }'
```

**Returns:**
```json
{
  "success": true,
  "keywords": ["artificial intelligence", "machine learning"],
  "timeframe": "today 12-m",
  "geo": "US",
  "interest_over_time": [...],
  "related_data": {
    "artificial intelligence": {
      "queries": {"rising": [...], "top": [...]},
      "topics": {"rising": [...], "top": [...]}
    },
    "machine learning": {...}
  },
  "interest_by_region": [...],
  "timestamp": "2024-02-18T10:00:00Z"
}
```

### **2. Related Queries**

```bash
curl -X POST http://localhost:8000/api/related-queries \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "python programming",
    "timeframe": "today 12-m",
    "geo": ""
  }'
```

### **3. Interest Over Time**

```bash
curl -X POST http://localhost:8000/api/interest-over-time \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["python", "javascript", "java"],
    "timeframe": "today 5-y",
    "geo": "",
    "gprop": ""
  }'
```

### **4. Trending Searches**

```bash
curl -X POST http://localhost:8000/api/trending-searches \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "pn": "united_states"
  }'
```

### **5. Geographic Interest**

```bash
curl -X POST http://localhost:8000/api/interest-by-region \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["bitcoin"],
    "timeframe": "today 12-m",
    "geo": "",
    "resolution": "COUNTRY",
    "inc_low_vol": true
  }'
```

### **6. Keyword Suggestions**

```bash
curl -X POST http://localhost:8000/api/suggestions \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "SEO"
  }'
```

### **7. Health Check (No Auth)**

```bash
curl http://localhost:8000/health
```

### **8. Cache Statistics**

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/api/cache/stats
```

---

## 🔗 Laravel Integration

### **Step 1: Configure Laravel**

**config/services.php:**
```php
'pytrends' => [
    'url' => env('PYTRENDS_API_URL'),
    'key' => env('PYTRENDS_API_KEY'),
],
```

**.env:**
```
PYTRENDS_API_URL=https://yourdomain.com/pytrends
PYTRENDS_API_KEY=your-secure-api-key
```

### **Step 2: Create Service Class**

**app/Services/GoogleTrendsService.php:**
```php
<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Cache;

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
     * Comprehensive research for AI blog writer
     */
    public function research(array $keywords, string $timeframe = 'today 12-m', string $geo = 'US')
    {
        $cacheKey = "trends_research_" . md5(json_encode($keywords) . $timeframe . $geo);
        
        return Cache::remember($cacheKey, 3600, function() use ($keywords, $timeframe, $geo) {
            $response = Http::withHeaders([
                'X-API-Key' => $this->apiKey,
            ])->timeout(30)->post($this->apiUrl . '/api/research', [
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

            throw new \Exception('Trends API error: ' . $response->body());
        });
    }

    /**
     * Get related queries only
     */
    public function relatedQueries(string $keyword, string $timeframe = 'today 12-m')
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

    /**
     * Get trending searches
     */
    public function trending(string $country = 'united_states')
    {
        $response = Http::withHeaders([
            'X-API-Key' => $this->apiKey,
        ])->post($this->apiUrl . '/api/trending-searches', [
            'pn' => $country,
        ]);

        return $response->json();
    }
}
```

### **Step 3: Use in Controller**

**app/Http/Controllers/BlogController.php:**
```php
<?php

namespace App\Http\Controllers;

use App\Services\GoogleTrendsService;
use Illuminate\Http\Request;

class BlogController extends Controller
{
    protected $trends;

    public function __construct(GoogleTrendsService $trends)
    {
        $this->trends = $trends;
    }

    public function researchTopic(Request $request)
    {
        $keywords = $request->input('keywords', []);
        
        // Get comprehensive data
        $data = $this->trends->research($keywords);
        
        // Extract insights for AI
        $insights = [
            'main_keyword' => $keywords[0],
            'rising_queries' => $data['related_data'][$keywords[0]]['queries']['rising'] ?? [],
            'top_queries' => $data['related_data'][$keywords[0]]['queries']['top'] ?? [],
            'trend_data' => $data['interest_over_time'] ?? [],
            'top_regions' => array_slice($data['interest_by_region'] ?? [], 0, 10),
        ];
        
        return response()->json($insights);
    }

    public function getTrending()
    {
        $trending = $this->trends->trending('united_states');
        
        return response()->json($trending);
    }
}
```

### **Step 4: Register Service Provider (Optional)**

**app/Providers/AppServiceProvider.php:**
```php
public function register()
{
    $this->app->singleton(GoogleTrendsService::class, function ($app) {
        return new GoogleTrendsService();
    });
}
```

### **Step 5: Create Routes**

**routes/api.php:**
```php
use App\Http\Controllers\BlogController;

Route::post('/blog/research', [BlogController::class, 'researchTopic']);
Route::get('/blog/trending', [BlogController::class, 'getTrending']);
```

### **Step 6: Use in Blade/Vue**

```javascript
// JavaScript example
async function researchTopic(keywords) {
    const response = await fetch('/api/blog/research', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify({ keywords })
    });
    
    const data = await response.json();
    console.log('Rising queries:', data.rising_queries);
    console.log('Trend data:', data.trend_data);
}
```

---

## 📅 Common Timeframes

| Timeframe | Description |
|-----------|-------------|
| `now 1-H` | Last 1 hour |
| `now 4-H` | Last 4 hours |
| `now 1-d` | Last 24 hours |
| `now 7-d` | Last 7 days |
| `today 1-m` | Past 30 days |
| `today 3-m` | Past 90 days |
| `today 12-m` | Past 12 months (default) |
| `today 5-y` | Past 5 years |
| `all` | 2004-present |

**Custom Range:**
```
"2024-01-01 2024-12-31"  // Specific date range
```

---

## 🌍 Country Codes

| Code | Country |
|------|---------|
| `""` | Worldwide |
| `US` | United States |
| `GB` | United Kingdom |
| `CA` | Canada |
| `AU` | Australia |
| `IN` | India |
| `JP` | Japan |
| `DE` | Germany |
| `FR` | France |
| `BR` | Brazil |
| `IT` | Italy |
| `ES` | Spain |
| `MX` | Mexico |
| `KR` | South Korea |
| `NL` | Netherlands |

**Full list:** Use ISO 3166-1 alpha-2 codes

**For trending searches, use country names:**
- `united_states`
- `united_kingdom`
- `japan`
- `india`
- etc.

---

## 🐛 Troubleshooting

### **1. "Missing API key" Error**

**Problem:** Request missing `X-API-Key` header

**Solution:**
```bash
# Always include header
curl -H "X-API-Key: YOUR_KEY" ...
```

### **2. "429 Too Many Requests"**

**Problem:** Google Trends rate limiting

**Solution:**
- Check cache is working: `/api/cache/stats`
- Reduce request frequency
- Use longer cache TTL
- Wait before retrying

### **3. Empty Results**

**Problem:** Keyword has no data

**Solution:**
- Try different timeframe (`today 12-m` instead of `now 7-d`)
- Try broader geo (worldwide `""` instead of specific country)
- Check keyword spelling
- Use more popular keywords

### **4. "Connection Timeout"**

**Problem:** Google Trends slow/unavailable

**Solution:**
- Retry the request
- Check internet connection
- Google may be temporarily down

### **5. "urllib3 compatibility error"**

**Problem:** Wrong package versions

**Solution:**
```bash
pip install 'urllib3<2.0' 'requests<2.32'
```

### **6. Cache Not Working**

**Problem:** Same requests hitting Google multiple times

**Check:**
```bash
curl -H "X-API-Key: YOUR_KEY" http://localhost:8000/api/cache/stats
```

**Solution:**
- Check `cache_stats.memory.active_entries > 0`
- Verify requests have identical parameters
- Clear cache and retry

### **7. Laravel Connection Issues**

**Problem:** Laravel can't reach API

**Check:**
1. API is running: `curl http://your-api.com/health`
2. API key is correct in `.env`
3. URL is correct (no trailing slash)
4. CORS is configured for your Laravel domain

### **8. Server Returns 500 Error**

**Check Logs:**
```bash
tail -f ~/pytrends_api/logs/pytrends_api.log
```

**Common Causes:**
- Missing dependencies
- API key not set
- File permission issues
- Python version incompatibility

---

## 📊 Response Time Expectations

| Scenario | Response Time |
|----------|---------------|
| Cached data | < 100ms |
| Fresh data (Google) | 3-8 seconds |
| Comprehensive research (uncached) | 10-15 seconds |
| Comprehensive research (cached) | < 200ms |

**Tip:** First request is slow, subsequent requests are fast (cached)

---

## 💡 Pro Tips

### **1. Use Comprehensive Endpoint**
Instead of 5 separate requests, use `/api/research` once:
```javascript
// ❌ Bad: 5 requests
const interest = await fetch('/api/interest-over-time');
const queries = await fetch('/api/related-queries');
const topics = await fetch('/api/related-topics');
const regions = await fetch('/api/interest-by-region');
const trending = await fetch('/api/trending-searches');

// ✅ Good: 1 request
const allData = await fetch('/api/research');
```

### **2. Cache in Laravel Too**
```php
// Cache for 1 hour in Laravel
$data = Cache::remember('trends_' . $keyword, 3600, function() {
    return $this->trends->research([$keyword]);
});
```

### **3. Handle Errors Gracefully**
```php
try {
    $data = $this->trends->research($keywords);
} catch (\Exception $e) {
    Log::error('Trends API error: ' . $e->getMessage());
    return $this->fallbackData(); // Use cached/default data
}
```

### **4. Monitor Cache Hit Rate**
```bash
# Check regularly
curl -H "X-API-Key: KEY" http://your-api.com/api/cache/stats

# Good hit rate: 60-80%
```

### **5. Use Appropriate Timeframes**
- Blog research: `today 12-m` or `today 5-y`
- Trending content: `now 7-d` or `today 1-m`
- Historical analysis: `today 5-y` or `all`

---

## 🎯 Quick Test Commands

### **Test API is Running**
```bash
curl http://localhost:8000/
```

### **Test Health**
```bash
curl http://localhost:8000/health
```

### **Test with Auth**
```bash
curl -H "X-API-Key: YOUR_SECRET_KEY_CHANGE_THIS" \
  http://localhost:8000/api/cache/stats
```

### **Test Comprehensive Endpoint**
```bash
curl -X POST http://localhost:8000/api/research \
  -H "X-API-Key: YOUR_SECRET_KEY_CHANGE_THIS" \
  -H "Content-Type: application/json" \
  -d '{"keywords":["AI"],"timeframe":"today 12-m","geo":"US","include_related":true,"include_regional":true}'
```

---

## 📞 Getting Help

1. **Check logs:** `logs/pytrends_api.log`
2. **View API docs:** `http://localhost:8000/docs`
3. **Read deployment guide:** [DEPLOYMENT.md](DEPLOYMENT.md)
4. **Review examples:** This file

---

**🎉 You're ready to use the PyTrends API!**

Start with `/api/research` endpoint - it's optimized for AI blog writing and gives you everything in one request.
