cd /Users/jeffreyvonrotz/SynologyDrive/Projects/ThreatModelingPipeline

# Update the root package.json to use the venv Python
cat > package.json << 'EOF'
{
  "name": "threat-modeling-platform",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "concurrently \"npm run dev:api\" \"npm run dev:web\"",
    "dev:api": "cd apps/api && source venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000",
    "dev:web": "cd apps/web && npm run dev",
    "build": "cd apps/web && npm run build"
  },
  "devDependencies": {
    "concurrently": "^8.2.2"
  }
}
EOF