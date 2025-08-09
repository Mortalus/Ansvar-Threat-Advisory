# Ansvar Security Agents - Design System

## 🎨 Design Philosophy

Our design system is built on the principles of **data sovereignty**, **security**, and **professional excellence**. We aim for Apple-level design aesthetics with a focus on cybersecurity and enterprise workflows.

### Core Principles
- **Clarity**: Every element should have a clear purpose and meaning
- **Consistency**: Unified experience across all components and views
- **Accessibility**: WCAG 2.1 AA compliance for all users
- **Performance**: Optimized for speed and efficiency
- **Security**: Visual cues that reinforce trust and security

---

## 🎯 Brand Identity

### Brand Values
- **Data Sovereignty**: Complete control over your data
- **Security First**: Enterprise-grade security in every aspect
- **AI-Powered**: Intelligent automation and insights
- **Professional**: Built for serious security professionals

### Voice & Tone
- **Professional**: Clear, authoritative, knowledgeable
- **Helpful**: Supportive without being condescending
- **Confident**: Assured in capabilities and security
- **Precise**: Accurate and specific in communication

---

## 🎨 Color System

### Primary Colors
```css
/* Purple Gradient - Primary Brand */
--purple-50: #faf5ff;
--purple-100: #f3e8ff;
--purple-200: #e9d5ff;
--purple-300: #d8b4fe;
--purple-400: #c084fc;
--purple-500: #a855f7;  /* Primary */
--purple-600: #9333ea;  /* Primary Dark */
--purple-700: #7c3aed;
--purple-800: #6b21a8;
--purple-900: #581c87;

/* Blue Gradient - Secondary Brand */
--blue-50: #eff6ff;
--blue-100: #dbeafe;
--blue-200: #bfdbfe;
--blue-300: #93c5fd;
--blue-400: #60a5fa;
--blue-500: #3b82f6;   /* Secondary */
--blue-600: #2563eb;   /* Secondary Dark */
--blue-700: #1d4ed8;
--blue-800: #1e40af;
--blue-900: #1e3a8a;
```

### Semantic Colors
```css
/* Success */
--green-50: #f0fdf4;
--green-500: #22c55e;
--green-600: #16a34a;
--green-700: #15803d;

/* Warning */
--yellow-50: #fefce8;
--yellow-500: #eab308;
--yellow-600: #ca8a04;
--yellow-700: #a16207;

/* Error */
--red-50: #fef2f2;
--red-500: #ef4444;
--red-600: #dc2626;
--red-700: #b91c1c;

/* Neutral */
--gray-50: #f9fafb;
--gray-100: #f3f4f6;
--gray-200: #e5e7eb;
--gray-300: #d1d5db;
--gray-400: #9ca3af;
--gray-500: #6b7280;
--gray-600: #4b5563;
--gray-700: #374151;
--gray-800: #1f2937;
--gray-900: #111827;
```

### Usage Guidelines
- **Primary Gradient**: Main CTAs, active states, brand elements
- **Blue**: Secondary actions, information, links
- **Green**: Success states, completed actions, positive feedback
- **Yellow**: Warnings, pending states, attention needed
- **Red**: Errors, destructive actions, critical alerts
- **Gray**: Text, borders, backgrounds, neutral elements

---

## 📝 Typography

### Font Stack
```css
font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

### Type Scale
```css
/* Headings */
--text-xs: 0.75rem;     /* 12px */
--text-sm: 0.875rem;    /* 14px */
--text-base: 1rem;      /* 16px */
--text-lg: 1.125rem;    /* 18px */
--text-xl: 1.25rem;     /* 20px */
--text-2xl: 1.5rem;     /* 24px */
--text-3xl: 1.875rem;   /* 30px */
--text-4xl: 2.25rem;    /* 36px */
--text-5xl: 3rem;       /* 48px */

/* Line Heights */
--leading-tight: 1.25;   /* 120% - Headings */
--leading-normal: 1.5;   /* 150% - Body text */
--leading-relaxed: 1.625; /* 162.5% - Large text */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Typography Hierarchy
```css
/* H1 - Page Titles */
.text-h1 {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  color: var(--gray-900);
}

/* H2 - Section Titles */
.text-h2 {
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
  color: var(--gray-900);
}

/* H3 - Subsection Titles */
.text-h3 {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
  color: var(--gray-900);
}

/* Body Text */
.text-body {
  font-size: var(--text-base);
  font-weight: var(--font-normal);
  line-height: var(--leading-normal);
  color: var(--gray-700);
}

/* Small Text */
.text-small {
  font-size: var(--text-sm);
  font-weight: var(--font-normal);
  line-height: var(--leading-normal);
  color: var(--gray-600);
}

/* Caption */
.text-caption {
  font-size: var(--text-xs);
  font-weight: var(--font-normal);
  line-height: var(--leading-normal);
  color: var(--gray-500);
}
```

