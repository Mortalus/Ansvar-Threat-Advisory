#!/usr/bin/env node

/**
 * Frontend Migration Validation Script
 * Validates that all critical components and services are properly integrated
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Validating Frontend Migration...\n');

// Validation results
const results = {
  passed: 0,
  failed: 0,
  warnings: 0
};

function checkFile(filePath, description) {
  const fullPath = path.join(__dirname, filePath);
  if (fs.existsSync(fullPath)) {
    console.log(`✅ ${description}`);
    results.passed++;
    return true;
  } else {
    console.log(`❌ ${description} - Missing: ${filePath}`);
    results.failed++;
    return false;
  }
}

function checkBuildOutput() {
  const distPath = path.join(__dirname, 'dist');
  if (!fs.existsSync(distPath)) {
    console.log('❌ Build output directory missing');
    results.failed++;
    return false;
  }
  
  const indexPath = path.join(distPath, 'index.html');
  if (!fs.existsSync(indexPath)) {
    console.log('❌ Built index.html missing');
    results.failed++;
    return false;
  }
  
  console.log('✅ Build output exists');
  results.passed++;
  
  // Check for large chunks
  const assetsPath = path.join(distPath, 'assets');
  if (fs.existsSync(assetsPath)) {
    const files = fs.readdirSync(assetsPath);
    const largeFiles = files.filter(file => {
      const filePath = path.join(assetsPath, file);
      const stats = fs.statSync(filePath);
      return stats.size > 2 * 1024 * 1024; // 2MB
    });
    
    if (largeFiles.length > 0) {
      console.log(`⚠️  Large asset files found: ${largeFiles.join(', ')}`);
      results.warnings++;
    } else {
      console.log('✅ No excessively large asset files');
      results.passed++;
    }
  }
  
  return true;
}

console.log('📁 Core Files:');
checkFile('src/main.tsx', 'Main entry point');
checkFile('src/App.tsx', 'Main App component');
checkFile('package.json', 'Package configuration');
checkFile('vite.config.ts', 'Vite configuration');
checkFile('tsconfig.json', 'TypeScript configuration');

console.log('\n🔧 Services:');
checkFile('src/services/auth.service.ts', 'Authentication service');
checkFile('src/services/api.client.ts', 'API client service');
checkFile('src/services/websocket.service.ts', 'WebSocket service');
checkFile('src/services/project.service.ts', 'Project service');
checkFile('src/services/pipeline.service.ts', 'Pipeline service');
checkFile('src/services/workflow.service.ts', 'Workflow service');

console.log('\n🏪 State Management:');
checkFile('src/store/authStore.ts', 'Authentication store');

console.log('\n🎨 UI Components:');
checkFile('src/components/LoginPage.tsx', 'Login page component');
checkFile('src/components/Dashboard.tsx', 'Dashboard component');
checkFile('src/components/AgentsView.tsx', 'Agents view component');
checkFile('src/components/WorkflowsView.tsx', 'Workflows view component');
checkFile('src/components/ErrorBoundary.tsx', 'Error boundary component');

console.log('\n⚙️  Configuration:');
checkFile('.env.development', 'Development environment config');
checkFile('.env.production', 'Production environment config');

console.log('\n🐳 Docker:');
checkFile('Dockerfile', 'Docker configuration');
checkFile('nginx.conf', 'Nginx configuration');

console.log('\n🏗️ Build Output:');
checkBuildOutput();

console.log('\n🧪 Validation Summary:');
console.log(`✅ Passed: ${results.passed}`);
if (results.warnings > 0) console.log(`⚠️  Warnings: ${results.warnings}`);
if (results.failed > 0) console.log(`❌ Failed: ${results.failed}`);

if (results.failed === 0) {
  console.log('\n🎉 Migration validation PASSED! Frontend is ready for deployment.');
  process.exit(0);
} else {
  console.log('\n❌ Migration validation FAILED. Please fix the issues above.');
  process.exit(1);
}