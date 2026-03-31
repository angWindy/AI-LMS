#!/bin/bash
# Setup domain angwindy-ai-lms for local development
# Run: sudo ./setup-domain.sh

echo "🔧 Setting up angwindy-ai-lms domain..."
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Please run with sudo: sudo ./setup-domain.sh"
    exit 1
fi

# Add to /etc/hosts
if ! grep -q "angwindy-ai-lms" /etc/hosts; then
    echo "127.0.0.1 angwindy-ai-lms" >> /etc/hosts
    echo "✅ Added angwindy-ai-lms to /etc/hosts"
else
    echo "✅ angwindy-ai-lms already in /etc/hosts"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "You can now access:"
echo "  • http://angwindy-ai-lms"
echo "  • http://angwindy-ai-lms/docs"
echo ""
