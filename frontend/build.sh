#!/bin/bash
# Build script for Render deployment

set -e  # Exit on error

echo "🔨 Building ProjectAria Frontend..."

# Install dependencies
echo "📦 Installing npm dependencies..."
npm install

# Build the application
echo "🏗️  Building production bundle..."
npm run build

echo "✅ Build complete! Output in dist/"

