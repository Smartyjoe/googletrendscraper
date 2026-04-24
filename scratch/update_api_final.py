import os

file_path = r"c:\Users\USER\Documents\smatatech\pytrends-google-search\pytrends_api.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace related_topics
old_rt = """    try:
        pytrends = get_pytrends_client()
        pytrends.build_payload(
            [request.keyword],
            timeframe=request.timeframe,
            geo=request.geo
        )
        
        related = pytrends.related_topics()"""

new_rt = """    try:
        def _fetch(pt):
            pt.build_payload(
                [request.keyword],
                timeframe=request.timeframe,
                geo=request.geo
            )
            return pt.related_topics()
            
        related = execute_with_proxy_retry(_fetch)"""

# Replace trending_searches
old_ts = """    try:
        pytrends = get_pytrends_client()
        df = pytrends.trending_searches(pn=request.pn)"""

new_ts = """    try:
        def _fetch(pt):
            return pt.trending_searches(pn=request.pn)
        df = execute_with_proxy_retry(_fetch)"""

# Replace today_searches
old_tds = """    try:
        pytrends = get_pytrends_client()
        df = pytrends.today_searches(pn=pn)"""

new_tds = """    try:
        def _fetch(pt):
            return pt.today_searches(pn=pn)
        df = execute_with_proxy_retry(_fetch)"""

# Replace realtime_trending
old_rt_trend = """    try:
        pytrends = get_pytrends_client()
        df = pytrends.realtime_trending_searches(pn=pn, cat=cat)"""

new_rt_trend = """    try:
        def _fetch(pt):
            return pt.realtime_trending_searches(pn=pn, cat=cat)
        df = execute_with_proxy_retry(_fetch)"""

# Replace suggestions
old_sugg = """    try:
        pytrends = get_pytrends_client()
        suggestions = pytrends.suggestions(request.keyword)"""

new_sugg = """    try:
        def _fetch(pt):
            return pt.suggestions(request.keyword)
        suggestions = execute_with_proxy_retry(_fetch)"""

content = content.replace(old_rt, new_rt)
content = content.replace(old_ts, new_ts)
content = content.replace(old_tds, new_tds)
content = content.replace(old_rt_trend, new_rt_trend)
content = content.replace(old_sugg, new_sugg)

with open(file_path, 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("Successfully updated remaining endpoints in pytrends_api.py")
