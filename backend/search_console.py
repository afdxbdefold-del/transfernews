"""
TransferNews.de - Google Search Console Integration
Indexierungsstatus, Performance-Daten und URL-Einreichung für das Admin-Dashboard

Features:
- URL Inspection API: Indexierungsstatus prüfen
- Search Analytics API: Klicks, Impressionen, CTR, Position
- Indexing API: URLs zur Indexierung einreichen
- Mobile Usability: Fehler und Warnungen abrufen
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path
from functools import lru_cache

logger = logging.getLogger(__name__)

# Check if Google credentials are available
GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE', '')
SITE_URL = os.environ.get('SITE_URL', 'https://transfernews.de')

# Flag to check if GSC is configured
GSC_CONFIGURED = bool(GOOGLE_SERVICE_ACCOUNT_FILE and Path(GOOGLE_SERVICE_ACCOUNT_FILE).exists())


class GoogleSearchConsoleService:
    """
    Google Search Console API Service
    Provides methods for URL inspection, search analytics, and indexing
    """
    
    def __init__(self):
        self.credentials = None
        self.webmasters_service = None
        self.searchconsole_service = None
        self.indexing_service = None
        self.configured = GSC_CONFIGURED
        
        if self.configured:
            self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Google API services with service account credentials"""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            # Scopes needed for all GSC APIs
            scopes = [
                'https://www.googleapis.com/auth/webmasters.readonly',
                'https://www.googleapis.com/auth/webmasters',
                'https://www.googleapis.com/auth/indexing'
            ]
            
            # Load credentials from service account file
            self.credentials = service_account.Credentials.from_service_account_file(
                GOOGLE_SERVICE_ACCOUNT_FILE,
                scopes=scopes
            )
            
            # Build service objects
            self.webmasters_service = build('webmasters', 'v3', credentials=self.credentials)
            self.searchconsole_service = build('searchconsole', 'v1', credentials=self.credentials)
            self.indexing_service = build('indexing', 'v3', credentials=self.credentials)
            
            logger.info("Google Search Console services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize GSC services: {e}")
            self.configured = False
    
    # ========================
    # URL INSPECTION API
    # ========================
    
    async def inspect_url(self, url: str) -> Dict[str, Any]:
        """
        Inspect URL indexation status using URL Inspection API
        
        Returns detailed information about how Google has indexed the URL
        """
        if not self.configured:
            return {"error": "Google Search Console nicht konfiguriert", "configured": False}
        
        try:
            request_body = {
                "inspectionUrl": url,
                "siteUrl": SITE_URL,
                "languageCode": "de"
            }
            
            response = self.searchconsole_service.urlInspection().index().inspect(
                body=request_body
            ).execute()
            
            inspection_result = response.get("inspectionResult", {})
            index_result = inspection_result.get("indexStatusResult", {})
            mobile_result = inspection_result.get("mobileUsabilityResult", {})
            rich_results = inspection_result.get("richResultsResult", {})
            
            # Determine overall status
            indexed = index_result.get("verdict") == "PASS"
            coverage_state = index_result.get("coverageState", "Unbekannt")
            
            # Map coverage states to German
            coverage_translations = {
                "Indexed, not submitted in sitemap": "Indexiert, nicht in Sitemap",
                "Submitted and indexed": "Eingereicht und indexiert",
                "Excluded by 'noindex' tag": "Durch 'noindex' ausgeschlossen",
                "Crawled - currently not indexed": "Gecrawlt - derzeit nicht indexiert",
                "Discovered - currently not indexed": "Entdeckt - derzeit nicht indexiert",
                "Page with redirect": "Seite mit Weiterleitung",
                "Not found (404)": "Nicht gefunden (404)",
                "Soft 404": "Soft 404",
                "Server error (5xx)": "Serverfehler (5xx)",
                "Blocked by robots.txt": "Durch robots.txt blockiert",
                "Unknown": "Unbekannt"
            }
            
            return {
                "url": url,
                "indexed": indexed,
                "coverage_state": coverage_translations.get(coverage_state, coverage_state),
                "coverage_state_raw": coverage_state,
                "last_crawl_time": index_result.get("lastCrawlTime"),
                "crawled_as": index_result.get("crawledAs", "Unbekannt"),
                "robots_txt_state": index_result.get("robotsTxtState", "Unbekannt"),
                "indexing_allowed": index_result.get("indexingAllowed", False),
                "mobile_usability": {
                    "verdict": mobile_result.get("verdict", "Unbekannt"),
                    "issues": mobile_result.get("issues", [])
                },
                "rich_results": {
                    "verdict": rich_results.get("verdict", "Nicht verfügbar"),
                    "detected_items": rich_results.get("detectedItems", [])
                },
                "referring_urls": index_result.get("referringUrls", []),
                "sitemap": index_result.get("sitemap"),
                "configured": True
            }
            
        except Exception as e:
            logger.error(f"URL Inspection error for {url}: {e}")
            return {"url": url, "error": str(e), "configured": True}
    
    async def batch_inspect_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Inspect multiple URLs"""
        results = []
        for url in urls[:20]:  # Limit to 20 URLs per batch
            result = await self.inspect_url(url)
            results.append(result)
        return results
    
    # ========================
    # SEARCH ANALYTICS API
    # ========================
    
    async def get_performance_data(
        self,
        start_date: str = None,
        end_date: str = None,
        dimensions: List[str] = None,
        row_limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get search performance data (clicks, impressions, CTR, position)
        
        Args:
            start_date: Start date (YYYY-MM-DD), defaults to 7 days ago
            end_date: End date (YYYY-MM-DD), defaults to today
            dimensions: Grouping dimensions (date, query, page, device, country)
            row_limit: Maximum rows to return
        """
        if not self.configured:
            return {"error": "Google Search Console nicht konfiguriert", "configured": False}
        
        try:
            # Default date range: last 7 days
            if not end_date:
                end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if not start_date:
                start_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
            
            if not dimensions:
                dimensions = ["date"]
            
            request_body = {
                "startDate": start_date,
                "endDate": end_date,
                "dimensions": dimensions,
                "rowLimit": row_limit,
                "startRow": 0
            }
            
            response = self.webmasters_service.searchanalytics().query(
                siteUrl=SITE_URL,
                body=request_body
            ).execute()
            
            rows = response.get("rows", [])
            
            # Calculate totals
            total_clicks = sum(row.get("clicks", 0) for row in rows)
            total_impressions = sum(row.get("impressions", 0) for row in rows)
            avg_ctr = total_clicks / total_impressions if total_impressions > 0 else 0
            avg_position = sum(row.get("position", 0) for row in rows) / len(rows) if rows else 0
            
            return {
                "date_range": {"start": start_date, "end": end_date},
                "dimensions": dimensions,
                "totals": {
                    "clicks": total_clicks,
                    "impressions": total_impressions,
                    "ctr": round(avg_ctr * 100, 2),
                    "position": round(avg_position, 1)
                },
                "rows": [
                    {
                        "keys": row.get("keys", []),
                        "clicks": row.get("clicks", 0),
                        "impressions": row.get("impressions", 0),
                        "ctr": round(row.get("ctr", 0) * 100, 2),
                        "position": round(row.get("position", 0), 1)
                    }
                    for row in rows
                ],
                "row_count": len(rows),
                "configured": True
            }
            
        except Exception as e:
            logger.error(f"Search Analytics error: {e}")
            return {"error": str(e), "configured": True}
    
    async def get_top_queries(self, days: int = 7, limit: int = 20) -> Dict[str, Any]:
        """Get top performing search queries"""
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        
        return await self.get_performance_data(
            start_date=start_date,
            end_date=end_date,
            dimensions=["query"],
            row_limit=limit
        )
    
    async def get_top_pages(self, days: int = 7, limit: int = 20) -> Dict[str, Any]:
        """Get top performing pages"""
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        
        return await self.get_performance_data(
            start_date=start_date,
            end_date=end_date,
            dimensions=["page"],
            row_limit=limit
        )
    
    async def get_daily_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get daily performance stats for chart"""
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        
        return await self.get_performance_data(
            start_date=start_date,
            end_date=end_date,
            dimensions=["date"],
            row_limit=days
        )
    
    async def get_device_breakdown(self, days: int = 7) -> Dict[str, Any]:
        """Get performance breakdown by device type"""
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        
        return await self.get_performance_data(
            start_date=start_date,
            end_date=end_date,
            dimensions=["device"],
            row_limit=10
        )
    
    async def get_country_breakdown(self, days: int = 7, limit: int = 10) -> Dict[str, Any]:
        """Get performance breakdown by country"""
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        
        return await self.get_performance_data(
            start_date=start_date,
            end_date=end_date,
            dimensions=["country"],
            row_limit=limit
        )
    
    # ========================
    # INDEXING API
    # ========================
    
    async def submit_url_for_indexing(self, url: str) -> Dict[str, Any]:
        """
        Submit a URL for indexing via Google Indexing API
        
        Note: Indexing API is primarily for job postings and livestream content,
        but can help with faster crawling for news sites
        """
        if not self.configured:
            return {"error": "Google Search Console nicht konfiguriert", "configured": False}
        
        try:
            request_body = {
                "url": url,
                "type": "URL_UPDATED"
            }
            
            response = self.indexing_service.urlNotifications().publish(
                body=request_body
            ).execute()
            
            return {
                "url": url,
                "status": "submitted",
                "notification_time": response.get("urlNotificationMetadata", {}).get("latestUpdate", {}).get("notifyTime"),
                "configured": True
            }
            
        except Exception as e:
            logger.error(f"Indexing API error for {url}: {e}")
            return {"url": url, "status": "error", "error": str(e), "configured": True}
    
    async def submit_urls_batch(self, urls: List[str]) -> Dict[str, Any]:
        """Submit multiple URLs for indexing"""
        results = {"submitted": [], "errors": []}
        
        for url in urls[:100]:  # Limit to 100 URLs
            result = await self.submit_url_for_indexing(url)
            if result.get("status") == "submitted":
                results["submitted"].append(url)
            else:
                results["errors"].append({"url": url, "error": result.get("error")})
        
        return {
            "total": len(urls),
            "submitted": len(results["submitted"]),
            "errors": len(results["errors"]),
            "details": results,
            "configured": True
        }
    
    async def request_url_removal(self, url: str) -> Dict[str, Any]:
        """Request URL removal from Google index"""
        if not self.configured:
            return {"error": "Google Search Console nicht konfiguriert", "configured": False}
        
        try:
            request_body = {
                "url": url,
                "type": "URL_DELETED"
            }
            
            response = self.indexing_service.urlNotifications().publish(
                body=request_body
            ).execute()
            
            return {
                "url": url,
                "status": "removal_requested",
                "configured": True
            }
            
        except Exception as e:
            logger.error(f"URL removal error for {url}: {e}")
            return {"url": url, "status": "error", "error": str(e), "configured": True}
    
    # ========================
    # DASHBOARD SUMMARY
    # ========================
    
    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Get complete dashboard summary with all key metrics
        Designed for the Admin Panel overview
        """
        if not self.configured:
            return {
                "configured": False,
                "message": "Google Search Console ist nicht konfiguriert. Füge GOOGLE_SERVICE_ACCOUNT_FILE zur .env hinzu.",
                "setup_instructions": {
                    "step1": "Erstelle ein Google Cloud Project",
                    "step2": "Aktiviere Search Console API, URL Inspection API und Indexing API",
                    "step3": "Erstelle einen Service Account und lade die JSON-Datei herunter",
                    "step4": "Füge den Service Account als Nutzer in der Search Console hinzu",
                    "step5": "Setze GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/key.json in backend/.env"
                }
            }
        
        try:
            # Get performance data for different time periods
            daily_stats = await self.get_daily_stats(days=30)
            top_queries = await self.get_top_queries(days=7, limit=10)
            top_pages = await self.get_top_pages(days=7, limit=10)
            device_breakdown = await self.get_device_breakdown(days=7)
            country_breakdown = await self.get_country_breakdown(days=7, limit=5)
            
            # Calculate week-over-week comparison
            current_week = await self.get_performance_data(
                start_date=(datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d"),
                end_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                dimensions=["date"]
            )
            
            previous_week = await self.get_performance_data(
                start_date=(datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%d"),
                end_date=(datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d"),
                dimensions=["date"]
            )
            
            # Calculate changes
            current_clicks = current_week.get("totals", {}).get("clicks", 0)
            previous_clicks = previous_week.get("totals", {}).get("clicks", 0)
            clicks_change = ((current_clicks - previous_clicks) / previous_clicks * 100) if previous_clicks > 0 else 0
            
            current_impressions = current_week.get("totals", {}).get("impressions", 0)
            previous_impressions = previous_week.get("totals", {}).get("impressions", 0)
            impressions_change = ((current_impressions - previous_impressions) / previous_impressions * 100) if previous_impressions > 0 else 0
            
            return {
                "configured": True,
                "site_url": SITE_URL,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "overview": {
                    "clicks_7d": current_clicks,
                    "clicks_change": round(clicks_change, 1),
                    "impressions_7d": current_impressions,
                    "impressions_change": round(impressions_change, 1),
                    "ctr_7d": current_week.get("totals", {}).get("ctr", 0),
                    "position_7d": current_week.get("totals", {}).get("position", 0)
                },
                "daily_stats": daily_stats.get("rows", []),
                "top_queries": top_queries.get("rows", []),
                "top_pages": top_pages.get("rows", []),
                "device_breakdown": device_breakdown.get("rows", []),
                "country_breakdown": country_breakdown.get("rows", [])
            }
            
        except Exception as e:
            logger.error(f"Dashboard summary error: {e}")
            return {
                "configured": True,
                "error": str(e)
            }


# Global service instance
_gsc_service: Optional[GoogleSearchConsoleService] = None


def get_gsc_service() -> GoogleSearchConsoleService:
    """Get or create GSC service instance"""
    global _gsc_service
    if _gsc_service is None:
        _gsc_service = GoogleSearchConsoleService()
    return _gsc_service
