# UX Conversion Plan - ChordScout Music Transcription App

## Overview

This document outlines what we need from the UX designer to convert their designs into a working React/TypeScript application.

---

## Current App Structure

### Technology Stack
- **Frontend**: React 18 + TypeScript + Vite
- **Styling**: Inline styles (currently) - can easily switch to CSS Modules, Tailwind, or styled-components
- **State Management**: React hooks (useState, useEffect)
- **API Communication**: Fetch API with custom service layer

### Current Pages/Views
1. **Main Page** (`src/App.tsx`)
   - YouTube URL input
   - Job status display
   - Progress indicator
   - PDF download button

---

## What We Need From UX Designer

### 1. Design Files (Required)

**Preferred Format** (in order of preference):
- [ ] Figma file (with developer handoff enabled)
- [ ] Adobe XD file
- [ ] Sketch file
- [ ] High-fidelity mockups (PNG/PDF) with annotations

**What to Include in Design Files**:
- All page states (empty, loading, success, error)
- Mobile responsive breakpoints (320px, 768px, 1024px, 1440px)
- Component states (hover, active, disabled, focus)
- Color palette with hex codes
- Typography specifications (fonts, sizes, weights, line heights)
- Spacing system (margins, padding)
- Interactive elements (buttons, inputs, dropdowns)

### 2. Design System Specifications (Required)

Create a simple design system document with:

#### Colors
```
Primary: #9333ea (purple)
Secondary: #2563eb (blue)
Success: #16a34a (green)
Error: #dc2626 (red)
Warning: #f59e0b (amber)
Background: #1f2937 (dark gray)
Text Primary: #ffffff (white)
Text Secondary: #9ca3af (light gray)
Border: #e5e7eb (light gray)
```

#### Typography
```
Font Family: [Designer to specify]
Headings:
  - H1: [size]px, [weight], [line-height]
  - H2: [size]px, [weight], [line-height]
Body:
  - Regular: [size]px, [weight], [line-height]
  - Small: [size]px, [weight], [line-height]
```

#### Spacing Scale
```
xs: 4px
sm: 8px
md: 16px
lg: 24px
xl: 32px
2xl: 48px
```

#### Border Radius
```
sm: 4px
md: 8px
lg: 12px
xl: 16px
full: 9999px
```

### 3. Page Designs (Required)

For each page, provide:

#### A. Home/Input Page
- [ ] Empty state (before user enters URL)
- [ ] Input field with YouTube URL
- [ ] Submit button
- [ ] Any hero text or branding
- [ ] Navigation (if any)

#### B. Processing/Loading Page
- [ ] Progress indicator design
- [ ] Current step display
- [ ] Percentage display
- [ ] Loading animations (if any)
- [ ] Cancel button (if needed)

#### C. Results/Success Page
- [ ] PDF preview or thumbnail
- [ ] Download button
- [ ] View button
- [ ] Song title display
- [ ] Duration display
- [ ] "Start new transcription" button

#### D. Error Page
- [ ] Error message display
- [ ] Error icon/illustration
- [ ] Retry button
- [ ] Troubleshooting tips section
- [ ] Back to home button

### 4. Component Designs (Optional but Helpful)

If you want custom components:
- [ ] Custom buttons (primary, secondary, disabled states)
- [ ] Custom input fields
- [ ] Custom progress bars
- [ ] Custom cards/containers
- [ ] Custom modals/dialogs
- [ ] Custom tooltips
- [ ] Loading spinners/animations

### 5. Assets (If Applicable)

- [ ] Logo files (SVG preferred, PNG as backup)
- [ ] Icons (SVG preferred)
- [ ] Illustrations
- [ ] Background images/patterns
- [ ] Custom fonts (with license/CDN link)

---

## Information About Current Functionality

### User Flow
```
1. User lands on home page
2. User enters YouTube URL
3. User clicks "Start" button
4. App shows progress (5 steps):
   - Downloading audio (20%)
   - Transcribing lyrics (40%)
   - Detecting chords (70%)
   - Generating PDF (90%)
   - Complete (100%)
5. User sees success message with PDF download link
6. User can download or view PDF
```

### Current Features
- YouTube URL validation
- Real-time progress updates (polls every 2 seconds)
- Error handling with troubleshooting tips
- PDF download and preview
- Responsive design (works on mobile)

