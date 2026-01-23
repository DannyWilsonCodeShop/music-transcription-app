# ChordScout Dashboard - Page Layout Specification

## 1. PAGE OVERVIEW

### Basic Information
- **Page Name**: ChordScout Dashboard
- **User Role**: Member (Musician/Student)
- **Primary Purpose**: Central hub for musicians to upload audio, transcribe music, and access learning resources
- **Page Type**: Dashboard with upload/transcription workflow

---

## 2. LAYOUT STRUCTURE

### Grid System
- **Desktop Layout**: 2-column grid (4-column system)
- **Column Proportions**: 
  - Left: 3/4 width (main transcription workflow)
  - Right: 1/4 width (sidebar widgets)
- **Mobile Behavior**: Stacks vertically (sidebar moves below main content)

---

## 3. HEADER/TOP SECTION

### Header Content
- **Title**: Dynamic greeting ("Good morning, Danny!")
- **Subtitle**: "Ready to continue your learning journey?"
- **Actions**: None in header
- **Sticky**: No (uses DashboardLayout component)
- **Background**: #3f3f3f (dark gray)
- **Text Color**: White

---

## 4. MAIN CONTENT AREA

### Section 1: Upload Section

**Location**: Left column (3/4 width), top
**Type**: Tabbed card interface
**Content**: File upload and YouTube link input

#### Components

