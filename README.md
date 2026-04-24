# 🔥 PyTrends API - Comprehensive Edition

**Production-ready Google Trends API for AI Blog Writers and Content Creators**

A fully-featured FastAPI wrapper for pytrends with intelligent caching, comprehensive research endpoints, and optimized for AI-powered content creation.

---

## ✨ Features

- ✅ **13+ Endpoints** - Complete coverage of Google Trends data
- ✅ **Intelligent Caching** - In-memory caching with optional Redis (works perfectly without Redis)
- ✅ **Comprehensive Research Endpoint** - Get ALL data in one request (optimized for AI)
- ✅ **Production Ready** - Error handling, logging, authentication, CORS
- ✅ **cPanel Compatible** - Easy deployment on shared hosting
- ✅ **Auto Documentation** - Swagger UI and ReDoc included
- ✅ **Laravel Ready** - Easy integration with PHP/Laravel apps

---

## 🚀 Quick Start

### **1. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **2. Set API Key**

```bash
export API_SECRET_KEY="your-secure-api-key-here"
```

Or edit `.htaccess` / `passenger_wsgi.py`

### **3. Run Locally**

```bash
python pytrends_api.py
```

API will be available at: `http://localhost:8000`

### **4. View Documentation**

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 📊 Available Endpoints

### **🎯 AI Blog Writer Optimized**

#### **Comprehensive Research** (Recommended for AI)
```http
POST /api/research
```

Get everything in one request: interest over time, related queries, related topics, regional data, and trending searches.

**Request:**
```json
{
  "keywords": ["artificial intelligence", "machine learning"],
  "timeframe": "today 12-m",
  "geo": "US",
  "include_related": true,
  "include_regional": true,
  "include_trending": false
}
```

**Response includes:**
- Historical trend data
- Rising & top related queries
- Rising & top related topics
- Geographic interest breakdown
- Current trending searches (optional)

Perfect for generating SEO-optimized, data-driven blog content!

---

### **📈 Individual Endpoints**

#### **1. Interest Over Time**
```http
POST /api/interest-over-time
```
Historical indexed data showing popularity trends over time.

#### **2. Interest by Region**
```http
POST /api/interest-by-region
```
Geographic breakdown of keyword popularity.

#### **3. Related Queries**
```http
POST /api/related-queries
```
Rising and top related search queries.

#### **4. Related Topics**
```http
POST /api/related-topics
```
Rising and top related topics.

#### **5. Trending Searches**
```http
POST /api/trending-searches
```
Daily trending searches for a specific country.

#### **6. Today's Searches**
```http
GET /api/today-searches?geo=US
```
Realtime trending topics for today.

#### **7. Realtime Trending**
```http
GET /api/realtime-trending?geo=US&category=all
```
Most current trending data available.

#### **8. Keyword Suggestions**
```http
POST /api/suggestions
```
Keyword expansion suggestions from Google.

#### **9. Categories**
```http
GET /api/categories
```
All available Google Trends categories.

---

### **🔧 Utility Endpoints**

#### **Cache Statistics**
```http
GET /api/cache/stats
```

#### **Clear Cache**
```http
POST /api/cache/clear
```

#### **Health Check**
```http
GET /health
```

---

## 🔐 Authentication

All API endpoints (except `/`, `/health`, `/docs`) require API key authentication.

**Header:**
```
X-API-Key: your-secure-api-key-here
```

**Swagger UI testing:**
Open `/docs`, click **Authorize**, paste your API key as the value for `X-API-Key`, then run secured endpoints directly from Swagger.

**Example with curl:**
```bash
curl -X POST https://your-api.com/api/related-queries \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "python", "timeframe": "today 12-m"}'
```

---

## 💾 Caching System

### **How It Works**

1. **In-Memory (Primary)** - Fast, works out of the box, no setup required
2. **Redis (Optional)** - For distributed caching across multiple servers

### **Cache TTL (Time-to-Live)**

- **Trending/Realtime Data**: 30 minutes
- **Most Queries**: 1 hour
- **Historical/Categories**: 2-24 hours

### **Enable Redis (Optional)**

Set environment variable:
```bash
export REDIS_URL="redis://localhost:6379/0"
```

The API works perfectly **without Redis** using in-memory caching!

### **Monitor Cache**

```bash
curl -H "X-API-Key: YOUR_KEY" http://localhost:8000/api/cache/stats
```

---

## 🎨 Example Use Cases

### **1. AI Blog Research**

Use `/api/research` to gather all data for your AI to create:
- SEO-optimized blog posts
- Trending topic articles
- Data-driven content
- Regional content targeting

### **2. Keyword Research Tool**

Build a keyword research tool using:
- `/api/suggestions` - Keyword ideas
- `/api/related-queries` - Related searches
- `/api/interest-over-time` - Popularity trends

### **3. Trending Content Monitor**

Monitor trends using:
- `/api/trending-searches` - Daily trends
- `/api/today-searches` - Today's topics
- `/api/realtime-trending` - Realtime data

### **4. SEO Analysis**

Analyze keywords with:
- `/api/interest-over-time` - Historical performance
- `/api/interest-by-region` - Geographic targeting
- `/api/related-topics` - Topic clusters

---

## 📦 Project Structure

