# PptxGenJS v4 Reference Guide

## 1. Gradient Backgrounds (Light Theme, Blue/White)

PptxGenJS does NOT have native gradient support. Simulate gradients using layered shapes with transparency:

`javascript
// Simulate blue-to-white diagonal gradient
const slide = pptx.addSlide();

// Base white background
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: '100%', h: '100%', fill: { color: 'FFFFFF' } });

// Gradient simulation - multiple overlapping shapes with decreasing opacity
const gradientSteps = 8;
const baseColor = '1E3A5F'; // Deep blue

for (let i = 0; i < gradientSteps; i++) {
  const opacity = 1 - (i / gradientSteps);
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: i * (5.625 / gradientSteps),
    w: '100%',
    h: 5.625 / gradientSteps + 0.1,
    fill: { color: baseColor, transparency: 100 - (opacity * 100) },
    line: { type: 'none' }
  });
}
`

**Alternative: Linear gradient simulation using angled shapes**

`javascript
// Diagonal gradient simulation
slide.addShape(pptx.ShapeType.rect, {
  x: -1, y: -1, w: 12, h: 8,
  fill: { color: '1E3A5F', transparency: 30 },
  rotate: 15
});
slide.addShape(pptx.ShapeType.rect, {
  x: -1, y: -1, w: 12, h: 8,
  fill: { color: '4A90D9', transparency: 50 },
  rotate: 15
});
`

---

## 2. Tables with Proper Formatting

`javascript
const tableData = [
  // Header row
  [
    { text: 'Product', options: { fill: '1E3A5F', color: 'FFFFFF', bold: true, align: 'center' } },
    { text: 'Q1 Sales', options: { fill: '1E3A5F', color: 'FFFFFF', bold: true, align: 'center' } },
    { text: 'Q2 Sales', options: { fill: '1E3A5F', color: 'FFFFFF', bold: true, align: 'center' } }
  ],
  // Data rows with alternating colors
  [
    { text: 'Widget A', options: { fill: 'F8FAFC' } },
    { text: ',200', options: { fill: 'F8FAFC', align: 'right' } },
    { text: ',100', options: { fill: 'F8FAFC', align: 'right' } }
  ],
  [
    { text: 'Widget B', options: { fill: 'FFFFFF' } },
    { text: ',900', options: { fill: 'FFFFFF', align: 'right' } },
    { text: ',200', options: { fill: 'FFFFFF', align: 'right' } }
  ],
  // Footer row
  [
    { text: 'Total', options: { fill: 'E2E8F0', bold: true } },
    { text: ',100', options: { fill: 'E2E8F0', bold: true, align: 'right' } },
    { text: ',300', options: { fill: 'E2E8F0', bold: true, align: 'right' } }
  ]
];

slide.addTable(tableData, {
  x: 0.5, y: 1.5, w: 9, h: 2.5,
  colW: [3, 3, 3],
  border: { pt: 0.5, color: 'CBD5E1' },
  fontFace: 'Arial',
  fontSize: 12,
  valign: 'middle'
});
`

**Merged cells example**

`javascript
const mergedTable = [
  [
    { text: 'Quarterly Results', options: { colspan: 3, fill: '1E3A5F', color: 'FFFFFF', bold: true, align: 'center' } },
    {}, {}
  ],
  [
    { text: 'Region', options: { fill: 'E2E8F0', bold: true } },
    { text: 'Revenue', options: { fill: 'E2E8F0', bold: true } },
    { text: 'Growth', options: { fill: 'E2E8F0', bold: true } }
  ],
  ['North', ',000', '+12%'],
  ['South', ',000', '+8%']
];

slide.addTable(mergedTable, { x: 0.5, y: 0.5, w: 6, border: { pt: 1, color: '1E3A5F' } });
`

---

## 3. Code Blocks with Syntax Highlighting Simulation

Use VS Code Dark+ theme colors for syntax highlighting:

`javascript
const codeTheme = {
  keyword: '569CD6',    // blue - keywords
  string: 'CE9178',    // orange - strings
  number: 'B5CEA8',    // green - numbers
  comment: '6A9955',   // dark green - comments
  function: 'DCDCAA',   // yellow - functions
  variable: '9CDCFE',  // light blue - variables
  type: '4EC9B0',      // teal - types/classes
  operator: 'D4D4D4'    // light gray - operators
};

const codeLines = [
  { text: 'async function fetchData(url) {', color: codeTheme.keyword },
  { text: '  const response = await fetch(url);', color: codeTheme.variable },
  { text: '  if (!response.ok) {', color: codeTheme.keyword },
  { text: '    throw new Error(\HTTP \\);', color: codeTheme.function },
  { text: '  }', color: codeTheme.keyword },
  { text: '  return response.json();', color: codeTheme.variable },
  { text: '}', color: codeTheme.keyword }
];

// Create code block background
slide.addShape(pptx.ShapeType.roundRect, {
  x: 0.5, y: 1, w: 9, h: 2.5,
  fill: { color: '1E1E1E' },
  line: { color: '3C3C3C', pt: 1 },
  rectRadius: 0.1
});

// Add code text
let yPos = 1.15;
codeLines.forEach((line, i) => {
  slide.addText(line.text, {
    x: 0.7, y: yPos + (i * 0.28), w: 8.6, h: 0.28,
    fontFace: 'Courier New',
    fontSize: 11,
    color: line.color,
    margin: 0
  });
});
`

---

## 4. Multi-Column Layouts

**Two-Column Layout**

`javascript
// Left column - text content
slide.addText('Left Column Content', {
  x: 0.5, y: 1, w: 4.25, h: 4,
  fontSize: 14, fontFace: 'Arial', color: '333333'
});

// Right column - image/shapes
slide.addImage({ url: 'https://example.com/image.png' }, {
  x: 5, y: 1, w: 4.5, h: 4
});

// Vertical divider
slide.addShape(pptx.ShapeType.line, {
  x: 4.9, y: 1, w: 0, h: 4,
  line: { color: 'E2E8F0', pt: 1 }
});
`

**Three-Column Layout**

`javascript
const colWidth = 2.8;
const colGap = 0.3;
const startX = 0.5;

for (let i = 0; i < 3; i++) {
  const x = startX + i * (colWidth + colGap);
  
  // Column card background
  slide.addShape(pptx.ShapeType.roundRect, {
    x: x, y: 1, w: colWidth, h: 4,
    fill: { color: 'FFFFFF' },
    line: { color: 'E2E8F0', pt: 1 },
    rectRadius: 0.1,
    shadow: { type: 'outer', blur: 3, offset: 2, angle: 45, color: '000000', opacity: 0.1 }
  });
  
  // Column header
  slide.addText('Column ' + (i + 1), {
    x: x, y: 1.2, w: colWidth, h: 0.5,
    fontSize: 16, bold: true, align: 'center', color: '1E3A5F'
  });
  
  // Column content
  slide.addText('Content for column ' + (i + 1) + '...', {
    x: x + 0.15, y: 1.8, w: colWidth - 0.3, h: 3,
    fontSize: 12, color: '666666'
  });
}
`

**Four-Column Grid**

`javascript
const gridCols = 4;
const gridWidth = 2.1;
const gridGap = 0.2;

for (let i = 0; i < gridCols; i++) {
  const x = 0.5 + i * (gridWidth + gridGap);
  
  slide.addShape(pptx.ShapeType.rect, {
    x: x, y: 0.5, w: gridWidth, h: 1.2,
    fill: { color: ['1E3A5F', '4A90D9', '7BB3E0', 'A8D5F2'][i] }
  });
  
  slide.addText('Feature ' + (i + 1), {
    x: x, y: 0.8, w: gridWidth, h: 0.6,
    fontSize: 14, bold: true, align: 'center', color: 'FFFFFF'
  });
}
`

