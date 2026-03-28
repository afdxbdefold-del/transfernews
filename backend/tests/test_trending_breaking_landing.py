"""
Test suite for Trending, Breaking, and Landing Page API endpoints
Tests the new TREND + BREAKING + SEO-LANDINGPAGE-SYSTEM features
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTrendingEndpoints:
    """Tests for /api/trending/* endpoints"""
    
    def test_trending_all_returns_valid_structure(self):
        """GET /api/trending/all - should return trending players and clubs"""
        response = requests.get(f"{BASE_URL}/api/trending/all")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "trending_players" in data, "Missing trending_players key"
        assert "trending_clubs" in data, "Missing trending_clubs key"
        assert "period_hours" in data, "Missing period_hours key"
        
        # Validate types
        assert isinstance(data["trending_players"], list), "trending_players should be a list"
        assert isinstance(data["trending_clubs"], list), "trending_clubs should be a list"
        assert isinstance(data["period_hours"], int), "period_hours should be an int"
        print(f"✓ Trending all: {len(data['trending_players'])} players, {len(data['trending_clubs'])} clubs")
    
    def test_trending_all_with_custom_hours(self):
        """GET /api/trending/all?hours=48 - should accept hours parameter"""
        response = requests.get(f"{BASE_URL}/api/trending/all", params={"hours": 48})
        assert response.status_code == 200
        
        data = response.json()
        assert data["period_hours"] == 48, f"Expected period_hours=48, got {data['period_hours']}"
        print("✓ Trending all with custom hours parameter works")
    
    def test_trending_players_only(self):
        """GET /api/trending/players - should return only trending players"""
        response = requests.get(f"{BASE_URL}/api/trending/players")
        assert response.status_code == 200
        
        data = response.json()
        assert "trending_players" in data, "Missing trending_players key"
        assert "period_hours" in data, "Missing period_hours key"
        # Should NOT have trending_clubs in this endpoint
        assert "trending_clubs" not in data, "Should not have trending_clubs in players endpoint"
        print(f"✓ Trending players: {len(data['trending_players'])} players")
    
    def test_trending_clubs_only(self):
        """GET /api/trending/clubs - should return only trending clubs"""
        response = requests.get(f"{BASE_URL}/api/trending/clubs")
        assert response.status_code == 200
        
        data = response.json()
        assert "trending_clubs" in data, "Missing trending_clubs key"
        assert "period_hours" in data, "Missing period_hours key"
        # Should NOT have trending_players in this endpoint
        assert "trending_players" not in data, "Should not have trending_players in clubs endpoint"
        print(f"✓ Trending clubs: {len(data['trending_clubs'])} clubs")


class TestBreakingEndpoint:
    """Tests for /api/breaking endpoint"""
    
    def test_breaking_news_returns_valid_structure(self):
        """GET /api/breaking - should return breaking news articles"""
        response = requests.get(f"{BASE_URL}/api/breaking")
        assert response.status_code == 200
        
        data = response.json()
        assert "breaking_news" in data, "Missing breaking_news key"
        assert "count" in data, "Missing count key"
        assert isinstance(data["breaking_news"], list), "breaking_news should be a list"
        assert isinstance(data["count"], int), "count should be an int"
        assert data["count"] == len(data["breaking_news"]), "count should match list length"
        print(f"✓ Breaking news: {data['count']} articles")
    
    def test_breaking_news_with_limit(self):
        """GET /api/breaking?limit=3 - should respect limit parameter"""
        response = requests.get(f"{BASE_URL}/api/breaking", params={"limit": 3})
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["breaking_news"]) <= 3, "Should respect limit parameter"
        print("✓ Breaking news limit parameter works")


class TestLandingPageEndpoints:
    """Tests for /api/landing/* SEO landing page endpoints"""
    
    def test_player_landing_404_for_nonexistent(self):
        """GET /api/landing/spieler/nonexistent-player - should return 404"""
        response = requests.get(f"{BASE_URL}/api/landing/spieler/nonexistent-player-xyz")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Player landing returns 404 for nonexistent player")
    
    def test_club_landing_404_for_nonexistent(self):
        """GET /api/landing/verein/nonexistent-club - should return 404"""
        response = requests.get(f"{BASE_URL}/api/landing/verein/nonexistent-club-xyz")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Club landing returns 404 for nonexistent club")
    
    def test_free_transfers_landing(self):
        """GET /api/landing/abloesefreie - should return free transfers data"""
        response = requests.get(f"{BASE_URL}/api/landing/abloesefreie")
        assert response.status_code == 200
        
        data = response.json()
        assert "title" in data, "Missing title key"
        assert "articles" in data, "Missing articles key"
        assert "count" in data, "Missing count key"
        assert data["title"] == "Ablösefreie Transfers", f"Unexpected title: {data['title']}"
        assert isinstance(data["articles"], list), "articles should be a list"
        print(f"✓ Free transfers landing: {data['count']} articles")
    
    def test_top_transfers_landing(self):
        """GET /api/landing/top-transfers - should return top transfers data"""
        response = requests.get(f"{BASE_URL}/api/landing/top-transfers")
        assert response.status_code == 200
        
        data = response.json()
        assert "title" in data, "Missing title key"
        assert "articles" in data, "Missing articles key"
        assert "count" in data, "Missing count key"
        assert data["title"] == "Top Transfers", f"Unexpected title: {data['title']}"
        print(f"✓ Top transfers landing: {data['count']} articles")
    
    def test_top_transfers_with_limit(self):
        """GET /api/landing/top-transfers?limit=5 - should respect limit"""
        response = requests.get(f"{BASE_URL}/api/landing/top-transfers", params={"limit": 5})
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["articles"]) <= 5, "Should respect limit parameter"
        print("✓ Top transfers limit parameter works")


class TestPublicNewsEndpoints:
    """Tests for /api/public/news endpoints"""
    
    def test_public_news_list(self):
        """GET /api/public/news - should return published news"""
        response = requests.get(f"{BASE_URL}/api/public/news")
        assert response.status_code == 200
        
        data = response.json()
        assert "articles" in data, "Missing articles key"
        assert "total" in data, "Missing total key"
        assert "skip" in data, "Missing skip key"
        assert "limit" in data, "Missing limit key"
        assert isinstance(data["articles"], list), "articles should be a list"
        print(f"✓ Public news: {data['total']} total articles, {len(data['articles'])} returned")
    
    def test_public_news_pagination(self):
        """GET /api/public/news?skip=5&limit=10 - should support pagination"""
        response = requests.get(f"{BASE_URL}/api/public/news", params={"skip": 5, "limit": 10})
        assert response.status_code == 200
        
        data = response.json()
        assert data["skip"] == 5, f"Expected skip=5, got {data['skip']}"
        assert data["limit"] == 10, f"Expected limit=10, got {data['limit']}"
        print("✓ Public news pagination works")
    
    def test_public_news_detail_404_for_nonexistent(self):
        """GET /api/public/news/nonexistent-slug - should return 404"""
        response = requests.get(f"{BASE_URL}/api/public/news/nonexistent-article-slug-xyz")
        assert response.status_code == 404
        print("✓ Public news detail returns 404 for nonexistent article")


class TestRelatedLinksEndpoint:
    """Tests for /api/articles/{id}/related-links endpoint"""
    
    def test_related_links_404_for_nonexistent(self):
        """GET /api/articles/nonexistent-id/related-links - should return 404"""
        response = requests.get(f"{BASE_URL}/api/articles/nonexistent-article-id/related-links")
        assert response.status_code == 404
        print("✓ Related links returns 404 for nonexistent article")


class TestExistingDataIntegration:
    """Integration tests using existing data in the database"""
    
    def test_get_published_articles_and_check_detail(self):
        """Get a published article and verify detail endpoint with related links"""
        # First get list of published articles
        list_response = requests.get(f"{BASE_URL}/api/public/news", params={"limit": 1})
        assert list_response.status_code == 200
        
        data = list_response.json()
        if data["total"] == 0:
            pytest.skip("No published articles available for testing")
        
        article = data["articles"][0]
        slug = article.get("slug")
        
        if not slug:
            pytest.skip("Article has no slug")
        
        # Get detail with related links
        detail_response = requests.get(f"{BASE_URL}/api/public/news/{slug}")
        assert detail_response.status_code == 200
        
        detail_data = detail_response.json()
        assert "related_links" in detail_data, "Detail should include related_links"
        assert isinstance(detail_data["related_links"], list), "related_links should be a list"
        
        # Validate related link structure if any exist
        for link in detail_data["related_links"]:
            assert "type" in link, "Link should have type"
            assert "name" in link, "Link should have name"
            assert "url" in link, "Link should have url"
            assert link["type"] in ["player", "club"], f"Invalid link type: {link['type']}"
        
        print(f"✓ Article detail with {len(detail_data['related_links'])} related links")


class TestHealthAndBasicEndpoints:
    """Basic health and sanity checks"""
    
    def test_health_endpoint(self):
        """GET /api/health - should return healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