```
pytrends_api/
├── pytrends_api.py          # Main API application (650+ lines)
├── cache_manager.py          # Intelligent caching system
├── passenger_wsgi.py         # cPanel WSGI entry point
├── requirements.txt          # Python dependencies
├── .htaccess                 # Apache/cPanel configuration
├── DEPLOYMENT.md            # Full deployment guide
├── README.md                # This file
└── logs/                    # Application logs
```

---

## 🔧 Configuration

### **Environment Variables**

```bash
# Required
API_SECRET_KEY=your-secure-api-key-min-32-chars

# Optional
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
TZ=UTC
```

### **Cache TTL Customization**

Edit `pytrends_api.py`:
```python
CACHE_TTL_SHORT = 1800      # 30 minutes
CACHE_TTL_MEDIUM = 3600     # 1 hour
CACHE_TTL_LONG = 7200       # 2 hours
```

---

## 🐛 Troubleshooting

### **Common Issues**

1. **"429 Too Many Requests"**
   - Google is rate limiting
   - Solution: Cache is enabled by default, reduce request frequency

2. **"Connection Timeout"**
   - Google Trends is slow/unavailable
   - Solution: Increase timeout in `get_pytrends_client()`

3. **"Empty Results"**
   - Keyword has no data for that timeframe/geo
   - Solution: Try different parameters

4. **Import Errors**
   - Missing dependencies
   - Solution: `pip install -r requirements.txt`

---

## 📚 Timeframe Options

Valid timeframe values:

- `now 1-H` - Last hour
- `now 4-H` - Last 4 hours  
- `now 1-d` - Last day
- `now 7-d` - Last 7 days
- `today 1-m` - Past 30 days
- `today 3-m` - Past 90 days
- `today 12-m` - Past 12 months (default)
- `today 5-y` - Past 5 years
- `all` - 2004-present (not always available)

---

## 🌍 Geographic Codes

Common geo codes:

- `""` - Worldwide
- `US` - United States
- `GB` - United Kingdom
- `CA` - Canada
- `AU` - Australia
- `IN` - India
- `JP` - Japan
- `DE` - Germany
- `FR` - France
- `BR` - Brazil

Full list: ISO 3166-1 alpha-2 country codes

---

## ⚡ Performance Tips

1. **Use Caching** - Already enabled by default
2. **Batch Requests** - Use `/api/research` for multiple data points
3. **Set Appropriate TTL** - Longer for historical data
4. **Monitor Cache Hit Rate** - Check `/api/cache/stats`
5. **Use Redis** - For multi-server deployments (optional)

---

## 📖 API Response Format

All endpoints return consistent JSON:

**Success:**
```json
{
  "success": true,
  "keyword": "python programming",
  "data": [...],
  "timestamp": "2024-02-18T10:30:00Z"
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message here",
  "timestamp": "2024-02-18T10:30:00Z"
}
```

---

## 🔒 Security Features

- ✅ API Key authentication
- ✅ HTTPS enforcement (configurable)
- ✅ CORS protection
- ✅ Rate limiting via caching
- ✅ Input validation
- ✅ Secure file permissions
- ✅ Sensitive file protection

---

## 📊 Technology Stack

- **FastAPI** - Modern Python web framework
- **PyTrends** - Unofficial Google Trends API
- **Pandas** - Data processing
- **Redis** - Optional distributed caching
- **Uvicorn** - ASGI server
- **Passenger** - cPanel deployment

---

## 🚢 Deployment

### **cPanel (Recommended)**
See [DEPLOYMENT.md](DEPLOYMENT.md) for complete guide.

### **Docker** (Future)
```dockerfile
# Coming soon
```

### **Heroku/Railway/Render**
Works with standard Python buildpack + Procfile

---

## 📝 License

This project uses:
- **PyTrends**: Apache 2.0 License
- **FastAPI**: MIT License

Your API wrapper: Use as you wish!

---

## ⚠️ Important Notes

1. **Unofficial API**: PyTrends scrapes Google Trends (not official API)
2. **Rate Limiting**: Google may rate limit requests
3. **Archive Status**: PyTrends repo was archived April 2025 but still functional
4. **Cache Recommended**: Always use caching to avoid rate limits
5. **No Guarantees**: Google may change their backend anytime

---

## 🎯 Perfect For

- ✅ AI Blog Writers
- ✅ Content Creators
- ✅ SEO Professionals
- ✅ Keyword Research Tools
- ✅ Market Research
- ✅ Trend Analysis
- ✅ Data Journalists
- ✅ Social Media Managers

---

## 🤝 Contributing

This is a custom implementation for your AI blog writer. Feel free to:
- Fork and customize
- Add new endpoints
- Improve caching strategies
- Enhance error handling

---

## 📞 Support

For deployment issues, check:
1. Application logs: `logs/pytrends_api.log`
2. [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section
3. Swagger docs: `/docs` endpoint

---

## 🎉 Quick Test

After deployment, test immediately:

```bash
# Health check (no auth required)
curl https://your-api.com/health

# Test with auth
curl -X POST https://your-api.com/api/related-queries \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "AI blog writing"}'
```

---

**Built with ❤️ for AI-powered content creation**

Last updated: 2024-02-18
