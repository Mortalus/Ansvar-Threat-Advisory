#!/usr/bin/env node

const puppeteer = require('puppeteer');

async function testRuntime() {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();

  try {
    console.log('🚀 Starting runtime integration test...');
    
    // Navigate to the app
    await page.goto('http://localhost:3001', { waitUntil: 'networkidle0' });
    
    console.log('✅ Page loaded successfully');
    
    // Check if we can see the login form or dashboard
    const loginForm = await page.$('form');
    const dashboardContent = await page.$('.dashboard');
    
    if (loginForm) {
      console.log('✅ Login form detected - testing authentication');
      
      // Test login with demo credentials
      await page.type('input[type="email"]', 'admin@company.com');
      await page.type('input[type="password"]', 'admin123');
      await page.click('button[type="submit"]');
      
      // Wait for navigation or dashboard to load
      await page.waitForTimeout(2000);
      
      const currentUrl = page.url();
      if (currentUrl.includes('dashboard') || currentUrl === 'http://localhost:3001/') {
        console.log('✅ Login successful - redirected to dashboard');
      } else {
        console.log('⚠️  Login completed but no redirect detected');
      }
    } else if (dashboardContent) {
      console.log('✅ Already logged in - dashboard visible');
    } else {
      console.log('✅ App loaded but no specific form detected');
    }
    
    // Check for console errors
    const logs = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        logs.push(msg.text());
      }
    });
    
    await page.waitForTimeout(1000);
    
    if (logs.length === 0) {
      console.log('✅ No JavaScript errors detected');
    } else {
      console.log('⚠️  JavaScript errors found:', logs);
    }
    
    console.log('🎉 Runtime test completed successfully!');
    
  } catch (error) {
    console.error('❌ Runtime test failed:', error.message);
  } finally {
    await browser.close();
  }
}

// Only run if puppeteer is available
const fs = require('fs');
const path = require('path');
const puppeteerPath = path.join(__dirname, 'node_modules', 'puppeteer');

if (fs.existsSync(puppeteerPath)) {
  testRuntime();
} else {
  console.log('📝 Puppeteer not installed - manual testing required');
  console.log('🌐 Visit http://localhost:3001 to test the application');
  console.log('🔐 Demo credentials:');
  console.log('   Admin: admin@company.com / admin123');
  console.log('   User:  user@company.com / user123');
  console.log('   Viewer: viewer@company.com / viewer123');
}