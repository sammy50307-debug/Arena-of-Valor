import sys
import os
print("Testing imports...")
try:
    import argparse
    import asyncio
    import io
    import json
    import logging
    import subprocess
    from datetime import datetime
    from pathlib import Path
    from dataclasses import asdict
    print("Standard imports OK")
    
    import apscheduler
    print("apscheduler OK")
    
    import rich
    print("rich OK")
    
    import jinja2
    print("jinja2 OK")
    
    print("Checking local imports...")
    import config
    print("config OK")
    
    from scrapers.tavily_searcher import TavilySearcher
    print("TavilySearcher OK")
    
    from scrapers.apify_scraper import ApifyInstagramScraper
    print("ApifyInstagramScraper OK")
    
    from scrapers.hero_stats import HeroStatsScraper
    print("HeroStatsScraper OK")
    
    from analyzer.sentiment import SentimentAnalyzer
    print("SentimentAnalyzer OK")
    
    from reporter.generator import ReportGenerator
    print("ReportGenerator OK")
    
    print("All modules imported successfully!")
except Exception as e:
    print(f"Error during import: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