---

## 5. Charts and Graphs

`javascript
// BAR CHART
slide.addChart(pptx.ChartType.bar, [
  { name: 'Q1', labels: ['Product A', 'Product B', 'Product C'], values: [45, 52, 38] },
  { name: 'Q2', labels: ['Product A', 'Product B', 'Product C'], values: [52, 48, 61] }
], {
  x: 0.5, y: 1, w: 4.5, h: 3,
  barDir: 'bar',
  chartColors: ['1E3A5F', '4A90D9'],
  showTitle: true, title: 'Quarterly Sales',
  showLegend: true, legendPos: 'b'
});

// LINE CHART
slide.addChart(pptx.ChartType.line, [
  { name: 'Revenue', labels: ['Jan', 'Feb', 'Mar', 'Apr'], values: [125, 139, 152, 168] },
  { name: 'Target', labels: ['Jan', 'Feb', 'Mar', 'Apr'], values: [120, 135, 145, 160] }
], {
  x: 5.5, y: 1, w: 4.5, h: 3,
  lineSize: 2,
  lineSmooth: true,
  chartColors: ['4A90D9', 'E2E8F0'],
  showTitle: true, title: 'Revenue Trend'
});

// PIE CHART
slide.addChart(pptx.ChartType.pie, [{
  name: 'Market Share',
  labels: ['Enterprise', 'SMB', 'Consumer', 'Other'],
  values: [45, 30, 18, 7]
}], {
  x: 0.5, y: 4, w: 4, h: 3,
  chartColors: ['1E3A5F', '4A90D9', '7BB3E0', 'A8D5F2'],
  showPercent: true,
  showLegend: true, legendPos: 'r'
});

// DOUGHNUT CHART
slide.addChart(pptx.ChartType.doughnut, [{
  name: 'Budget',
  labels: ['Marketing', 'R&D', 'Operations', 'Sales'],
  values: [25, 35, 20, 20]
}], {
  x: 5, y: 4, w: 4, h: 3,
  chartColors: ['1E3A5F', '4A90D9', '7BB3E0', 'A8D5F2'],
  holeSize: 50
});

// COMBO CHART (bar + line)
slide.addChart(pptx.ChartType.bar, [
  { name: 'Sales', labels: ['Jan', 'Feb', 'Mar'], values: [120, 145, 168] }
], {
  x: 0.5, y: 0.5, w: 5, h: 3.5,
  barDir: 'col',
  chartColors: ['4A90D9'],
  showTitle: true, title: 'Sales vs Target'
});

slide.addChart(pptx.ChartType.line, [
  { name: 'Target', labels: ['Jan', 'Feb', 'Mar'], values: [130, 140, 160] }
], {
  x: 0.5, y: 0.5, w: 5, h: 3.5,
  lineSize: 3,
  lineSmooth: true,
  chartColors: ['E2E8F0']
});
`

---

## 6. Master Slides and Slide Layouts

`javascript
// Define a slide master/layout
const slideMaster = pptx.defineSlideMaster({
  background: { color: 'FFFFFF' },
  objects: [
    // Header placeholder
    { text: '', x: 0.5, y: 0.3, w: 9, h: 0.6 },
    // Footer with page numbers
    { text: '', x: 0.5, y: 5.2, w: 9, h: 0.3 }
  ]
});

// Create slide from master
const slide1 = pptx.addSlide({ slideMaster });

// Add content that flows into the master placeholders
slide1.addText('Slide Title', {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  fontSize: 28, bold: true, color: '1E3A5F'
});

slide1.addText('Page 1 of 10', {
  x: 9, y: 5.2, w: 0.5, h: 0.3,
  fontSize: 10, color: '666666', align: 'right'
});

// Multiple layout types
const layouts = {
  title: { x: 0.5, y: 2.2, w: 9, h: 1.2, fontSize: 36, bold: true, align: 'center' },
  content: { x: 0.5, y: 1.2, w: 9, h: 4, fontSize: 16 },
  twoColumn: { left: { x: 0.5, w: 4.25 }, right: { x: 5, w: 4.5 } }
};
`

