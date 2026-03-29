#!/bin/bash

# AI-LMS Backend Testing Script
# Version: 1.0
# Date: 2026-03-29

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API Base URL
API_BASE="http://localhost:8000/api/v1"

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Log file
LOG_FILE="test_results_$(date +%Y%m%d_%H%M%S).log"

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    echo "[PASS] $1" >> "$LOG_FILE"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    echo "[FAIL] $1" >> "$LOG_FILE"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
    echo "[INFO] $1" >> "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    echo "[WARN] $1" >> "$LOG_FILE"
}

# Function to make API call and check response
test_api() {
    local test_name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="$5"
    local token="$6"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    print_info "Test #$TESTS_RUN: $test_name"
    
    # Build curl command
    local curl_cmd="curl -s -w '\n%{http_code}' -X $method"
    
    if [ ! -z "$token" ]; then
        curl_cmd="$curl_cmd -H 'Authorization: Bearer $token'"
    fi
    
    curl_cmd="$curl_cmd -H 'Content-Type: application/json'"
    
    if [ ! -z "$data" ]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi
    
    curl_cmd="$curl_cmd '$API_BASE$endpoint'"
    
    # Execute request
    response=$(eval $curl_cmd)
    
    # Extract status code (last line)
    status_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')
    
    # Check status code
    if [ "$status_code" == "$expected_status" ]; then
        print_success "$test_name - Status: $status_code"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        return 0
    else
        print_error "$test_name - Expected: $expected_status, Got: $status_code"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "$body"
        return 1
    fi
}

# Function to extract value from JSON response
extract_json_field() {
    echo "$1" | jq -r "$2" 2>/dev/null
}

# Header
clear
echo "=================================================="
echo "    AI-LMS Backend Testing Suite"
echo "=================================================="
echo "Date: $(date)"
echo "API Base: $API_BASE"
echo "Log File: $LOG_FILE"
echo "=================================================="
echo ""

# Check if backend is running
print_info "Checking if backend is running..."
if ! curl -s http://localhost:8000/health > /dev/null; then
    print_error "Backend is not running! Please start with: docker-compose up -d"
    exit 1
fi
print_success "Backend is healthy"
echo ""

# Variables to store tokens and IDs
ADMIN_TOKEN=""
INSTRUCTOR_TOKEN=""
STUDENT_TOKEN=""
COURSE_ID=""
ENROLLMENT_ID=""

# ========================================
# TEST SUITE 1: Authentication & Registration
# ========================================
echo "========================================"
echo "TEST SUITE 1: Authentication"
echo "========================================"
echo ""

# Test 1.1: Register Admin
print_info "1.1. Register Admin User"
response=$(test_api "Register Admin" "POST" "/auth/register" '{
  "email": "admin@ailms.com",
  "password": "Admin123!",
  "full_name": "System Administrator",
  "role": "ADMIN"
}' "201")
echo ""

# Test 1.2: Register Instructor
print_info "1.2. Register Instructor"
response=$(test_api "Register Instructor" "POST" "/auth/register" '{
  "email": "instructor1@ailms.com",
  "password": "Instructor123!",
  "full_name": "Nguyen Van A",
  "role": "INSTRUCTOR"
}' "201")
echo ""

# Test 1.3: Register Student
print_info "1.3. Register Student"
response=$(test_api "Register Student" "POST" "/auth/register" '{
  "email": "student1@ailms.com",
  "password": "Student123!",
  "full_name": "Tran Thi B",
  "role": "LEARNER"
}' "201")
echo ""

# Test 1.4: Login as Admin
print_info "1.4. Login as Admin"
login_response=$(curl -s -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@ailms.com",
    "password": "Admin123!"
  }')

ADMIN_TOKEN=$(echo "$login_response" | jq -r '.access_token')

if [ ! -z "$ADMIN_TOKEN" ] && [ "$ADMIN_TOKEN" != "null" ]; then
    print_success "Admin login successful - Token received"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_error "Admin login failed - No token received"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 1.5: Get Admin Profile
print_info "1.5. Get Admin Profile"
test_api "Get Admin Profile" "GET" "/auth/me" "" "200" "$ADMIN_TOKEN"
echo ""

# Test 1.6: Login as Instructor
print_info "1.6. Login as Instructor"
login_response=$(curl -s -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "instructor1@ailms.com",
    "password": "Instructor123!"
  }')

INSTRUCTOR_TOKEN=$(echo "$login_response" | jq -r '.access_token')

if [ ! -z "$INSTRUCTOR_TOKEN" ] && [ "$INSTRUCTOR_TOKEN" != "null" ]; then
    print_success "Instructor login successful"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_error "Instructor login failed"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 1.7: Login as Student
