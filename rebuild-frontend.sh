#!/bin/bash

# AI-LMS Frontend Rebuild Script
# Tự động build và khởi động lại service frontend

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

# Check if in project directory
check_directory() {
    print_step "BƯỚC 1: Kiểm tra thư mục dự án..."
    
    if [ ! -f "docker-compose.prod.yml" ]; then
        print_error "Không tìm thấy file docker-compose.prod.yml"
        echo "Hãy chạy script này từ thư mục gốc của dự án AI-LMS"
        exit 1
    fi
    
    print_success "Đang ở đúng thư mục dự án!"
    echo ""
}

# Build Docker image for frontend
build_frontend_image() {
    print_step "BƯỚC 2: Build lại Docker image cho frontend..."
    print_info "Quá trình này có thể mất vài phút..."
    
    docker compose -f docker-compose.prod.yml build frontend
    
    print_success "Build image frontend hoàn tất!"
    echo ""
}

# Restart frontend service
restart_frontend_service() {
    print_step "BƯỚC 3: Khởi động lại service frontend..."
    
    docker compose -f docker-compose.prod.yml up -d --no-deps frontend
    
    print_success "Đã khởi động lại service frontend!"
    echo ""
}

# Main execution
main() {
    echo ""
    echo "╔═════════════════════════════════════════╗"
    echo "║   AI-LMS Frontend Rebuild Script v1.0   ║"
    echo "╚═════════════════════════════════════════╝"
    echo ""
    
    check_directory
    build_frontend_image
    restart_frontend_service
    
    echo ""
    print_success "=============================================="
    print_success "  🎉 REBUILD FRONTEND THÀNH CÔNG! 🎉"
    print_success "=============================================="
    echo ""
    echo "📍 Frontend đã được cập nhật."
    echo "   Hãy truy cập lại http://localhost để xem thay đổi."
    echo ""
}

# Run main function
main
