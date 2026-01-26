#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import uuid
import os

class MeowlsVisaAPITester:
    def __init__(self, base_url="https://evisa-meowls.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()  # Use session to handle cookies
        self.user_id = None
        self.application_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.session_token:
            test_headers['Authorization'] = f'Bearer {self.session_token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Response: {response.text[:100]}"
            
            self.log_test(name, success, details if not success else "")
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test user registration"""
        timestamp = int(datetime.now().timestamp())
        test_data = {
            "name": f"Test User {timestamp}",
            "email": f"test.user.{timestamp}@example.com",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_data
        )
        
        if success and 'user_id' in response:
            self.user_id = response['user_id']
            return True
        return False

    def test_user_login(self):
        """Test user login with existing credentials"""
        # First register a user
        timestamp = int(datetime.now().timestamp())
        register_data = {
            "name": f"Login Test User {timestamp}",
            "email": f"login.test.{timestamp}@example.com",
            "password": "TestPass123!"
        }
        
        # Register user
        success, _ = self.run_test(
            "Pre-Login Registration",
            "POST",
            "auth/register",
            200,
            data=register_data
        )
        
        if not success:
            return False
        
        # Now test login
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"]
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'user_id' in response:
            self.user_id = response['user_id']
            return True
        return False

    def test_get_current_user(self):
        """Test getting current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_create_application(self):
        """Test creating a visa application"""
        app_data = {
            "visa_type": "tourist",
            "personal_info": {
                "full_name": "John Doe",
                "date_of_birth": "1990-01-01",
                "nationality": "American",
                "passport_number": "A12345678",
                "passport_expiry": "2030-01-01",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "address": "123 Main St, City, Country"
            },
            "travel_details": {
                "purpose": "Tourism and sightseeing",
                "arrival_date": "2024-06-01",
                "departure_date": "2024-06-15",
                "accommodation": "Hotel Meowls, 456 Cat Street, Meowls City"
            }
        }
        
        success, response = self.run_test(
            "Create Visa Application",
            "POST",
            "applications",
            200,
            data=app_data
        )
        
        if success and 'application_id' in response:
            self.application_id = response['application_id']
            return True
        return False

    def test_get_applications(self):
        """Test getting user applications"""
        success, response = self.run_test(
            "Get User Applications",
            "GET",
            "applications",
            200
        )
        return success

    def test_get_application_details(self):
        """Test getting specific application details"""
        if not self.application_id:
            self.log_test("Get Application Details", False, "No application ID available")
            return False
        
        success, response = self.run_test(
            "Get Application Details",
            "GET",
            f"applications/{self.application_id}",
            200
        )
        return success

    def test_update_application(self):
        """Test updating an application"""
        if not self.application_id:
            self.log_test("Update Application", False, "No application ID available")
            return False
        
        update_data = {
            "visa_type": "business",
            "personal_info": {
                "full_name": "John Doe Updated",
                "date_of_birth": "1990-01-01",
                "nationality": "American",
                "passport_number": "A12345678",
                "passport_expiry": "2030-01-01",
                "email": "john.doe.updated@example.com",
                "phone": "+1234567890",
                "address": "123 Main St, City, Country"
            },
            "travel_details": {
                "purpose": "Business meetings and conferences",
                "arrival_date": "2024-07-01",
                "departure_date": "2024-07-15",
                "accommodation": "Business Hotel, 789 Business Ave, Meowls City"
            }
        }
        
        success, response = self.run_test(
            "Update Application",
            "PUT",
            f"applications/{self.application_id}",
            200,
            data=update_data
        )
        return success

    def test_submit_application(self):
        """Test submitting an application"""
        if not self.application_id:
            self.log_test("Submit Application", False, "No application ID available")
            return False
        
        success, response = self.run_test(
            "Submit Application",
            "POST",
            f"applications/{self.application_id}/submit",
            200
        )
        return success

    def test_admin_endpoints(self):
        """Test admin-only endpoints (should fail for regular user)"""
        success, response = self.run_test(
            "Admin Get All Applications (Should Fail)",
            "GET",
            "admin/applications",
            403  # Should be forbidden for regular user
        )
        return success

    def test_logout(self):
        """Test user logout"""
        success, response = self.run_test(
            "User Logout",
            "POST",
            "auth/logout",
            200
        )
        return success

    def test_invalid_endpoints(self):
        """Test invalid endpoints"""
        success, response = self.run_test(
            "Invalid Endpoint (Should 404)",
            "GET",
            "nonexistent/endpoint",
            404
        )
        return success

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Meowls e-Visa API Tests")
        print("=" * 50)
        
        # Test authentication flow
        print("\n📝 Testing Authentication...")
        self.test_user_registration()
        self.test_user_login()
        self.test_get_current_user()
        
        # Test application flow
        print("\n📋 Testing Application Management...")
        self.test_create_application()
        self.test_get_applications()
        self.test_get_application_details()
        self.test_update_application()
        self.test_submit_application()
        
        # Test admin endpoints (should fail)
        print("\n🔒 Testing Admin Access Control...")
        self.test_admin_endpoints()
        
        # Test logout
        print("\n🚪 Testing Logout...")
        self.test_logout()
        
        # Test invalid endpoints
        print("\n❓ Testing Error Handling...")
        self.test_invalid_endpoints()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    """Main test execution"""
    tester = MeowlsVisaAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())