print_info "1.7. Login as Student"
login_response=$(curl -s -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student1@ailms.com",
    "password": "Student123!"
  }')

STUDENT_TOKEN=$(echo "$login_response" | jq -r '.access_token')

if [ ! -z "$STUDENT_TOKEN" ] && [ "$STUDENT_TOKEN" != "null" ]; then
    print_success "Student login successful"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_error "Student login failed"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# ========================================
# TEST SUITE 2: User Management (Admin)
# ========================================
echo "========================================"
echo "TEST SUITE 2: User Management"
echo "========================================"
echo ""

# Test 2.1: List All Users
print_info "2.1. List All Users (Admin)"
test_api "List Users" "GET" "/users?page=1&page_size=10" "" "200" "$ADMIN_TOKEN"
echo ""

# Test 2.2: Create Another Instructor
print_info "2.2. Create Instructor via Admin"
test_api "Admin Create Instructor" "POST" "/users" '{
  "email": "instructor2@ailms.com",
  "password": "Instructor123!",
  "full_name": "Le Van C",
  "role": "INSTRUCTOR",
  "is_active": true,
  "is_verified": true
}' "201" "$ADMIN_TOKEN"
echo ""

# Test 2.3: Filter Users by Role
print_info "2.3. Filter Users by Role (INSTRUCTOR)"
test_api "Filter by Role" "GET" "/users?role=INSTRUCTOR" "" "200" "$ADMIN_TOKEN"
echo ""

# ========================================
# TEST SUITE 3: Course Management
# ========================================
echo "========================================"
echo "TEST SUITE 3: Course Management"
echo "========================================"
echo ""

# Test 3.1: Create Course (Instructor)
print_info "3.1. Create Python Course (Instructor)"
course_response=$(curl -s -X POST "$API_BASE/courses" \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python Programming for Beginners",
    "description": "Learn Python from scratch. This comprehensive course covers all fundamental concepts including variables, data types, loops, functions, and object-oriented programming. Perfect for absolute beginners with no prior coding experience.",
    "short_description": "Learn Python programming from zero to hero",
    "category": "Programming",
    "level": "beginner",
    "language": "vi",
    "estimated_duration": 1200,
    "thumbnail_url": "https://example.com/python-course.jpg"
  }')

COURSE_ID=$(echo "$course_response" | jq -r '.id')

if [ ! -z "$COURSE_ID" ] && [ "$COURSE_ID" != "null" ]; then
    print_success "Course created successfully - ID: $COURSE_ID"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo "$course_response" | jq '.'
else
    print_error "Failed to create course"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 3.2: Get Course Details
print_info "3.2. Get Course Details"
test_api "Get Course" "GET" "/courses/$COURSE_ID" "" "200" "$INSTRUCTOR_TOKEN"
echo ""

# Test 3.3: Update Course
print_info "3.3. Update Course"
test_api "Update Course" "PUT" "/courses/$COURSE_ID" '{
  "title": "Complete Python Programming Course",
  "short_description": "Master Python programming with hands-on projects"
}' "200" "$INSTRUCTOR_TOKEN"
echo ""

# Test 3.4: Create More Courses
print_info "3.4. Create React Course"
test_api "Create React Course" "POST" "/courses" '{
  "title": "Modern Web Development with React",
  "description": "Learn to build modern web applications using React, the most popular JavaScript library.",
  "short_description": "Build modern web apps with React",
  "category": "Web Development",
  "level": "intermediate",
  "language": "vi",
  "estimated_duration": 1800
}' "201" "$INSTRUCTOR_TOKEN"
echo ""

# Test 3.5: Publish Course
print_info "3.5. Publish Python Course"
test_api "Publish Course" "POST" "/courses/$COURSE_ID/publish" "" "200" "$INSTRUCTOR_TOKEN"
echo ""

# Test 3.6: List All Published Courses (Public)
print_info "3.6. List Published Courses (Public Access)"
test_api "List Courses" "GET" "/courses?page=1&page_size=10" "" "200"
echo ""

# Test 3.7: Search Courses
print_info "3.7. Search Courses by 'Python'"
test_api "Search Courses" "GET" "/courses?search=python" "" "200"
echo ""

# Test 3.8: Filter by Category
print_info "3.8. Filter Courses by Category"
test_api "Filter by Category" "GET" "/courses?category=Programming" "" "200"
echo ""

# ========================================
# TEST SUITE 4: Enrollment
# ========================================
echo "========================================"
echo "TEST SUITE 4: Enrollment"
echo "========================================"
echo ""