---

## 7. Text Formatting Best Practices

**Typography Scale**

`javascript
const typography = {
  h1: { fontSize: 36, bold: true, color: '1E3A5F', fontFace: 'Arial' },
  h2: { fontSize: 28, bold: true, color: '1E3A5F', fontFace: 'Arial' },
  h3: { fontSize: 22, bold: true, color: '333333', fontFace: 'Arial' },
  h4: { fontSize: 18, bold: true, color: '333333', fontFace: 'Arial' },
  body: { fontSize: 14, color: '666666', fontFace: 'Arial' },
  caption: { fontSize: 11, color: '999999', fontFace: 'Arial' },
  code: { fontSize: 12, fontFace: 'Courier New', color: '333333' }
};

// Usage
slide.addText('Main Heading', { x: 0.5, y: 0.5, ...typography.h1 });
slide.addText('Section Title', { x: 0.5, y: 1.2, ...typography.h2 });
slide.addText('Body text content here', { x: 0.5, y: 1.8, ...typography.body });
`

**Text Effects**

`javascript
// Shadow effect on text
slide.addText('Shadow Text', {
  x: 1, y: 1, w: 4, h: 0.6,
  fontSize: 24, bold: true, color: '1E3A5F',
  shadow: { type: 'outer', blur: 3, offset: 2, angle: 45, color: '000000', opacity: 0.2 }
});

// Text with outline
slide.addText('Outlined Text', {
  x: 1, y: 2, w: 4, h: 0.6,
  fontSize: 24, bold: true, color: 'FFFFFF',
  line: { color: '1E3A5F', pt: 2 }
});

// Superscript and Subscript
slide.addText([
  { text: 'E = mc', options: { fontSize: 20 } },
  { text: '2', options: { fontSize: 12, superscript: true } }
], { x: 1, y: 3, w: 4, h: 0.5 });

// Line spacing
slide.addText('Multi-line text with proper line spacing', {
  x: 0.5, y: 1, w: 5, h: 2,
  fontSize: 14, color: '333333',
  paraSpaceAfter: 12,
  lineSpacingMultiple: 1.5
});
`

---

## 8. Images from URLs

`javascript
// Basic image from URL
slide.addImage({ url: 'https://example.com/photo.jpg' }, {
  x: 0.5, y: 1, w: 4, h: 3
});

// Image with sizing options
slide.addImage({ url: 'https://example.com/photo.jpg' }, {
  x: 0.5, y: 1, w: 4, h: 3,
  sizing: {
    type: 'contain',  // 'cover', 'contain', 'crop'
    align: 'center',
    valign: 'middle'
  }
});

// Circle crop (profile picture style)
slide.addShape(pptx.ShapeType.ellipse, {
  x: 0.5, y: 1, w: 1.5, h: 1.5,
  fill: { color: 'FFFFFF' },
  line: { type: 'none' }
});

slide.addImage({ url: 'https://example.com/avatar.jpg' }, {
  x: 0.6, y: 1.1, w: 1.3, h: 1.3,
  sizing: { type: 'crop', pos: 'center' }
});

// Image with shadow
slide.addImage({ url: 'https://example.com/photo.jpg' }, {
  x: 1, y: 1, w: 3, h: 2,
  shadow: { type: 'outer', blur: 5, offset: 3, angle: 45, color: '000000', opacity: 0.25 }
});
`

---

## 9. Professional Card-Based Layouts

**Basic Card Component**

`javascript
function addCard(slide, x, y, w, h, title, content, color = '4A90D9') {
  // Card background with shadow
  slide.addShape(pptx.ShapeType.roundRect, {
    x: x, y: y, w: w, h: h,
    fill: { color: 'FFFFFF' },
    line: { color: 'E2E8F0', pt: 1 },
    rectRadius: 0.1,
    shadow: { type: 'outer', blur: 4, offset: 2, angle: 45, color: '000000', opacity: 0.1 }
  });
  
  // Color accent bar at top
  slide.addShape(pptx.ShapeType.rect, {
    x: x, y: y, w: w, h: 0.08,
    fill: { color: color },
    line: { type: 'none' }
  });
  
  // Card title
  slide.addText(title, {
    x: x + 0.2, y: y + 0.25, w: w - 0.4, h: 0.4,
    fontSize: 14, bold: true, color: '1E3A5F'
  });
  
  // Card content
  slide.addText(content, {
    x: x + 0.2, y: y + 0.7, w: w - 0.4, h: h - 1,
    fontSize: 11, color: '666666'
  });
}

// Usage
addCard(slide, 0.5, 0.5, 4, 2.5, 'Feature One', 'Description of the first feature card.', '1E3A5F');
addCard(slide, 5, 0.5, 4, 2.5, 'Feature Two', 'Description of the second feature card.', '4A90D9');
`

**Feature Card with Icon Placeholder**

`javascript
function addFeatureCard(slide, x, y, w, h, iconEmoji, title, description) {
  // Card background
  slide.addShape(pptx.ShapeType.roundRect, {
    x: x, y: y, w: w, h: h,
    fill: { color: 'FFFFFF' },
    line: { type: 'none' },
    rectRadius: 0.15,
    shadow: { type: 'outer', blur: 6, offset: 3, angle: 45, color: '000000', opacity: 0.12 }
  });
  
  // Icon circle
  slide.addShape(pptx.ShapeType.ellipse, {
    x: x + (w - 0.8) / 2, y: y + 0.3, w: 0.8, h: 0.8,
    fill: { color: 'F0F7FF' },
    line: { type: 'none' }
  });
  
  // Icon text (emoji)
  slide.addText(iconEmoji, {
    x: x + (w - 0.8) / 2, y: y + 0.4, w: 0.8, h: 0.6,
    fontSize: 24, align: 'center'
  });
  
  // Title
  slide.addText(title, {
    x: x + 0.2, y: y + 1.3, w: w - 0.4, h: 0.4,
    fontSize: 14, bold: true, align: 'center', color: '1E3A5F'
  });
  
  // Description
  slide.addText(description, {
    x: x + 0.2, y: y + 1.75, w: w - 0.4, h: h - 2.2,
    fontSize: 10, align: 'center', color: '666666'
  });
}

addFeatureCard(slide, 0.5, 0.5, 2.8, 3, '🚀', 'Fast Delivery', 'Quick deployment to production');
addFeatureCard(slide, 3.6, 0.5, 2.8, 3, '🔒', 'Secure', 'Enterprise-grade security');
addFeatureCard(slide, 6.7, 0.5, 2.8, 3, '📊', 'Analytics', 'Real-time insights');
`

**Stat Card**

`javascript
function addStatCard(slide, x, y, w, h, value, label, change) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x: x, y: y, w: w, h: h,
    fill: { color: '1E3A5F' },
    rectRadius: 0.1
  });
  
  slide.addText(value, {
    x: x, y: y + 0.3, w: w, h: 0.8,
    fontSize: 36, bold: true, align: 'center', color: 'FFFFFF'
  });
  
  slide.addText(label, {
    x: x, y: y + 1.1, w: w, h: 0.4,
    fontSize: 12, align: 'center', color: 'A8D5F2'
  });
  
  slide.addText(change, {
    x: x, y: y + 1.5, w: w, h: 0.3,
    fontSize: 10, align: 'center', color: change.startsWith('+') ? '4ADE80' : 'F87171'
  });
}

addStatCard(slide, 0.5, 0.5, 2.2, 2.2, '2.4M', 'Users', '+12.5%');
addStatCard(slide, 2.9, 0.5, 2.2, 2.2, '.2B', 'Revenue', '+28.3%');
addStatCard(slide, 5.3, 0.5, 2.2, 2.2, '99.9%', 'Uptime', '+0.1%');
`

---

## 10. Complete PptxGenJS API Reference

### Core Methods

`javascript
// Initialize
const pptx = new PptxGenJS();

// Presentation settings
pptx.author = 'Your Name';
pptx.title = 'Presentation Title';
pptx.subject = 'Topic';
pptx.company = 'Company Name';

// Layout options
pptx.layout = 'LAYOUT_16x9';  // Default
// Also: 'LAYOUT_16x9', 'LAYOUT_16x10', 'LAYOUT_4x3', 'LAYOUT_WIDE', 'LAYOUT_CUSTOM'

// Save
await pptx.writeFile({ fileName: 'presentation.pptx' });
// Or for browser: pptx.write('blob').then(blob => ...);
`

### Slide Object

`javascript
const slide = pptx.addSlide({ slideMaster?: SlideMaster });

// Background
slide.background = { color: 'FFFFFF' };
// Or: slide.background = { color: 'FFFFFF', transparency: 50 };

// Add shapes
slide.addShape(shapeType, options);
slide.addText(text, options);
slide.addTable(data, options);
slide.addImage(image, options);
slide.addChart(chartType, data, options);

// Slide properties
slide.slideNumber = { x: 9, y: 5.3, w: 0.5, h: 0.3 };
`

### Shape Types

`javascript
pptx.ShapeType = {
  rect: 'rect',
  roundRect: 'roundRect',
  ellipse: 'ellipse',
  triangle: 'triangle',
  line: 'line',
  arrow: 'arrow',
  upArrow: 'upArrow',
  downArrow: 'downArrow',
  leftArrow: 'leftArrow',
  rightArrow: 'rightArrow',
  star5: 'star5',
  heart: 'heart',
  lightningBolt: 'lightningBolt',
  smileyFace: 'smileyFace',
  rectangle: 'rect',
  square: 'square',
  circle: 'ellipse',
  oval: 'ellipse',
  // ... many more
};
`

### Shape Options

`javascript
slide.addShape(pptx.ShapeType.roundRect, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: '4A90D9' },
  // fill: { color: '4A90D9', transparency: 30 },
  // fill: { type: 'solid', color: '4A90D9' },
  line: { color: '1E3A5F', pt: 2 },
  // line: { type: 'none' },
  rotate: 45,
  rectRadius: 0.1,
  shadow: {
    type: 'outer',  // 'outer', 'inner', 'outer'
    blur: 5,
    offset: 3,
    angle: 45,
    color: '000000',
    opacity: 0.25
  }
});
`

### Text Options

`javascript
slide.addText('Hello World', {
  x: 0.5, y: 0.5, w: 5, h: 1,
  fontSize: 24,
  fontFace: 'Arial',
  color: '1E3A5F',
  bold: true,
  italic: true,
  underline: { style: 'single', color: '1E3A5F' },
  align: 'left',  // 'left', 'center', 'right', 'justify'
  valign: 'middle',  // 'top', 'middle', 'bottom'
  rotate: 0,  // 0, 90, 180, 270, 360
  margin: 5,
  indentLevel: 0,
  // Line spacing
  lineSpacingMultiple: 1.15,
  paraSpaceBefore: 0,
  paraSpaceAfter: 6,
  // Superscript/Subscript
  superscript: false,
  subscript: false,
  // Shadow
  shadow: { type: 'outer', blur: 2, offset: 1, angle: 45, color: '000000', opacity: 0.2 }
});
`

### Table Options

`javascript
slide.addTable(data, {
  x: 0.5, y: 1, w: 9, h: 3,
  colW: [3, 3, 3],  // Column widths
  rowH: [0.5, 0.4, 0.4, 0.4],  // Row heights
  border: { pt: 0.5, color: 'CBD5E1' },
  fontFace: 'Arial',
  fontSize: 11,
  color: '333333',
  align: 'left',
  valign: 'middle',
  margin: [5, 5, 5, 5],  // [top, right, bottom, left]
  span: { row: 0, col: 0 },  // For merged cells
  fill: { color: 'FFFFFF' }
});
`