---

## 📏 Spacing System

### 8px Grid System
```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
--space-20: 5rem;     /* 80px */
--space-24: 6rem;     /* 96px */
```

### Usage Guidelines
- **4px**: Fine adjustments, icon spacing
- **8px**: Standard spacing unit, padding, margins
- **16px**: Component spacing, form fields
- **24px**: Section spacing, card padding
- **32px**: Large component spacing
- **48px+**: Page-level spacing, major sections

---

## 🔘 Component Library

### Buttons

#### Primary Button
```css
.btn-primary {
  background: linear-gradient(135deg, var(--purple-600), var(--blue-600));
  color: white;
  padding: var(--space-3) var(--space-6);
  border-radius: 0.5rem;
  font-weight: var(--font-medium);
  transition: all 0.2s ease;
  border: none;
  cursor: pointer;
}

.btn-primary:hover {
  box-shadow: 0 10px 25px rgba(168, 85, 247, 0.3);
  transform: translateY(-1px);
}
```

#### Secondary Button
```css
.btn-secondary {
  background: var(--gray-600);
  color: white;
  padding: var(--space-3) var(--space-6);
  border-radius: 0.5rem;
  font-weight: var(--font-medium);
  transition: all 0.2s ease;
  border: none;
  cursor: pointer;
}

.btn-secondary:hover {
  background: var(--gray-700);
}
```

#### Outline Button
```css
.btn-outline {
  background: transparent;
  color: var(--gray-700);
  padding: var(--space-3) var(--space-6);
  border: 1px solid var(--gray-300);
  border-radius: 0.5rem;
  font-weight: var(--font-medium);
  transition: all 0.2s ease;
  cursor: pointer;
}

.btn-outline:hover {
  background: var(--gray-100);
  border-color: var(--gray-400);
}
```

### Form Elements

#### Input Fields
```css
.input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--gray-300);
  border-radius: 0.5rem;
  font-size: var(--text-base);
  transition: all 0.2s ease;
  background: white;
}

.input:focus {
  outline: none;
  border-color: var(--purple-500);
  box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.1);
}

.input:disabled {
  background: var(--gray-50);
  color: var(--gray-500);
  cursor: not-allowed;
}
```

#### Select Dropdown
```css
.select {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--gray-300);
  border-radius: 0.5rem;
  font-size: var(--text-base);
  background: white;
  cursor: pointer;
}

.select:focus {
  outline: none;
  border-color: var(--purple-500);
  box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.1);
}
```

### Cards

#### Basic Card
```css
.card {
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: 0.75rem;
  padding: var(--space-6);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.card:hover {
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  border-color: var(--purple-300);
}
```

#### Interactive Card
```css
.card-interactive {
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: 0.75rem;
  padding: var(--space-6);
  cursor: pointer;
  transition: all 0.2s ease;
}

.card-interactive:hover {
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  border-color: var(--purple-300);
  background: linear-gradient(135deg, var(--purple-50), var(--blue-50));
}
```

### Status Indicators

#### Success State
```css
.status-success {
  background: var(--green-50);
  border: 1px solid var(--green-200);
  color: var(--green-700);
  padding: var(--space-3) var(--space-4);
  border-radius: 0.5rem;
  font-size: var(--text-sm);
}
```

#### Warning State
```css
.status-warning {
  background: var(--yellow-50);
  border: 1px solid var(--yellow-200);
  color: var(--yellow-700);
  padding: var(--space-3) var(--space-4);
  border-radius: 0.5rem;
  font-size: var(--text-sm);
}
```

#### Error State
```css
.status-error {
  background: var(--red-50);
  border: 1px solid var(--red-200);
  color: var(--red-700);
  padding: var(--space-3) var(--space-4);
  border-radius: 0.5rem;
  font-size: var(--text-sm);
}
```

---

## 🎭 Animation & Transitions

### Standard Transitions
```css
/* Standard transition for most elements */
.transition-standard {
  transition: all 0.2s ease;
}

/* Smooth transition for hover effects */
.transition-smooth {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Fast transition for immediate feedback */
.transition-fast {
  transition: all 0.15s ease;
}
```

### Hover Effects
```css
/* Subtle lift effect */
.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
}

/* Scale effect for buttons */
.hover-scale:hover {
  transform: scale(1.02);
}

/* Glow effect for primary elements */
.hover-glow:hover {
  box-shadow: 0 0 20px rgba(168, 85, 247, 0.3);
}
```

