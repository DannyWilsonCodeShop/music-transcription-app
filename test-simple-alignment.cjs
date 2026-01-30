// Simple test with TAB-BASED alignment - every 3 tabs = new downbeat
const { jsPDF } = require('jspdf');
const fs = require('fs');
const path = require('path');

function createTabAlignedTest() {
  const doc = new jsPDF();
  
  // Title
  doc.setFontSize(18);
  doc.setFont('helvetica', 'bold');
  doc.text('AMAZING GRACE - TAB ALIGNED', 20, 20);
  
  let yPos = 40;
  
  // Define tab positions - every 3 tabs = new downbeat
  const tab1 = 20;   // First downbeat
  const tab2 = 70;   // Second downbeat (3 tabs later)
  const tab3 = 120;  // Third downbeat (3 tabs later)
  const tab4 = 170;  // Fourth downbeat (3 tabs later)
  
  // Line 1: A-, Grace, sweet, sound
  doc.setFontSize(11);
  doc.setFont('helvetica', 'normal');
  doc.text('A-', tab1, yPos);
  doc.text('Grace,', tab2, yPos);
  doc.text('sweet', tab3, yPos);
  doc.text('sound', tab4, yPos);
  yPos += 6;
  
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(200, 0, 0);
  doc.text('1', tab1, yPos);     // Under "A-"
  doc.text('1', tab2, yPos);     // Under "Grace"
  doc.text('5', tab3, yPos);     // Under "sweet"
  doc.text('1', tab4, yPos);     // Under "sound"
  
  yPos += 15;
  
  // Line 2: saved, a, wretch, me
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(0, 0, 0);
  doc.text('saved', tab1, yPos);
  doc.text('a', tab2, yPos);
  doc.text('wretch', tab3, yPos);
  doc.text('me', tab4, yPos);
  yPos += 6;
  
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(200, 0, 0);
  doc.text('5', tab1, yPos);     // Under "saved"
  doc.text('6', tab2, yPos);     // Under "a"
  doc.text('4', tab3, yPos);     // Under "wretch"
  doc.text('1', tab4, yPos);     // Under "me"
  
  yPos += 15;
  
  // Line 3: once, lost, now, found
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(0, 0, 0);
  doc.text('once', tab1, yPos);
  doc.text('lost,', tab2, yPos);
  doc.text('now', tab3, yPos);
  doc.text('found', tab4, yPos);
  yPos += 6;
  
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(200, 0, 0);
  doc.text('1', tab1, yPos);     // Under "once"
  doc.text('1', tab2, yPos);     // Under "lost"
  doc.text('4', tab3, yPos);     // Under "now"
  doc.text('1', tab4, yPos);     // Under "found"
  
  yPos += 15;
  
  // Line 4: blind, now, see, (no word)
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(0, 0, 0);
  doc.text('blind,', tab1, yPos);
  doc.text('now', tab2, yPos);
  doc.text('see', tab3, yPos);
  doc.text('(rest)', tab4, yPos);
  yPos += 6;
  
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(200, 0, 0);
  doc.text('1', tab1, yPos);     // Under "blind"
  doc.text('5', tab2, yPos);     // Under "now"
  doc.text('1', tab3, yPos);     // Under "see"
  doc.text('1', tab4, yPos);     // (no word)
  
  // Save
  const pdfBuffer = Buffer.from(doc.output('arraybuffer'));
  const outputPath = path.join(__dirname, 'tab-aligned-test.pdf');
  fs.writeFileSync(outputPath, pdfBuffer);
  
  console.log('✅ Tab-aligned test PDF created:', outputPath);
  console.log('This shows 4 downbeats per line in perfect columns:');
  console.log('Line 1: A-      Grace,   sweet    sound');
  console.log('        1       1        5        1');
  console.log('Line 2: saved   a        wretch   me');
  console.log('        5       6        4        1');
  console.log('Line 3: once    lost,    now      found');
  console.log('        1       1        4        1');
  console.log('Line 4: blind,  now      see      (rest)');
  console.log('        1       5        1        1');
}

createTabAlignedTest();