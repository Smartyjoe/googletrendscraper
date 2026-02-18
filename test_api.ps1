# ============================================================================
# PyTrends API - Automated Test Script
# ============================================================================
# This script tests all major endpoints to verify the API is working correctly
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PyTrends API - Automated Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$API_URL = "http://localhost:8000"
$API_KEY = "test-secret-key-for-local-development-12345"

$headers = @{
    "X-API-Key" = $API_KEY
    "Content-Type" = "application/json"
}

# Test counter
$testsPassed = 0
$testsFailed = 0

# ============================================================================
# Helper Functions
# ============================================================================

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers = @{},
        [string]$Body = $null
    )
    
    Write-Host "Testing: $Name..." -NoNewline
    
    try {
        if ($Method -eq "GET") {
            $response = Invoke-RestMethod -Method GET -Uri $Url -Headers $Headers -ErrorAction Stop
        } else {
            $response = Invoke-RestMethod -Method POST -Uri $Url -Headers $Headers -Body $Body -ErrorAction Stop
        }
        
        Write-Host " ✅ PASSED" -ForegroundColor Green
        $script:testsPassed++
        return $response
    }
    catch {
        Write-Host " ❌ FAILED" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
        $script:testsFailed++
        return $null
    }
}

# ============================================================================
# Run Tests
# ============================================================================

Write-Host "Starting tests..." -ForegroundColor Yellow
Write-Host ""

# Test 1: Health Check
Write-Host "[1/9] Health Check" -ForegroundColor Cyan
$health = Test-Endpoint -Name "Health Check" -Method "GET" -Url "$API_URL/health"
if ($health) {
    Write-Host "   Status: $($health.status)" -ForegroundColor Gray
    Write-Host "   Cache: $($health.cache.type)" -ForegroundColor Gray
}
Write-Host ""

# Test 2: API Root
Write-Host "[2/9] API Root" -ForegroundColor Cyan
$root = Test-Endpoint -Name "API Root" -Method "GET" -Url "$API_URL/"
if ($root) {
    Write-Host "   Version: $($root.version)" -ForegroundColor Gray
}
Write-Host ""

# Test 3: Related Queries
Write-Host "[3/9] Related Queries" -ForegroundColor Cyan
$body = @{
    keyword = "artificial intelligence"
    timeframe = "today 1-m"
    geo = ""
} | ConvertTo-Json

$related = Test-Endpoint -Name "Related Queries" -Method "POST" -Url "$API_URL/api/related-queries" -Headers $headers -Body $body
if ($related) {
    Write-Host "   Keyword: $($related.keyword)" -ForegroundColor Gray
    Write-Host "   Top queries: $($related.top.Count)" -ForegroundColor Gray
    Write-Host "   Rising queries: $($related.rising.Count)" -ForegroundColor Gray
}
Write-Host ""

# Test 4: Interest Over Time
Write-Host "[4/9] Interest Over Time" -ForegroundColor Cyan
$body = @{
    keyword = "python programming"
    timeframe = "today 3-m"
    geo = ""
} | ConvertTo-Json

$interest = Test-Endpoint -Name "Interest Over Time" -Method "POST" -Url "$API_URL/api/interest-over-time" -Headers $headers -Body $body
if ($interest) {
    Write-Host "   Keyword: $($interest.keyword)" -ForegroundColor Gray
    Write-Host "   Data points: $($interest.data.Count)" -ForegroundColor Gray
}
Write-Host ""

# Test 5: Interest by Region
Write-Host "[5/9] Interest by Region" -ForegroundColor Cyan
$body = @{
    keyword = "pizza"
    timeframe = "today 1-m"
    geo = "US"
    resolution = "REGION"
} | ConvertTo-Json

$region = Test-Endpoint -Name "Interest by Region" -Method "POST" -Url "$API_URL/api/interest-by-region" -Headers $headers -Body $body
if ($region) {
    Write-Host "   Keyword: $($region.keyword)" -ForegroundColor Gray
    Write-Host "   Regions: $($region.data.Count)" -ForegroundColor Gray
}
Write-Host ""

# Test 6: Trending Searches
Write-Host "[6/9] Trending Searches" -ForegroundColor Cyan
$body = @{
    geo = "US"
} | ConvertTo-Json

