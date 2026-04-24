import os

file_path = r"c:\Users\USER\Documents\smatatech\pytrends-google-search\pytrends_api.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace interest_over_time
old_iot = """        pytrends = get_pytrends_client()
        pytrends.build_payload(
            request.keywords,
            timeframe=request.timeframe,
            geo=request.geo,
            gprop=request.gprop
        )
        
        df = pytrends.interest_over_time()"""

new_iot = """        def _fetch(pt):
            pt.build_payload(
                request.keywords,
                timeframe=request.timeframe,
                geo=request.geo,
                gprop=request.gprop
            )
            return pt.interest_over_time()
            
        df = execute_with_proxy_retry(_fetch)"""

# Replace interest_by_region
old_ibr = """        pytrends = get_pytrends_client()
        pytrends.build_payload(
            request.keywords,
            timeframe=request.timeframe,
            geo=request.geo
        )
        
        df = pytrends.interest_by_region(
            resolution=request.resolution,
            inc_low_vol=request.inc_low_vol,
            inc_geo_code=request.inc_geo_code
        )"""

new_ibr = """        def _fetch(pt):
            pt.build_payload(
                request.keywords,
                timeframe=request.timeframe,
                geo=request.geo
            )
            return pt.interest_by_region(
                resolution=request.resolution,
                inc_low_vol=request.inc_low_vol,
                inc_geo_code=request.inc_geo_code
            )
            
        df = execute_with_proxy_retry(_fetch)"""

# Replace related_queries
old_rq = """        pytrends = get_pytrends_client()
        pytrends.build_payload([request.keyword], timeframe=request.timeframe, geo=request.geo)
        
        related_queries = pytrends.related_queries()"""

new_rq = """        def _fetch(pt):
            pt.build_payload([request.keyword], timeframe=request.timeframe, geo=request.geo)
            return pt.related_queries()
            
        related_queries = execute_with_proxy_retry(_fetch)"""

# Replace comprehensive_research
old_comp = """        pytrends = get_pytrends_client()
        pytrends.build_payload(request.keywords, timeframe=request.timeframe, geo=request.geo)
        
        response = {
            "success": True,
            "keywords": request.keywords,
            "timeframe": request.timeframe,
            "geo": request.geo or "worldwide",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 1. Interest Over Time
        try:
            df_interest = pytrends.interest_over_time()
            response["interest_over_time"] = dataframe_to_json_serializable(df_interest)
        except Exception as e:
            logger.warning(f"Failed to fetch interest_over_time: {e}")
            response["interest_over_time"] = []"""

new_comp = """        def _fetch_all(pt):
            pt.build_payload(request.keywords, timeframe=request.timeframe, geo=request.geo)
            
            res = {
                "success": True,
                "keywords": request.keywords,
                "timeframe": request.timeframe,
                "geo": request.geo or "worldwide",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # 1. Interest Over Time
            try:
                df_interest = pt.interest_over_time()
                res["interest_over_time"] = dataframe_to_json_serializable(df_interest)
            except Exception as e:
                logger.warning(f"Failed to fetch interest_over_time: {e}")
                res["interest_over_time"] = []
            return res, pt

        fetch_res, pytrends = execute_with_proxy_retry(_fetch_all)
        response = fetch_res"""

# Replace categories
old_cat = """    try:
        pytrends = get_pytrends_client()
        categories = pytrends.categories()"""

new_cat = """    try:
        def _fetch(pt):
            return pt.categories()
        categories = execute_with_proxy_retry(_fetch)"""

content = content.replace(old_iot, new_iot)
content = content.replace(old_ibr, new_ibr)
content = content.replace(old_rq, new_rq)
content = content.replace(old_comp, new_comp)
content = content.replace(old_cat, new_cat)

with open(file_path, 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("Successfully updated pytrends_api.py")