### Image Options

`javascript
slide.addImage({
  url: 'https://example.com/image.jpg',
  // or
  data: base64String,
  // or
  path: '/local/path/to/image.jpg'
}, {
  x: 1, y: 1, w: 3, h: 2,
  sizing: {
    type: 'contain',  // 'contain', 'cover', 'crop', 'fit'
    pos: 'center'  // 'center', 'left', 'right', 'top', 'bottom'
  },
  shadow: { type: 'outer', blur: 4, offset: 2, angle: 45, color: '000000', opacity: 0.2 }
});
`

### Chart Types

`javascript
pptx.ChartType = {
  bar: 'bar',
  bar3d: 'bar3d',
  line: 'line',
  line3d: 'line3d',
  pie: 'pie',
  pie3d: 'pie3d',
  doughnut: 'doughnut',
  area: 'area',
  scatter: 'scatter',
  bubble: 'bubble',
  radar: 'radar',
  combo: 'combo'
};

// Chart data format
const chartData = [
  { name: 'Series 1', labels: ['A', 'B', 'C'], values: [10, 20, 30] },
  { name: 'Series 2', labels: ['A', 'B', 'C'], values: [15, 25, 35] }
];
`

### Color Format

**IMPORTANT: Colors are 6-character hex WITHOUT the # prefix**

`javascript
// Correct
fill: { color: 'FF0000' }
color: '1E3A5F'

// Wrong - will not work
fill: { color: '#FF0000' }
`

### Layout Dimensions

`javascript
// 16:9 (default) - 10" x 5.625"
const LAYOUT_16x9 = { x: 0, y: 0, w: 10, h: 5.625 };

// 4:3 - 10" x 7.5"
const LAYOUT_4x3 = { x: 0, y: 0, w: 10, h: 7.5 };

// Custom
pptx.layout = { width: 13.33, height: 7.5 };  // 16:9 widescreen
`

### Common Patterns

**Slide with header and content**

`javascript
const slide = pptx.addSlide();
slide.background = { color: 'FFFFFF' };

// Header bar
slide.addShape(pptx.ShapeType.rect, {
  x: 0, y: 0, w: 10, h: 1,
  fill: { color: '1E3A5F' },
  line: { type: 'none' }
});

slide.addText('Slide Title', {
  x: 0.5, y: 0.25, w: 9, h: 0.5,
  fontSize: 24, bold: true, color: 'FFFFFF'
});

// Content area
slide.addText('Your content here...', {
  x: 0.5, y: 1.3, w: 9, h: 4,
  fontSize: 14, color: '333333'
});

// Footer
slide.addText('© 2026 Company Name', {
  x: 0.5, y: 5.2, w: 4, h: 0.3,
  fontSize: 10, color: '999999'
});
`

---

## Quick Reference Cheatsheet

| Feature | Syntax |
|---------|--------|
| Rectangle | addShape(ShapeType.rect, { x, y, w, h }) |
| Rounded Rect | addShape(ShapeType.roundRect, { ..., rectRadius: 0.1 }) |
| Text | addText('text', { x, y, w, h, fontSize, bold, color }) |
| Table | addTable(data, { x, y, w, h, colW }) |
| Image | addImage({ url }, { x, y, w, h }) |
| Chart | addChart(ChartType.bar, data, { x, y, w, h }) |
| Shadow | shadow: { type: 'outer', blur, offset, angle, color, opacity } |
| Line | addShape(ShapeType.line, { x, y, w, h }) |
| Colors | 6-char hex WITHOUT # (e.g., 'FF0000') |
| Layout | LAYOUT_16x9 = 10" x 5.625" |

---

*Generated from PptxGenJS v4 official documentation and real-world examples*