$trending = Test-Endpoint -Name "Trending Searches" -Method "POST" -Url "$API_URL/api/trending" -Headers $headers -Body $body
if ($trending) {
    Write-Host "   Country: $($trending.geo)" -ForegroundColor Gray
    Write-Host "   Trending topics: $($trending.trending.Count)" -ForegroundColor Gray
}
Write-Host ""

# Test 7: Suggestions
Write-Host "[7/9] Keyword Suggestions" -ForegroundColor Cyan
$body = @{
    keyword = "tech"
} | ConvertTo-Json

$suggestions = Test-Endpoint -Name "Suggestions" -Method "POST" -Url "$API_URL/api/suggestions" -Headers $headers -Body $body
if ($suggestions) {
    Write-Host "   Keyword: $($suggestions.keyword)" -ForegroundColor Gray
    Write-Host "   Suggestions: $($suggestions.suggestions.Count)" -ForegroundColor Gray
}
Write-Host ""

# Test 8: Comprehensive Research
Write-Host "[8/9] Comprehensive Research (This may take 10-15 seconds...)" -ForegroundColor Cyan
$body = @{
    keywords = @("AI")
    timeframe = "today 1-m"
    geo = ""
    include_interest_over_time = $true
    include_interest_by_region = $true
    include_related_queries = $true
    include_related_topics = $false
    include_trending = $false
    include_suggestions = $true
} | ConvertTo-Json

$research = Test-Endpoint -Name "Comprehensive Research" -Method "POST" -Url "$API_URL/api/research" -Headers $headers -Body $body
if ($research) {
    Write-Host "   Keywords analyzed: $($research.keywords.Count)" -ForegroundColor Gray
    Write-Host "   Has interest over time: $($research.interest_over_time -ne $null)" -ForegroundColor Gray
    Write-Host "   Has regional data: $($research.interest_by_region -ne $null)" -ForegroundColor Gray
}
Write-Host ""

# Test 9: Cache Test (Run same request twice)
Write-Host "[9/9] Cache Performance Test" -ForegroundColor Cyan
$body = @{
    keyword = "blockchain"
    timeframe = "today 1-m"
} | ConvertTo-Json

Write-Host "   First request (uncached)..." -NoNewline
$time1 = Measure-Command {
    $result1 = Invoke-RestMethod -Method POST -Uri "$API_URL/api/related-queries" -Headers $headers -Body $body -ErrorAction Stop
}
Write-Host " $([math]::Round($time1.TotalMilliseconds))ms" -ForegroundColor Yellow

Write-Host "   Second request (cached)..." -NoNewline
$time2 = Measure-Command {
    $result2 = Invoke-RestMethod -Method POST -Uri "$API_URL/api/related-queries" -Headers $headers -Body $body -ErrorAction Stop
}
Write-Host " $([math]::Round($time2.TotalMilliseconds))ms" -ForegroundColor Green

$speedup = [math]::Round($time1.TotalMilliseconds / $time2.TotalMilliseconds, 1)
Write-Host "   Cache speedup: ${speedup}x faster!" -ForegroundColor Green

if ($time2.TotalMilliseconds -lt 500) {
    Write-Host " ✅ PASSED" -ForegroundColor Green
    $script:testsPassed++
} else {
    Write-Host " ⚠️  WARNING: Cache might not be working optimally" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# Test Summary
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Test Results" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tests Passed: $testsPassed" -ForegroundColor Green
Write-Host "Tests Failed: $testsFailed" -ForegroundColor $(if ($testsFailed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "🎉 All tests passed! Your API is ready to deploy!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Review DEPLOYMENT.md for cPanel deployment guide" -ForegroundColor Gray
    Write-Host "  2. Update your API_SECRET_KEY for production" -ForegroundColor Gray
    Write-Host "  3. Configure CORS for your Laravel application" -ForegroundColor Gray
} else {
    Write-Host "⚠️  Some tests failed. Please check the errors above." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Make sure the API server is running (python pytrends_api.py)" -ForegroundColor Gray
    Write-Host "  2. Check that all dependencies are installed" -ForegroundColor Gray
    Write-Host "  3. Verify your API_SECRET_KEY environment variable" -ForegroundColor Gray
    Write-Host "  4. See LOCAL_TESTING_GUIDE.md for detailed troubleshooting" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan