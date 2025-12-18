#!/bin/bash
# Build script for Render deployment

set -e  # Exit on error

echo "🔨 Building ProjectAria Backend..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head

echo "✅ Build complete!"

