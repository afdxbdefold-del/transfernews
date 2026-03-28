"""
TransferNews.de - Background Scheduler
Automatisierte Tasks für News-Scraping und Pre-Rendering

Cronjobs:
- Alle 30 Min: RSS-Feeds scrapen
- Alle 30 Min: Pending Events verarbeiten
- Alle 6 Stunden: Cache aufräumen
- Alle 12 Stunden: Alle Artikel pre-rendern
"""

import asyncio
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler = None
db: AsyncIOMotorDatabase = None


def get_db():
    """Get database connection"""
    global db
    if db is None:
        mongo_url = os.environ.get('MONGO_URL')
        db_name = os.environ.get('DB_NAME', 'transfernews')
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
    return db


# ========================
# SCHEDULED TASKS
# ========================

async def task_scrape_rss_feeds():
    """
    Scrape RSS feeds for new transfer news
    Runs every 30 minutes
    """
    logger.info("[CRON] Starting RSS feed scrape...")
    
    try:
        from data_import import import_rss_events
        
        database = get_db()
        result = await import_rss_events(database)
        
        logger.info(f"[CRON] RSS scrape complete: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[CRON] RSS scrape failed: {e}")
        return {"error": str(e)}


async def task_process_pending_events():
    """
    Process pending events and generate articles
    Runs every 30 minutes (after RSS scrape)
    """
    logger.info("[CRON] Processing pending events...")
    
    try:
        from data_import import process_pending_events
        
        database = get_db()
        result = await process_pending_events(database, limit=5)
        
        logger.info(f"[CRON] Event processing complete: {result}")
        
        # Pre-render newly created articles
        if result.get("articles_created", 0) > 0:
            await task_prerender_new_articles()
        
        return result
        
    except Exception as e:
        logger.error(f"[CRON] Event processing failed: {e}")
        return {"error": str(e)}


async def task_prerender_new_articles():
    """
    Pre-render recently published articles
    Called after article creation
    """
    logger.info("[CRON] Pre-rendering new articles...")
    
    try:
        from prerender import prerender_all_articles, prerender_homepage
        
        database = get_db()
        result = await prerender_all_articles(database, limit=10)
        
        # Also refresh homepage
        await prerender_homepage()
        
        logger.info(f"[CRON] Pre-render complete: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[CRON] Pre-render failed: {e}")
        return {"error": str(e)}


async def task_cleanup_cache():
    """
    Clean up old pre-render cache files
    Runs every 6 hours
    """
    logger.info("[CRON] Cleaning up cache...")
    
    try:
        from prerender import cleanup_old_cache
        
        removed = await cleanup_old_cache(max_age_hours=48)
        
        logger.info(f"[CRON] Cache cleanup complete: {removed} files removed")
        return {"removed": removed}
        
    except Exception as e:
        logger.error(f"[CRON] Cache cleanup failed: {e}")
        return {"error": str(e)}


async def task_full_prerender():
    """
    Full pre-render of all articles
    Runs every 12 hours
    """
    logger.info("[CRON] Starting full pre-render...")
    
    try:
        from prerender import prerender_all_articles, prerender_homepage
        
        database = get_db()
        result = await prerender_all_articles(database, limit=100)
        await prerender_homepage()
        
        logger.info(f"[CRON] Full pre-render complete: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[CRON] Full pre-render failed: {e}")
        return {"error": str(e)}


async def task_ping_google_sitemaps():
    """
    Ping Google about sitemap updates
    Runs every hour
    """
    logger.info("[CRON] Pinging Google sitemaps...")
    
    try:
        from sitemap import ping_google_sitemap, ping_google_news_sitemap
        
        sitemap_ok = await ping_google_sitemap()
        news_ok = await ping_google_news_sitemap()
        
        logger.info(f"[CRON] Google ping: sitemap={sitemap_ok}, news={news_ok}")
        return {"sitemap": sitemap_ok, "news": news_ok}
        
    except Exception as e:
        logger.error(f"[CRON] Google ping failed: {e}")
        return {"error": str(e)}


# ========================
# SCHEDULER SETUP
# ========================

def setup_scheduler():
    """Initialize and configure the scheduler"""
    global scheduler
    
    if scheduler is not None:
        return scheduler
    
    scheduler = AsyncIOScheduler(timezone="UTC")
    
    # RSS Scraping - every 30 minutes
    scheduler.add_job(
        task_scrape_rss_feeds,
        IntervalTrigger(minutes=30),
        id="scrape_rss",
        name="Scrape RSS Feeds",
        replace_existing=True
    )
    
    # Process Events - every 30 minutes (offset by 5 min from RSS)
    scheduler.add_job(
        task_process_pending_events,
        IntervalTrigger(minutes=30, start_date=datetime.now(timezone.utc).replace(second=0, microsecond=0)),
        id="process_events",
        name="Process Pending Events",
        replace_existing=True
    )
    
    # Cache Cleanup - every 6 hours
    scheduler.add_job(
        task_cleanup_cache,
        IntervalTrigger(hours=6),
        id="cleanup_cache",
        name="Cleanup Cache",
        replace_existing=True
    )
    
    # Full Pre-render - every 12 hours
    scheduler.add_job(
        task_full_prerender,
        IntervalTrigger(hours=12),
        id="full_prerender",
        name="Full Pre-render",
        replace_existing=True
    )
    
    # Google Ping - every hour
    scheduler.add_job(
        task_ping_google_sitemaps,
        IntervalTrigger(hours=1),
        id="ping_google",
        name="Ping Google Sitemaps",
        replace_existing=True
    )
    
    logger.info("[SCHEDULER] Configured with 5 jobs")
    return scheduler


def start_scheduler():
    """Start the background scheduler"""
    global scheduler
    
    if scheduler is None:
        scheduler = setup_scheduler()
    
    if not scheduler.running:
        scheduler.start()
        logger.info("[SCHEDULER] Started")
    
    return scheduler


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("[SCHEDULER] Stopped")


def get_scheduler_status() -> dict:
    """Get current scheduler status and job info"""
    if scheduler is None:
        return {"running": False, "jobs": []}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "running": scheduler.running,
        "jobs": jobs
    }


# ========================
# MANUAL TRIGGERS
# ========================

async def trigger_rss_scrape():
    """Manually trigger RSS scrape"""
    return await task_scrape_rss_feeds()


async def trigger_event_processing():
    """Manually trigger event processing"""
    return await task_process_pending_events()


async def trigger_full_prerender():
    """Manually trigger full pre-render"""
    return await task_full_prerender()
