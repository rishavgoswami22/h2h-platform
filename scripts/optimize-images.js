#!/usr/bin/env node

/**
 * @deprecated Use Python optimizer: npm run optimize-images
 * See scripts/optimize_images_to_webp.py
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PUBLIC_DIR = path.join(__dirname, '..', 'public');
const SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'];

// Check if sharp is installed
try {
  require.resolve('sharp');
} catch (e) {
  console.log('Installing sharp for image optimization...');
  execSync('npm install sharp --save-dev', { stdio: 'inherit' });
}

const sharp = require('sharp');

async function convertToWebP(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (!SUPPORTED_EXTENSIONS.includes(ext)) return null;

  const webpPath = filePath.replace(ext, '.webp');
  
  // Skip if WebP already exists and is newer
  if (fs.existsSync(webpPath)) {
    const originalStat = fs.statSync(filePath);
    const webpStat = fs.statSync(webpPath);
    if (webpStat.mtime > originalStat.mtime) {
      console.log(`  ⏭️  Skipping (up to date): ${path.basename(filePath)}`);
      return null;
    }
  }

  try {
    const originalSize = fs.statSync(filePath).size;
    
    await sharp(filePath)
      .webp({ quality: 85, effort: 6 })
      .toFile(webpPath);
    
    const webpSize = fs.statSync(webpPath).size;
    const savings = ((1 - webpSize / originalSize) * 100).toFixed(1);
    
    console.log(`  ✅ Converted: ${path.basename(filePath)} → ${path.basename(webpPath)} (${savings}% smaller)`);
    return { original: filePath, webp: webpPath, savings };
  } catch (error) {
    console.error(`  ❌ Error converting ${filePath}:`, error.message);
    return null;
  }
}

async function processDirectory(dir) {
  const results = [];
  const items = fs.readdirSync(dir);

  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      // Recursively process subdirectories
      const subResults = await processDirectory(fullPath);
      results.push(...subResults);
    } else if (stat.isFile()) {
      const result = await convertToWebP(fullPath);
      if (result) results.push(result);
    }
  }

  return results;
}

async function main() {
  console.log('\n🖼️  Image Optimization Script');
  console.log('================================\n');
  console.log(`📁 Scanning: ${PUBLIC_DIR}\n`);

  if (!fs.existsSync(PUBLIC_DIR)) {
    console.error('❌ Public directory not found!');
    process.exit(1);
  }

  const results = await processDirectory(PUBLIC_DIR);

  console.log('\n================================');
  console.log(`✨ Optimization complete!`);
  console.log(`   ${results.length} images converted to WebP`);
  
  if (results.length > 0) {
    const totalSavings = results.reduce((acc, r) => acc + parseFloat(r.savings), 0) / results.length;
    console.log(`   Average size reduction: ${totalSavings.toFixed(1)}%`);
  }
  
  console.log('\n💡 Tip: Update your code to use .webp versions for better performance!\n');
}

main().catch(console.error);