### API Response Data Available
```typescript
{
  jobId: string
  status: 'PENDING' | 'DOWNLOADING' | 'TRANSCRIBING' | 'DETECTING_CHORDS' | 'GENERATING_PDF' | 'COMPLETE' | 'FAILED'
  progress: number (0-100)
  currentStep: string
  title: string (song title)
  pdfUrl: string (when complete)
  error: string (if failed)
  createdAt: string
  updatedAt: string
}
```

---

## Conversion Process

### Phase 1: Setup (1 hour)
1. Review design files
2. Extract color palette and typography
3. Set up styling approach (CSS Modules, Tailwind, or styled-components)
4. Install any required dependencies

### Phase 2: Component Creation (2-4 hours)
1. Create reusable components:
   - Button
   - Input
   - Card
   - ProgressBar
   - ErrorMessage
   - SuccessMessage
2. Implement design system tokens

### Phase 3: Page Implementation (3-5 hours)
1. Convert each page design to React components
2. Maintain existing functionality
3. Add responsive breakpoints
4. Test all states (loading, success, error)

### Phase 4: Polish (1-2 hours)
1. Add animations/transitions
2. Test on different screen sizes
3. Accessibility improvements
4. Performance optimization

**Total Estimated Time**: 7-12 hours (depending on design complexity)

---

## Recommended Design Approach

### Keep It Simple
- Single page application (SPA) works well for this use case
- Minimal navigation needed
- Focus on the core flow: Input → Progress → Result

### Mobile-First
- Most users may access from mobile devices
- Ensure touch-friendly buttons (min 44x44px)
- Readable text sizes (min 16px for body)

### Accessibility
- High contrast ratios (WCAG AA minimum)
- Clear focus states
- Keyboard navigation support
- Screen reader friendly

### Performance
- Optimize images (use SVG where possible)
- Minimize animations on mobile
- Fast loading times

---

## Handoff Checklist

Before starting conversion, ensure we have:

- [ ] All page designs in high fidelity
- [ ] Design system specifications
- [ ] Color palette with hex codes
- [ ] Typography specifications
- [ ] Spacing/sizing specifications
- [ ] All component states documented
- [ ] Mobile responsive designs
- [ ] Assets exported (logos, icons, images)
- [ ] Font files or CDN links
- [ ] Any animation specifications

---

## Communication

### Questions to Ask Designer

1. **Styling Preference**: Do you prefer CSS Modules, Tailwind CSS, or styled-components?
2. **Animations**: Are there specific animations or transitions you want?
3. **Fonts**: Are we using custom fonts? If so, do you have the license/CDN link?
4. **Icons**: Are we using an icon library (like Heroicons, Feather) or custom icons?
5. **Responsive Behavior**: How should components adapt on mobile vs desktop?
6. **Loading States**: What should the loading animations look like?
7. **Error States**: How should errors be displayed?

### Delivery Format

**Option 1: Figma (Recommended)**
- Share Figma file with developer access
- Enable "Inspect" mode for CSS export
- Organize layers clearly
- Name components consistently

**Option 2: Design Package**
- Zip file containing:
  - Design mockups (PNG/PDF)
  - Design system document
  - Assets folder (logos, icons, images)
  - Fonts folder (if custom fonts)
  - README with notes

---

## Example: Simple Conversion

### Designer Provides:
```
Button Design:
- Background: #9333ea
- Text: #ffffff
- Padding: 12px 24px
- Border Radius: 12px
- Font: 16px, weight 500
- Hover: Slightly darker background
```

### We Convert To:
```tsx
<button
  style={{
    background: '#9333ea',
    color: '#ffffff',
    padding: '12px 24px',
    borderRadius: '12px',
    fontSize: '16px',
    fontWeight: 500,
    border: 'none',
    cursor: 'pointer',
    transition: 'all 0.2s'
  }}
  onMouseEnter={(e) => e.currentTarget.style.background = '#7c2dd5'}
  onMouseLeave={(e) => e.currentTarget.style.background = '#9333ea'}
>
  Start Transcription
</button>
```

---

## Timeline

Once we receive complete designs:

- **Day 1**: Setup and component creation
- **Day 2**: Page implementation
- **Day 3**: Polish and testing
- **Day 4**: Review and adjustments

**Total**: 3-4 days for complete UX conversion

---

## Notes

- Current app is fully functional - we're only changing the visual design
- All backend functionality remains the same
- No API changes needed
- Can iterate on design after initial implementation
- Designer can provide designs in phases (e.g., home page first, then results page)

---

## Contact

For questions during the design process:
- Technical constraints
- Feasibility of animations
- Component behavior
- Responsive design questions

We're here to help make the conversion as smooth as possible!
