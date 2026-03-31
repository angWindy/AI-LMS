#!/bin/bash

# AI-LMS Deployment Script
# Tự động triển khai dự án AI-LMS

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print functions
print_step() {
    echo -e "${GREEN}==>${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    print_step "BƯỚC 1: Kiểm tra Docker..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker chưa được cài đặt!"
        echo "Cài đặt Docker bằng lệnh:"
        echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
        echo "  sudo sh get-docker.sh"
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null; then
        print_error "Docker Compose chưa được cài đặt!"
        exit 1
    fi
    
    print_info "Docker version: $(docker --version)"
    print_info "Docker Compose version: $(docker compose version)"
    print_success "Docker đã sẵn sàng!"
    echo ""
}

# Check if in project directory
check_directory() {
    print_step "BƯỚC 2: Kiểm tra thư mục dự án..."
    
    if [ ! -f "docker-compose.prod.yml" ]; then
        print_error "Không tìm thấy file docker-compose.prod.yml"
        echo "Hãy chạy script này từ thư mục gốc của dự án AI-LMS"
        exit 1
    fi
    
    print_success "Đang ở đúng thư mục dự án!"
    echo ""
}

# Create .env file if not exists
create_env_file() {
    print_step "BƯỚC 3: Cấu hình môi trường..."
    
    if [ -f ".env" ]; then
        print_info "File .env đã tồn tại, giữ nguyên cấu hình cũ"
    else
        print_info "Tạo file .env mới..."
        cat > .env << 'EOF'
# Database Configuration
DB_USER=lms_user
DB_PASSWORD=lms_password_123
DB_NAME=lms_db
DB_HOST=db
DB_PORT=5432

# Backend Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production-at-least-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost,http://localhost:80,http://localhost:3000

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000
EOF
        print_success "File .env đã được tạo!"
    fi
    echo ""
}

# Stop existing containers
stop_existing() {
    print_step "BƯỚC 4: Dừng containers cũ (nếu có)..."
    
    docker compose -f docker-compose.prod.yml down 2>/dev/null || true
    print_success "Đã dừng containers cũ!"
    echo ""
}

# Build Docker images
build_images() {
    print_step "BƯỚC 5: Build Docker images..."
    print_info "Quá trình này có thể mất 5-10 phút..."
    
    docker compose -f docker-compose.prod.yml build
    print_success "Build hoàn tất!"
    echo ""
}

# Start services
start_services() {
    print_step "BƯỚC 6: Khởi động services..."
    
    docker compose -f docker-compose.prod.yml up -d
    print_success "Đã khởi động tất cả services!"
    echo ""
}

# Wait for services to be healthy
wait_for_services() {
    print_step "BƯỚC 7: Đợi services khởi động..."
    
    print_info "Đợi database..."
    sleep 5
    
    print_info "Đợi backend..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker compose -f docker-compose.prod.yml ps backend | grep -q "healthy"; then
            print_success "Backend đã sẵn sàng!"
            break
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "Backend không khởi động được!"
        docker compose -f docker-compose.prod.yml logs backend
        exit 1
    fi
    
    echo ""
}

# Create default users
create_users() {
    print_step "BƯỚC 8: Tạo tài khoản mặc định..."
    
    docker compose -f docker-compose.prod.yml exec -T backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
from app.utils.auth import get_password_hash

db = SessionLocal()

users_data = [
    {'email': 'admin@test.com', 'full_name': 'Admin User', 'password': '00000000', 'role': 'admin'},
    {'email': 'teacher@test.com', 'full_name': 'Teacher User', 'password': '00000000', 'role': 'instructor'},
    {'email': 'student@test.com', 'full_name': 'Student User', 'password': '00000000', 'role': 'learner'}
]

for user_data in users_data:
    existing = db.query(User).filter(User.email == user_data['email']).first()
    if not existing:
        user = User(
            email=user_data['email'],
            full_name=user_data['full_name'],
            hashed_password=get_password_hash(user_data['password']),
            role=user_data['role'],
            is_active=True
        )
        db.add(user)
        print(f'✓ Created: {user_data[\"email\"]}')
    else:
        print(f'- Already exists: {user_data[\"email\"]}')

db.commit()
print('Done!')
" 2>/dev/null || print_info "Tài khoản đã tồn tại hoặc không thể tạo"
    
    echo ""
}

# Show status
show_status() {
    print_step "BƯỚC 9: Kiểm tra trạng thái..."
    
    echo ""
    docker compose -f docker-compose.prod.yml ps
    echo ""
}

# Print access information
print_access_info() {
    print_success "========================================="
    print_success "  🎉 TRIỂN KHAI THÀNH CÔNG! 🎉"
    print_success "========================================="
    echo ""
    echo "📍 Truy cập ứng dụng tại:"
    echo "   Frontend:  http://localhost"
    echo "   API Docs:  http://localhost/api/docs"
    echo ""
    echo "🔑 Tài khoản đăng nhập:"
    echo "   Admin:    admin@test.com / 00000000"
    echo "   Teacher:  teacher@test.com / 00000000"
    echo "   Student:  student@test.com / 00000000"
    echo ""
    echo "📚 Xem hướng dẫn chi tiết tại: QUICK_START.md"
    echo ""
    echo "💡 Các lệnh hữu ích:"
    echo "   Xem logs:    docker compose -f docker-compose.prod.yml logs -f"
    echo "   Dừng:        docker compose -f docker-compose.prod.yml down"
    echo "   Restart:     docker compose -f docker-compose.prod.yml restart"
    echo ""
}

# Main execution
main() {
    echo ""
    echo "╔═══════════════════════════════════════╗"
    echo "║   AI-LMS Deployment Script v1.0       ║"
    echo "╚═══════════════════════════════════════╝"
    echo ""
    
    check_docker
    check_directory
    create_env_file
    stop_existing
    build_images
    start_services
    wait_for_services
    create_users
    show_status
    print_access_info
}

# Run main function
main