1. **Upload Tabs**
   - Purpose: Switch between file upload and YouTube input
   - Position: Top of card
   - Size: Full width, 2 equal tabs
   - Interactive: Yes (tab switching)
   - Data Source: User input
   - Visual Style:
     - Active tab: bg-[#00bfc4], text-white, shadow-md
     - Inactive tab: bg-gray-100, text-gray-600, hover:bg-gray-200
     - Border radius: rounded-lg
     - Transition: all 0.3s

2. **File Upload Area (Tab 1)**
   - Purpose: Drag-and-drop or click to upload audio files
   - Position: Below tabs
   - Size: Full width, 8rem padding
   - Interactive: Yes (drag-and-drop, click to browse)
   - Data Source: User file selection
   - Visual Style:
     - Border: 2px dashed border-gray-300
     - Hover: border-[#00bfc4], bg-gray-50
     - With file: border-[#00bfc4], bg-[#00bfc4]/5
     - Border radius: rounded-xl
     - Icon: 📤 (upload) or 🎵 (with file)
     - Shows: filename, file size when selected

3. **YouTube Input (Tab 2)**
   - Purpose: Accept YouTube video URLs
   - Position: Below tabs
   - Size: Full width input field
   - Interactive: Yes (text input)
   - Data Source: User input
   - Visual Style:
     - Border: 2px solid border-gray-300
     - Focus: border-[#00bfc4]
     - Border radius: rounded-lg
     - Placeholder: "https://www.youtube.com/watch?v=..."

4. **Submit Buttons**
   - Purpose: Upload and process audio
   - Position: Bottom of upload section
   - Size: Full width
   - Interactive: Yes (click to submit)
   - Visual Style:
     - File upload: gradient from-[#00bfc4] to-[#0089c6]
     - YouTube: gradient from-[#0089c6] to-[#00bfc4]
     - Text: white, font-semibold
     - Border radius: rounded-lg
     - Hover: shadow-lg
     - Disabled: opacity-50, cursor-not-allowed

### Section 2: Transcription Options

**Location**: Left column (3/4 width), middle
**Type**: 2x2 grid of action cards
**Content**: Available transcription features

#### Components

1. **Transcribe Lyrics Card**
   - Purpose: AI-powered lyric transcription
   - Position: Top-left
   - Size: 1/2 width
   - Interactive: Yes (clickable)
   - Available: Yes
   - Visual Style:
     - Background: gradient from-blue-500 to-blue-600
     - Text: white
     - Icon: 🎤 (3xl size)
     - Border radius: rounded-xl
     - Hover: shadow-lg, scale-105
     - Padding: p-4

2. **Transcribe Chords Card**
   - Purpose: Detect chord progressions
   - Position: Top-right
   - Size: 1/2 width
   - Interactive: Yes (clickable)
   - Available: Yes
   - Visual Style:
     - Background: gradient from-purple-500 to-purple-600
     - Text: white
     - Icon: 🎸 (3xl size)
     - Border radius: rounded-xl
     - Hover: shadow-lg, scale-105

3. **Transpose Card**
   - Purpose: Change key signature
   - Position: Bottom-left
   - Size: 1/2 width
   - Interactive: No (coming soon)
   - Available: No
   - Visual Style:
     - Background: bg-gray-100
     - Text: text-gray-400
     - Icon: 🔄 (3xl size)
     - Badge: "Coming Soon" (yellow-400 bg)
     - Cursor: not-allowed

4. **Nashville Numbers Card**
   - Purpose: Convert to number system
   - Position: Bottom-right
   - Size: 1/2 width
   - Interactive: No (coming soon)
   - Available: No
   - Visual Style: Same as Transpose

### Section 3: Your Transcriptions List

**Location**: Left column (3/4 width), bottom
**Type**: Scrollable list of transcription jobs
**Content**: User's transcription history

#### Components

1. **List Header**
   - Purpose: Section title and count badge
   - Position: Top of list
   - Size: Full width
   - Visual Style:
     - Title: text-xl, font-semibold, text-[#3f3f3f]
     - Count badge: bg-[#00bfc4], text-white, rounded-full

2. **Transcription Items**
   - Purpose: Display individual transcription jobs
   - Position: Scrollable list
   - Size: Full width cards
   - Interactive: Yes (expandable, clickable)
   - Data Source: /api/transcription-jobs
   - Update Frequency: Real-time (polls every 5 seconds)
   - Visual Style:
     - Background: bg-gray-50
     - Border: border-gray-200
     - Border radius: rounded-lg
     - Hover: shadow-md
     - Padding: p-4
     - Spacing: space-y-3

3. **Job Status Badges**
   - Pending: ⏳ bg-yellow-100, text-yellow-700, border-yellow-200
   - Processing: ⚙️ bg-blue-100, text-blue-700, border-blue-200 (with spinner)
   - Completed: ✅ bg-green-100, text-green-700, border-green-200
   - Failed: ❌ bg-red-100, text-red-700, border-red-200

4. **Results Preview (Completed Jobs)**
   - Lyrics preview: bg-white, border-blue-100, 🎤 icon
   - Chords preview: bg-white, border-purple-100, 🎸 icon
   - View button: gradient from-blue-500 to-purple-600

5. **Empty State**
   - Icon: 🎼 (6xl size)
   - Text: "No transcriptions yet"
   - Subtext: "Upload an audio file or YouTube link to get started"
   - Style: text-center, py-12, text-gray-500

6. **Scrollbar**
   - Max height: 500px
   - Overflow: overflow-y-auto
   - Custom scrollbar: scrollbar-thin, scrollbar-thumb-gray-400, scrollbar-track-gray-200

---

## 5. SIDEBAR/SECONDARY CONTENT

### Widgets (top to bottom):

1. **Ripped Songs Database Widget**
   - Purpose: Show recently transcribed songs
   - Size: Full width card
   - Update Frequency: On page load
   - Interactive: Yes (clickable songs, "View All" link)
   - Visual Style:
     - Background: white
     - Border: border-blue-200
     - Border radius: rounded-xl
     - Shadow: shadow-md
     - Padding: p-4
   - Content:
     - Header: 🎵 title + "View All" link (text-[#00bfc4])
     - 3 recent songs
     - Each song shows:
       * Song name (font-medium)
       * Key signature badge (bg-[#00bfc4], text-white, rounded-full)
       * Chart type badges (Lyrics, Piano, Guitar, Bass)
       * Date (text-xs, text-gray-500)

2. **Backing Tracks Widget**
   - Purpose: Show recently created backing tracks
   - Size: Full width card
   - Update Frequency: On page load
   - Interactive: Yes (clickable tracks, "View All" link)
   - Visual Style: Same as Ripped Songs
   - Content:
     - Header: 🎼 title + "View All" link
     - 3 recent tracks
     - Each track shows:
       * Color dot (genre-coded: blue, purple, red)
       * Track name
       * Genre label
       * Key signature badge
       * Instrument badges (Drums, Bass, Keys, Piano)

3. **Study Modules Widget**
   - Purpose: Show available learning courses
   - Size: Full width card
   - Update Frequency: Static
   - Interactive: Yes (clickable courses)
   - Visual Style: Same as other widgets
   - Content:
     - Header: 🎓 title
     - 3 course cards:
       * Nashville Number System (blue-purple gradient)
       * Chord Theory Basics (orange-yellow gradient)
       * Ear Training (green-teal gradient)
     - Each course shows:
       * Icon (🎓, 🎸, 🎹)
       * Course title
       * Description
       * Lesson count badge
       * Difficulty badge

---

## 6. INTERACTIVE ELEMENTS

### Buttons

1. **Tab Buttons**
   - Label: "📁 Upload File" / "🎬 YouTube Link"
   - Style: Rounded-lg, full width
   - Color: Active: bg-[#00bfc4], Inactive: bg-gray-100
   - Size: py-2, px-4
   - Action: Switch between upload modes

2. **Upload Button**
   - Label: "🚀 Upload & Transcribe"
   - Style: Gradient, rounded-lg
   - Color: from-[#00bfc4] to-[#0089c6]
   - Size: Full width, py-3, px-6
   - Action: Upload file and create transcription job

3. **YouTube Submit Button**
   - Label: "🎬 Transcribe YouTube Video"
   - Style: Gradient, rounded-lg
   - Color: from-[#0089c6] to-[#00bfc4]
   - Size: Full width, py-3, px-6
   - Action: Submit YouTube URL for transcription

4. **Transcription Option Cards**
   - Label: Feature name + description
   - Style: Gradient background, rounded-xl
   - Size: p-4, hover:scale-105
   - Action: Select transcription type

5. **View Results Button**
   - Label: "View Full Results"
   - Style: Gradient, rounded-lg
   - Color: from-blue-500 to-purple-600
   - Size: Full width, py-2, px-4
   - Action: Open full transcription view

### Forms/Inputs

1. **File Input**
   - Type: File upload (hidden input + drag-drop area)
   - Accept: audio/*
   - Validation: File type, max 50MB
   - Style: Dashed border, rounded-xl
   - Feedback: Shows filename and size when selected

2. **YouTube URL Input**
   - Type: Text input (URL)
   - Placeholder: "https://www.youtube.com/watch?v=..."
   - Validation: Required, URL format
   - Style: Border-2, rounded-lg, focus:border-[#00bfc4]

---

## 7. RESPONSIVE BEHAVIOR

### Breakpoints

**Desktop (lg: 1024px+)**
- 4-column grid system
- Main content: 3 columns
- Sidebar: 1 column
- Side-by-side layout
- All widgets visible
- Max width: 1600px

**Tablet (md: 768px - 1023px)**
- Single column layout
- Main content full width
- Sidebar widgets stack below
- Reduced padding (px-4)
- Maintained card spacing

**Mobile (sm: < 768px)**
- Single column, full width
- Compact spacing (gap-4)
- Smaller text sizes
- Touch-friendly buttons (min 44px height)
- Sidebar widgets collapse
- Reduced padding (px-2)

---

## 8. COLORS & STYLING

### Color Palette
- **Primary**: #3f3f3f (dark gray - headers, text)
- **Secondary**: #00bfc4 (teal - buttons, accents, badges)
- **Accent**: #0089c6 (blue - gradients)
- **Background**: #e5e5e5 (light gray - page background)
- **Card Background**: white
- **Text Primary**: #3f3f3f
- **Text Secondary**: #666, #9e9e9e
- **Border**: #e0e0e0, rgba(0, 191, 196, 0.1)

### Status Colors
- **Pending**: yellow-100, yellow-700
- **Processing**: blue-100, blue-700
- **Completed**: green-100, green-700
- **Failed**: red-100, red-700

### Design Tokens
- **Border Radius**: 
  - Cards: rounded-xl (12px)
  - Buttons: rounded-lg (8px)
  - Badges: rounded-full
- **Shadows**: 
  - Cards: shadow-md, shadow-lg
  - Hover: shadow-lg
- **Spacing**: 
  - Grid gap: gap-6
  - Card padding: p-4, p-6
  - Section spacing: space-y-6, space-y-4
- **Font Sizes**: 
  - Headings: text-xl, text-3xl
  - Body: text-sm, text-base
  - Small: text-xs

### Gradients
- **Upload button**: from-[#00bfc4] to-[#0089c6]
- **YouTube button**: from-[#0089c6] to-[#00bfc4]
- **Lyrics card**: from-blue-500 to-blue-600
- **Chords card**: from-purple-500 to-purple-600
- **Results button**: from-blue-500 to-purple-600
- **Study modules**: Various (blue-purple, orange-yellow, green-teal)

---

## 9. DATA & STATE

### Data Sources

1. **Transcription Jobs API**
   - URL: AWS Amplify Data (TranscriptionJob model)
   - Method: client.models.TranscriptionJob.list()
   - Purpose: Fetch user's transcription jobs
   - Refresh: On load, every 5 seconds (polling)
   - Returns: Array of jobs with status, title, lyrics, chords

2. **File Upload API**
   - URL: AWS Amplify Storage (uploadData)
   - Method: POST
   - Purpose: Upload audio files to S3
   - Returns: File path/URL

3. **Ripped Songs API** (Mock)
   - URL: Static data (to be replaced)
   - Purpose: Show recently transcribed songs
   - Refresh: On load

4. **Backing Tracks API** (Mock)
   - URL: Static data (to be replaced)
   - Purpose: Show available backing tracks
   - Refresh: On load

5. **Study Modules API** (Mock)
   - URL: Static data (to be replaced)
   - Purpose: Show available courses
   - Refresh: Static

### State Management

1. **file**
   - Type: File | null
   - Initial: null
   - Updates: When user selects file
   - Used By: UploadSection component

2. **youtubeUrl**
   - Type: string
   - Initial: ''
   - Updates: When user types URL
   - Used By: UploadSection component

3. **loading**
   - Type: boolean
   - Initial: false
   - Updates: During upload/submission
   - Used By: Button disabled state

4. **activeTab**
   - Type: 'file' | 'youtube'
   - Initial: 'file'
   - Updates: When user clicks tabs
   - Used By: Tab display logic

5. **jobs**
   - Type: Array<TranscriptionJob>
   - Initial: []
   - Updates: After API fetch, every 5 seconds
   - Used By: TranscriptionsList component

6. **userName**
   - Type: string
   - Initial: 'Danny'
   - Updates: From user profile
   - Used By: DashboardHeader component

---

## 10. SPECIAL FEATURES

### Animations
- Tab switching: Smooth transition
- Card hover: scale-105, shadow-lg
- Button hover: shadow-lg
- Loading spinner: animate-spin
- Fade-in: animate-fadeIn (0.3s ease-out)

### Real-time Updates
- Polling: TranscriptionsList polls every 5 seconds
- Status updates: Automatic refresh of job status
- No WebSockets (using polling for simplicity)

### Drag and Drop
- File upload area supports drag-and-drop
- Visual feedback on drag over
- Accepts audio files only

### Accessibility
- Semantic HTML (header, main, section)
- ARIA labels on inputs
- Keyboard navigation support
- Focus indicators on interactive elements
- Alt text on images
- Screen reader friendly status updates

### Performance
- Lazy loading of components
- Efficient re-renders with React hooks
- Optimized polling (only when component mounted)
- Custom scrollbar for better UX

---

## 11. SIMILAR PAGES (Reference)

**Reference Page**: Class-cast.com Student Dashboard

**Similarities**: 
- 3/4 + 1/4 column layout
- Widget-based sidebar
- Main content workflow area
- Dynamic greeting header
- Card-based design
- Scrollable main content
- Status badges and indicators
- "View All" links in widgets

**Differences**:
- Upload/transcription workflow instead of social feed
- No video player (audio processing instead)
- Different color scheme (teal/blue instead of blue/purple)
- Transcription options grid instead of post composer
- Job status tracking instead of assignment tracking
- Music-focused widgets instead of academic widgets

---

## IMPLEMENTATION CHECKLIST

- [x] Page name and purpose
- [x] Grid layout (4-column system, 3/4 + 1/4)
- [x] Header content (dynamic greeting)
- [x] Main content sections (Upload, Options, List)
- [x] Sidebar widgets (Songs, Tracks, Modules)
- [x] Upload interface (tabs, drag-drop, YouTube)
- [x] Transcription options grid
- [x] Scrollable transcriptions list
- [x] Button styles and actions
- [x] Form inputs and validation
- [x] Responsive breakpoints
- [x] Color palette (#3f3f3f, #00bfc4, #e5e5e5)
- [x] Data sources (Amplify Data, Storage)
- [x] Special features (polling, drag-drop, animations)
- [x] Status badges and indicators
- [x] Empty states
- [x] Loading states
- [x] Error handling

---

## CURRENT STATUS

✅ **Implemented**:
- Complete 2-column dashboard layout
- Upload section with file and YouTube tabs
- Transcription options grid (4 cards)
- Scrollable transcriptions list with real-time updates
- All 3 sidebar widgets
- Dynamic header with greeting
- Responsive mobile layout
- Custom scrollbars
- Status badges and indicators
- Empty states
- Loading states

🔄 **In Progress**:
- Backend transcription processing
- OpenAI Whisper integration
- Chord detection algorithm

📋 **To Do**:
- User authentication (AWS Cognito)
- Real API endpoints for widgets
- Full transcription results view
- Export functionality
- Transpose feature
- Nashville Numbers feature
- Search and filter
- User settings

---

## NOTES

This dashboard follows the Class-cast.com student dashboard pattern with a music transcription focus. The layout prioritizes the upload-to-transcription workflow while providing quick access to learning resources and previously transcribed content through the sidebar widgets.

The design uses a professional color scheme with teal (#00bfc4) as the primary accent color, maintaining consistency across all interactive elements. The 3/4 + 1/4 column split ensures the main workflow has plenty of space while keeping helpful resources easily accessible.

All components are built with React + TypeScript and use Tailwind CSS for styling, ensuring maintainability and consistency with modern web development practices.
