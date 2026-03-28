"""
TransferNews.de - SPEED-OPTIMIZED SCHEDULER
============================================

INTERVALLE:
- RSS Scraping:     alle 2 Minuten
- Event Processing: alle 1 Minute (kontinuierlich)
- GPT Rewrite:      alle 5 Minuten
- Sitemap:          alle 2 Minuten
- Internal Links:   alle 3 Minuten
- Pre-Render:       alle 2 Stunden
- Cache Cleanup:    alle 6 Stunden
"""

import asyncio
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)

# Scheduler Instance
scheduler = AsyncIOScheduler()

# DB Connection
_db = None

def get_db():
    global _db
    if _db is None:
        client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
        _db = client[os.environ.get('DB_NAME', 'transfernews')]
    return _db


# =============================================================================
# JOB 1: RSS SCRAPING (alle 2 Minuten)
# =============================================================================

async def task_rss_scrape():
    """Scraped alle RSS-Feeds nach Transfer-News"""
    try:
        from data_import import import_rss_events
        db = get_db()
        result = await import_rss_events(db)
        
        new_events = result.get("new_events", 0)
        if new_events > 0:
            logger.info(f"[CRON:RSS] {new_events} neue Events gefunden")
        
        return result
    except Exception as e:
        logger.error(f"[CRON:RSS] Error: {e}")
        return {"error": str(e)}


# =============================================================================
# JOB 2: SPEED PIPELINE (alle 1 Minute)
# =============================================================================

async def task_speed_pipeline():
    """Verarbeitet pending Events SOFORT zu Artikeln"""
    try:
        from speed_pipeline import SpeedPipeline
        db = get_db()
        pipeline = SpeedPipeline(db)
        result = await pipeline.process_pending_events(limit=20)
        
        if result.get("created", 0) > 0 or result.get("updated", 0) > 0:
            logger.info(f"[CRON:SPEED] Created: {result.get('created', 0)}, Updated: {result.get('updated', 0)}, Avg: {result.get('total_time_ms', 0) // max(1, result.get('processed', 1))}ms")
        
        return result
    except Exception as e:
        logger.error(f"[CRON:SPEED] Error: {e}")
        return {"error": str(e)}


# =============================================================================
# JOB 3: GPT REWRITE (alle 5 Minuten)
# =============================================================================

async def task_gpt_rewrite():
    """Verbessert Instant-Artikel mit GPT (Hintergrund)"""
    try:
        from speed_pipeline import GPTRewriter
        db = get_db()
        rewriter = GPTRewriter(db)
        result = await rewriter.process_rewrite_queue(limit=3)
        
        if result.get("rewritten", 0) > 0:
            logger.info(f"[CRON:GPT] {result.get('rewritten', 0)} Artikel verbessert")
        
        return result
    except Exception as e:
        logger.error(f"[CRON:GPT] Error: {e}")
        return {"error": str(e)}


# =============================================================================
# JOB 4: NEWS-SITEMAP UPDATE (alle 2 Minuten)
# =============================================================================

async def task_sitemap_update():
    """Aktualisiert news-sitemap.xml"""
    try:
        from sitemap import generate_news_sitemap, ping_google_sitemaps
        db = get_db()
        
        # Sitemap generieren
        sitemap = await generate_news_sitemap(db)
        
        # Google pingen (nur wenn neue Artikel)
        article_count = sitemap.count("<url>")
        if article_count > 0:
            await ping_google_sitemaps()
            logger.info(f"[CRON:SITEMAP] {article_count} URLs, Google gepingt")
        
        return {"articles": article_count}
    except Exception as e:
        logger.error(f"[CRON:SITEMAP] Error: {e}")
        return {"error": str(e)}


# =============================================================================
# JOB 5: INTERNAL LINKS (alle 3 Minuten)
# =============================================================================

async def task_internal_links():
    """Aktualisiert interne Verlinkungen"""
    try:
        from speed_pipeline import InternalLinksUpdater
        db = get_db()
        updater = InternalLinksUpdater(db)
        
        # Neue Artikel ohne Links
        articles = await db.articles.find(
            {"links_updated": {"$ne": True}},
            {"_id": 0}
        ).sort("published_at", -1).limit(10).to_list(10)
        
        for article in articles:
            await updater.update_links_for_article(article)
            await db.articles.update_one(
                {"id": article.get("id")},
                {"$set": {"links_updated": True}}
            )
        
        if articles:
            logger.info(f"[CRON:LINKS] {len(articles)} Artikel verlinkt")
        
        return {"updated": len(articles)}
    except Exception as e:
        logger.error(f"[CRON:LINKS] Error: {e}")
        return {"error": str(e)}


# =============================================================================
# JOB 6: PRE-RENDERING (alle 2 Stunden)
# =============================================================================

async def task_prerender():
    """Pre-rendert Seiten für Google"""
    try:
        from prerender import prerender_homepage, prerender_recent_articles
        
        await prerender_homepage()
        count = await prerender_recent_articles(limit=20)
        
        logger.info(f"[CRON:PRERENDER] {count} Seiten gerendert")
        return {"pages": count}
    except Exception as e:
        logger.error(f"[CRON:PRERENDER] Error: {e}")
        return {"error": str(e)}


# =============================================================================
# JOB 7: CACHE CLEANUP (alle 6 Stunden)
# =============================================================================