### Loading States
```css
/* Pulse animation for loading */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.loading-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Spin animation for spinners */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-spin {
  animation: spin 1s linear infinite;
}
```

---

## 📱 Responsive Design

### Breakpoints
```css
/* Mobile First Approach */
--breakpoint-sm: 640px;   /* Small devices */
--breakpoint-md: 768px;   /* Medium devices */
--breakpoint-lg: 1024px;  /* Large devices */
--breakpoint-xl: 1280px;  /* Extra large devices */
--breakpoint-2xl: 1536px; /* 2X large devices */
```

### Grid System
```css
/* Container */
.container {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--space-4);
}

/* Grid */
.grid {
  display: grid;
  gap: var(--space-6);
}

.grid-cols-1 { grid-template-columns: repeat(1, 1fr); }
.grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
.grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
.grid-cols-4 { grid-template-columns: repeat(4, 1fr); }

/* Responsive utilities */
@media (min-width: 768px) {
  .md\:grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
  .md\:grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
}

@media (min-width: 1024px) {
  .lg\:grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
  .lg\:grid-cols-4 { grid-template-columns: repeat(4, 1fr); }
}
```

---

## ♿ Accessibility Guidelines

### Color Contrast
- **AA Standard**: Minimum 4.5:1 contrast ratio for normal text
- **AAA Standard**: Minimum 7:1 contrast ratio for enhanced accessibility
- **Large Text**: Minimum 3:1 contrast ratio for text 18px+ or 14px+ bold

### Focus States
```css
/* Visible focus indicators */
.focus-visible {
  outline: 2px solid var(--purple-500);
  outline-offset: 2px;
}

/* Custom focus ring */
.focus-ring:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.3);
}
```

### Screen Reader Support
- Use semantic HTML elements
- Provide alt text for images
- Use ARIA labels and descriptions
- Ensure keyboard navigation works
- Test with screen readers

---

## 🎨 Icon System

### Icon Guidelines
- **Size**: 16px, 20px, 24px standard sizes
- **Style**: Outline style for consistency
- **Weight**: 1.5px stroke weight
- **Library**: Lucide React for consistency

### Usage
```tsx
import { User, Settings, Bell } from 'lucide-react';

// Standard size (20px)
<User className="w-5 h-5" />

// Small size (16px)
<Settings className="w-4 h-4" />

// Large size (24px)
<Bell className="w-6 h-6" />
```

---

## 🌙 Dark Mode Support

### CSS Variables for Theming
```css
/* Light theme (default) */
:root {
  --bg-primary: var(--gray-50);
  --bg-secondary: white;
  --text-primary: var(--gray-900);
  --text-secondary: var(--gray-600);
  --border-primary: var(--gray-200);
}

/* Dark theme */
[data-theme="dark"] {
  --bg-primary: var(--gray-900);
  --bg-secondary: var(--gray-800);
  --text-primary: var(--gray-100);
  --text-secondary: var(--gray-400);
  --border-primary: var(--gray-700);
}
```

---

## 📋 Component Checklist

When creating new components, ensure:

### ✅ Design
- [ ] Follows color system
- [ ] Uses consistent spacing
- [ ] Implements proper typography
- [ ] Includes hover/focus states
- [ ] Responsive design

### ✅ Accessibility
- [ ] Keyboard navigation
- [ ] Screen reader support
- [ ] Color contrast compliance
- [ ] Focus indicators
- [ ] ARIA attributes

### ✅ Functionality
- [ ] Error states
- [ ] Loading states
- [ ] Empty states
- [ ] Edge cases handled
- [ ] Performance optimized

### ✅ Documentation
- [ ] Usage examples
- [ ] Props documented
- [ ] Variants explained
- [ ] Accessibility notes
- [ ] Browser support

---

## 🚀 Implementation Guidelines

### File Structure
```
src/
├── components/
│   ├── ui/              # Reusable UI components
│   ├── forms/           # Form components
│   ├── layout/          # Layout components
│   └── features/        # Feature-specific components
├── styles/
│   ├── globals.css      # Global styles
│   ├── components.css   # Component styles
│   └── utilities.css    # Utility classes
└── design-tokens/
    ├── colors.ts        # Color definitions
    ├── typography.ts    # Typography scale
    └── spacing.ts       # Spacing system
```

### Best Practices
1. **Mobile First**: Design for mobile, enhance for desktop
2. **Progressive Enhancement**: Core functionality works without JavaScript
3. **Performance**: Optimize images, minimize CSS, lazy load components
4. **Consistency**: Use design tokens and component library
5. **Testing**: Test across devices, browsers, and accessibility tools

This design system provides a solid foundation for consistent, accessible, and beautiful user interfaces across your entire application.