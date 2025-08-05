#!/bin/bash

# Create directory structure
echo "Creating directory structure..."
mkdir -p apps/api/app/{api/endpoints,core/{llm,pipeline/steps},models,services}
mkdir -p apps/web/{app,components/{pipeline/steps,ui},lib,hooks}
mkdir -p packages

# Create root package.json
echo "Creating root package.json..."
cat > package.json << 'EOF'
{
  "name": "threat-modeling-platform",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "concurrently \"npm run dev:api\" \"npm run dev:web\"",
    "dev:api": "cd apps/api && uvicorn app.main:app --reload",
    "dev:web": "cd apps/web && npm run dev"
  },
  "devDependencies": {
    "concurrently": "^8.2.2"
  }
}
EOF

# Install root dependencies
echo "Installing root dependencies..."
npm install

# Setup frontend
echo "Setting up frontend..."
cd apps/web
npm init -y
npm install next react react-dom
npm install -D @types/node @types/react @types/react-dom typescript

# Setup backend
echo "Setting up backend..."
cd ../api
python3 -m venv venv
echo "Python virtual environment created. Activate it and run: pip install -r requirements.txt"

echo "Setup complete! Next steps:"
echo "1. Copy all the component files from the artifacts"
echo "2. Configure your .env files"
echo "3. Start Redis: docker run -d -p 6379:6379 redis:alpine"
echo "4. Run: npm run dev"