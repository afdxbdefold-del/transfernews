#!/usr/bin/env python3
"""
TransferNews.de Backend API Testing
Comprehensive test suite for the German football transfer news platform
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class TransferNewsAPITester:
    def __init__(self, base_url="https://deploy-transfers.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response_sample"] = str(response_data)[:200] + "..." if len(str(response_data)) > 200 else str(response_data)
        
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return success status and response"""
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"status_code": response.status_code, "text": response.text[:200]}

            return success, response_data

        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        # Test root endpoint
        success, data = self.make_request('GET', '/')
        self.log_result("API Root Endpoint", success, f"Status: {data.get('message', 'No message')}", data)
        
        # Test health endpoint
        success, data = self.make_request('GET', '/health')
        self.log_result("Health Check Endpoint", success, f"Status: {data.get('status', 'Unknown')}", data)

    def test_admin_login(self):
        """Test admin authentication"""
        print("\n🔍 Testing Admin Authentication...")
        
        # Test login with correct credentials
        login_data = {
            "email": "admin@transfernews.de",
            "password": "admin123"
        }
        
        success, data = self.make_request('POST', '/auth/login', login_data)
        if success and 'access_token' in data:
            self.token = data['access_token']
            self.log_result("Admin Login", True, "Successfully authenticated and got token")
            
            # Test getting current user info
            success, user_data = self.make_request('GET', '/auth/me')
            self.log_result("Get Current User", success, f"User: {user_data.get('email', 'Unknown')}", user_data)
        else:
            self.log_result("Admin Login", False, "Failed to authenticate", data)

    def test_players_crud(self):
        """Test Players CRUD operations"""
        print("\n🔍 Testing Players CRUD...")
        
        # Get players list
        success, data = self.make_request('GET', '/players')
        self.log_result("Get Players List", success, f"Found {len(data) if isinstance(data, list) else 0} players", data)
        
        if not self.token:
            self.log_result("Players CRUD (Create/Update/Delete)", False, "No auth token - skipping write operations")
            return
        
        # Create a test player
        test_player = {
            "name": "Test Spieler",
            "slug": "test-spieler",
            "country": "Deutschland",
            "position": "Mittelfeld",
            "aliases": ["Test Player"]
        }
        
        success, player_data = self.make_request('POST', '/players', test_player, 200)
        if success:
            player_id = player_data.get('id')
            self.log_result("Create Player", True, f"Created player with ID: {player_id}")
            
            # Test get player by ID
            success, get_data = self.make_request('GET', f'/players/{player_id}')
            self.log_result("Get Player by ID", success, f"Retrieved player: {get_data.get('name', 'Unknown')}")
            
            # Test update player
            update_data = {"position": "Sturm"}
            success, update_result = self.make_request('PUT', f'/players/{player_id}', update_data)
            self.log_result("Update Player", success, f"Updated position to: {update_result.get('position', 'Unknown')}")
            
            # Test delete player
            success, delete_result = self.make_request('DELETE', f'/players/{player_id}')
            self.log_result("Delete Player", success, "Player deleted successfully")
        else:
            self.log_result("Create Player", False, "Failed to create test player", player_data)

    def test_clubs_crud(self):
        """Test Clubs CRUD operations"""
        print("\n🔍 Testing Clubs CRUD...")
        
        # Get clubs list
        success, data = self.make_request('GET', '/clubs')
        self.log_result("Get Clubs List", success, f"Found {len(data) if isinstance(data, list) else 0} clubs", data)
        
        if not self.token:
            self.log_result("Clubs CRUD (Create/Update/Delete)", False, "No auth token - skipping write operations")
            return
        
        # Create a test club
        test_club = {
            "name": "Test Verein",
            "slug": "test-verein",
            "country": "Deutschland",
            "aliases": ["Test Club"]
        }
        
        success, club_data = self.make_request('POST', '/clubs', test_club, 200)
        if success:
            club_id = club_data.get('id')
            self.log_result("Create Club", True, f"Created club with ID: {club_id}")
            
            # Test get club by ID
            success, get_data = self.make_request('GET', f'/clubs/{club_id}')
            self.log_result("Get Club by ID", success, f"Retrieved club: {get_data.get('name', 'Unknown')}")
            
            # Test delete club
            success, delete_result = self.make_request('DELETE', f'/clubs/{club_id}')
            self.log_result("Delete Club", success, "Club deleted successfully")
        else:
            self.log_result("Create Club", False, "Failed to create test club", club_data)

    def test_competitions_crud(self):
        """Test Competitions CRUD operations"""
        print("\n🔍 Testing Competitions CRUD...")
        
        # Get competitions list
        success, data = self.make_request('GET', '/competitions')
        self.log_result("Get Competitions List", success, f"Found {len(data) if isinstance(data, list) else 0} competitions", data)
        
        if not self.token:
            return
        
        # Create a test competition
        test_competition = {
            "name": "Test Liga",
            "slug": "test-liga",
            "country": "Deutschland",
            "type": "league"
        }
        
        success, comp_data = self.make_request('POST', '/competitions', test_competition, 200)
        if success:
            comp_id = comp_data.get('id')
            self.log_result("Create Competition", True, f"Created competition with ID: {comp_id}")
            
            # Test delete competition
            success, delete_result = self.make_request('DELETE', f'/competitions/{comp_id}')
            self.log_result("Delete Competition", success, "Competition deleted successfully")
        else:
            self.log_result("Create Competition", False, "Failed to create test competition", comp_data)

    def test_articles_crud(self):
        """Test Articles CRUD operations"""
        print("\n🔍 Testing Articles CRUD...")
        
        # Get published articles
        success, data = self.make_request('GET', '/articles/published')
        self.log_result("Get Published Articles", success, f"Found {len(data) if isinstance(data, list) else 0} published articles", data)
        
        # Get breaking news
        success, breaking_data = self.make_request('GET', '/articles/breaking')
        self.log_result("Get Breaking News", success, f"Found {len(breaking_data) if isinstance(breaking_data, list) else 0} breaking news", breaking_data)
        
        if not self.token:
            return
        
        # Create a test article
        test_article = {
            "title": "Test Artikel",
            "slug": "test-artikel",
            "excerpt": "Dies ist ein Test-Artikel",
            "body": "Vollständiger Artikel-Inhalt hier...",
            "article_type": "news",
            "status": "draft"
        }
        
        success, article_data = self.make_request('POST', '/articles', test_article, 200)
        if success:
            article_id = article_data.get('id')
            self.log_result("Create Article", True, f"Created article with ID: {article_id}")
            
            # Test update article to published
            update_data = {"status": "published"}
            success, update_result = self.make_request('PUT', f'/articles/{article_id}', update_data)
            self.log_result("Publish Article", success, f"Article status: {update_result.get('status', 'Unknown')}")
            
            # Test delete article
            success, delete_result = self.make_request('DELETE', f'/articles/{article_id}')
            self.log_result("Delete Article", success, "Article deleted successfully")
        else:
            self.log_result("Create Article", False, "Failed to create test article", article_data)

    def test_ad_slots(self):
        """Test Ad Slots functionality"""
        print("\n🔍 Testing Ad Slots...")
        
        # Get all ad slots
        success, data = self.make_request('GET', '/ad-slots')
        self.log_result("Get All Ad Slots", success, f"Found {len(data) if isinstance(data, list) else 0} ad slots", data)
        
        # Get active ad slots
        success, active_data = self.make_request('GET', '/ad-slots/active')
        self.log_result("Get Active Ad Slots", success, f"Found {len(active_data) if isinstance(active_data, list) else 0} active ad slots", active_data)

    def test_search_functionality(self):
        """Test Search endpoints"""
        print("\n🔍 Testing Search Functionality...")
        
        # Test search with a common term
        success, data = self.make_request('GET', '/search?q=test&limit=10')
        self.log_result("Global Search", success, f"Search results structure: {list(data.keys()) if isinstance(data, dict) else 'Invalid'}", data)
        
        # Test autosuggest
        success, suggest_data = self.make_request('GET', '/search/autosuggest?q=test&limit=5')
        self.log_result("Autosuggest Search", success, f"Found {len(suggest_data) if isinstance(suggest_data, list) else 0} suggestions", suggest_data)

    def test_dashboard_stats(self):
        """Test Dashboard Statistics"""
        print("\n🔍 Testing Dashboard Stats...")
        
        if not self.token:
            self.log_result("Dashboard Stats", False, "No auth token - cannot access admin endpoints")
            return
        
        success, data = self.make_request('GET', '/stats/dashboard')
        if success and isinstance(data, dict):
            stats_summary = {k: v for k, v in data.items() if isinstance(v, (int, float))}
            self.log_result("Dashboard Stats", True, f"Stats: {stats_summary}", data)
        else:
            self.log_result("Dashboard Stats", False, "Failed to get dashboard stats", data)

    def test_initialization_endpoints(self):
        """Test Initialization endpoints"""
        print("\n🔍 Testing Initialization Endpoints...")
        
        # Test admin initialization (should already exist)
        success, data = self.make_request('POST', '/init/admin')
        self.log_result("Initialize Admin", success, data.get('message', 'No message'), data)
        
        if not self.token:
            return
        
        # Test ad slots initialization
        success, ad_data = self.make_request('POST', '/init/ad-slots')
        self.log_result("Initialize Ad Slots", success, ad_data.get('message', 'No message'), ad_data)

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting TransferNews.de Backend API Tests")
        print(f"🎯 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run test suites in order
        self.test_health_check()
        self.test_admin_login()
        self.test_players_crud()
        self.test_clubs_crud()
        self.test_competitions_crud()
        self.test_articles_crud()
        self.test_ad_slots()
        self.test_search_functionality()
        self.test_dashboard_stats()
        self.test_initialization_endpoints()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test runner"""
    tester = TransferNewsAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/tmp/backend_test_results.json', 'w') as f:
        json.dump({
            'summary': {
                'total_tests': tester.tests_run,
                'passed_tests': tester.tests_passed,
                'failed_tests': tester.tests_run - tester.tests_passed,
                'success_rate': (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0
            },
            'results': tester.test_results,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())