async def task_cache_cleanup():
    """Löscht alte Cache-Dateien"""
    try:
        from prerender import cleanup_old_cache
        result = await cleanup_old_cache(max_age_hours=48)
        
        if result.get("deleted", 0) > 0:
            logger.info(f"[CRON:CLEANUP] {result.get('deleted', 0)} Dateien gelöscht")
        
        return result
    except Exception as e:
        logger.error(f"[CRON:CLEANUP] Error: {e}")
        return {"error": str(e)}


# =============================================================================
# JOB 8: HEALTH CHECK (alle 5 Minuten)
# =============================================================================

async def task_health_check():
    """Prüft System-Gesundheit"""
    try:
        db = get_db()
        
        # Pending Events zählen
        pending = await db.events.count_documents({"status": "pending"})
        
        # Artikel der letzten Stunde
        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        recent = await db.articles.count_documents({"published_at": {"$gte": cutoff}})
        
        if pending > 50:
            logger.warning(f"[HEALTH] {pending} pending events - Pipeline möglicherweise überlastet")
        
        return {"pending_events": pending, "recent_articles": recent}
    except Exception as e:
        logger.error(f"[HEALTH] Error: {e}")
        return {"error": str(e)}


# =============================================================================
# SCHEDULER SETUP
# =============================================================================

def setup_scheduler():
    """Konfiguriert alle Cronjobs"""
    
    # Job 1: RSS Scraping - alle 2 Minuten
    scheduler.add_job(
        task_rss_scrape,
        IntervalTrigger(minutes=2),
        id='rss_scrape',
        name='RSS Feed Scraping',
        replace_existing=True,
        max_instances=1
    )
    
    # Job 2: Speed Pipeline - alle 1 Minute
    scheduler.add_job(
        task_speed_pipeline,
        IntervalTrigger(minutes=1),
        id='speed_pipeline',
        name='Speed Pipeline Processing',
        replace_existing=True,
        max_instances=1
    )
    
    # Job 3: GPT Rewrite - alle 5 Minuten
    scheduler.add_job(
        task_gpt_rewrite,
        IntervalTrigger(minutes=5),
        id='gpt_rewrite',
        name='GPT Article Rewrite',
        replace_existing=True,
        max_instances=1
    )
    
    # Job 4: Sitemap Update - alle 2 Minuten
    scheduler.add_job(
        task_sitemap_update,
        IntervalTrigger(minutes=2),
        id='sitemap_update',
        name='News Sitemap Update',
        replace_existing=True,
        max_instances=1
    )
    
    # Job 5: Internal Links - alle 3 Minuten
    scheduler.add_job(
        task_internal_links,
        IntervalTrigger(minutes=3),
        id='internal_links',
        name='Internal Links Update',
        replace_existing=True,
        max_instances=1
    )
    
    # Job 6: Pre-Rendering - alle 2 Stunden
    scheduler.add_job(
        task_prerender,
        IntervalTrigger(hours=2),
        id='prerender',
        name='Page Pre-Rendering',
        replace_existing=True,
        max_instances=1
    )
    
    # Job 7: Cache Cleanup - alle 6 Stunden
    scheduler.add_job(
        task_cache_cleanup,
        IntervalTrigger(hours=6),
        id='cache_cleanup',
        name='Cache Cleanup',
        replace_existing=True,
        max_instances=1
    )
    
    # Job 8: Health Check - alle 5 Minuten
    scheduler.add_job(
        task_health_check,
        IntervalTrigger(minutes=5),
        id='health_check',
        name='System Health Check',
        replace_existing=True,
        max_instances=1
    )
    
    logger.info("[SCHEDULER] All jobs configured")
    logger.info("[SCHEDULER] Intervals: RSS=2min, Pipeline=1min, GPT=5min, Sitemap=2min")


def start_scheduler():
    """Startet den Scheduler"""
    if not scheduler.running:
        setup_scheduler()
        scheduler.start()
        logger.info("[SCHEDULER] Started")


def stop_scheduler():
    """Stoppt den Scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("[SCHEDULER] Stopped")


def get_scheduler_status() -> dict:
    """Gibt Scheduler-Status zurück"""
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
        "jobs": jobs,
        "job_count": len(jobs)
    }


# =============================================================================
# MANUAL TRIGGERS (für API)
# =============================================================================

async def trigger_rss_scrape():
    """Manueller RSS-Scrape"""
    return await task_rss_scrape()

async def trigger_speed_pipeline():
    """Manuelle Pipeline-Verarbeitung"""
    return await task_speed_pipeline()

async def trigger_gpt_rewrite():
    """Manueller GPT-Rewrite"""
    return await task_gpt_rewrite()

async def trigger_sitemap_update():
    """Manuelles Sitemap-Update"""
    return await task_sitemap_update()

async def trigger_prerender():
    """Manuelles Pre-Rendering"""
    return await task_prerender()

async def trigger_full_pipeline():
    """Komplette Pipeline manuell ausführen"""
    results = {}
    
    # 1. RSS Scrape
    results["rss"] = await task_rss_scrape()
    
    # 2. Speed Pipeline
    results["pipeline"] = await task_speed_pipeline()
    
    # 3. Sitemap
    results["sitemap"] = await task_sitemap_update()
    
    # 4. Internal Links
    results["links"] = await task_internal_links()
    
    return results
