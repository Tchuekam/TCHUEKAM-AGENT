# GIANTECH EMPIRE - SCRAPER PRODUCTION SETTINGS
BOT_NAME = "scraper"

SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# Respect standard scraping practices
ROBOTSTXT_OBEY = False

# Realistic user agents to bypass basic blocking
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Run with respectful concurrency
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 1.0

# Active Pipeline integrations
ITEM_PIPELINES = {
    "scraper.pipelines.SQLitePipeline": 300,
}

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