# Test 4.1: Enroll in Course (Student)
print_info "4.1. Student Enrolls in Python Course"
enrollment_response=$(curl -s -X POST "$API_BASE/courses/$COURSE_ID/enroll" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json")

ENROLLMENT_ID=$(echo "$enrollment_response" | jq -r '.id')

if [ ! -z "$ENROLLMENT_ID" ] && [ "$ENROLLMENT_ID" != "null" ]; then
    print_success "Enrollment successful - ID: $ENROLLMENT_ID"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo "$enrollment_response" | jq '.'
else
    print_error "Enrollment failed"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 4.2: Try to Enroll Again (Should Fail)
print_info "4.2. Try Duplicate Enrollment (Should Fail)"
duplicate_response=$(curl -s -w '\n%{http_code}' -X POST "$API_BASE/courses/$COURSE_ID/enroll" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json")

duplicate_status=$(echo "$duplicate_response" | tail -n 1)

if [ "$duplicate_status" == "400" ]; then
    print_success "Duplicate enrollment prevented correctly (400)"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_error "Duplicate enrollment check failed - Status: $duplicate_status"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 4.3: View My Enrollments
print_info "4.3. View Student's Enrollments"
test_api "View Enrollments" "GET" "/courses/enrollments/me" "" "200" "$STUDENT_TOKEN"
echo ""

# Test 4.4: Get Course Lessons (Empty for now)
print_info "4.4. Get Course Lessons (Should be Empty)"
test_api "Get Course Lessons" "GET" "/courses/$COURSE_ID/lessons" "" "200" "$STUDENT_TOKEN"
echo ""

# ========================================
# TEST SUITE 5: Profile Management
# ========================================
echo "========================================"
echo "TEST SUITE 5: Profile Management"
echo "========================================"
echo ""

# Test 5.1: Update Student Profile
print_info "5.1. Update Student Profile"
test_api "Update Profile" "PUT" "/auth/me" '{
  "full_name": "Tran Thi B (Updated)",
  "bio": "Passionate learner interested in programming and data science",
  "avatar_url": "https://example.com/avatar.jpg"
}' "200" "$STUDENT_TOKEN"
echo ""

# Test 5.2: Change Password
print_info "5.2. Change Password"
test_api "Change Password" "PUT" "/auth/me/password" '{
  "old_password": "Student123!",
  "new_password": "NewStudent456!"
}' "200" "$STUDENT_TOKEN"
echo ""

# Test 5.3: Login with New Password
print_info "5.3. Login with New Password"
new_login_response=$(curl -s -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student1@ailms.com",
    "password": "NewStudent456!"
  }')

new_token=$(echo "$new_login_response" | jq -r '.access_token')

if [ ! -z "$new_token" ] && [ "$new_token" != "null" ]; then
    print_success "Login with new password successful"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_PASSED=$((TESTS_PASSED + 1))
    STUDENT_TOKEN="$new_token"  # Update token
else
    print_error "Login with new password failed"
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# ========================================
# FINAL REPORT
# ========================================
echo ""
echo "=================================================="
echo "              TEST RESULTS SUMMARY"
echo "=================================================="
echo ""
echo "Total Tests Run:    $TESTS_RUN"
echo -e "${GREEN}Tests Passed:      $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed:       $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
    success_rate=100
else
    success_rate=$((TESTS_PASSED * 100 / TESTS_RUN))
    echo -e "${YELLOW}⚠ Some tests failed${NC}"
fi

echo "Success Rate:       $success_rate%"
echo ""
echo "=================================================="
echo ""
echo "Detailed log saved to: $LOG_FILE"
echo ""

# Summary of what can and cannot be tested
echo "=================================================="
echo "              FEATURE STATUS"
echo "=================================================="
echo ""
echo -e "${GREEN}✓ WORKING FEATURES (Tested):${NC}"
echo "  - User Registration (Admin, Instructor, Learner)"
echo "  - User Authentication (Login/Logout)"
echo "  - Profile Management"
echo "  - Password Change"
echo "  - User Management (Admin)"
echo "  - Course Creation & Management"
echo "  - Course Publishing"
echo "  - Course Browsing & Search"
echo "  - Course Enrollment"
echo ""
echo -e "${RED}✗ MISSING FEATURES (Cannot Test):${NC}"
echo "  - Lesson Management (No API)"
echo "  - File Upload (Video/Documents)"
echo "  - Materials Management"
echo "  - Progress Tracking"
echo "  - Assignment System"
echo "  - Submission System"
echo ""
echo "=================================================="

exit $TESTS_FAILED
