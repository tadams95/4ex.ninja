# 🎨 Consistent Color Scheme Documentation

## Updated Wallet Button Colors

### ✅ **Aligned Color Palette**

All wallet components now use the exact same green color scheme as the rest of your app:

#### **Green Color Usage:**

- **`green-400`**: Link hovers, connection indicators, outline button text
- **`green-600`**: Primary button backgrounds, solid borders
- **`green-700`**: Primary button hover states, hover borders
- **`green-300`**: Hover states for green-400 elements

### **Component Color Mapping:**

#### **WalletButton**

```tsx
// Primary variant (matches WelcomeBanner buttons)
primary: 'bg-green-600 hover:bg-green-700 text-white border-green-600 hover:border-green-700';

// Outline variant (matches Header link hovers)
outline: 'bg-transparent hover:bg-green-600/10 text-green-400 border-green-400 hover:text-green-300 hover:border-green-300';

// Secondary variant (neutral gray)
secondary: 'bg-gray-700 hover:bg-gray-600 text-white border-gray-700 hover:border-gray-600';
```

#### **WalletProfile**

```tsx
// Connection indicator (matches Header account link)
bg - green - 400; // Pulsing dot indicator
```

#### **Header Navigation**

```tsx
// Account link (when connected)
text-green-400 hover:text-green-300

// Navigation link hovers
hover:text-green-400
```

#### **WelcomeBanner**

```tsx
// Primary action button
bg-green-600 hover:bg-green-700

// Secondary action button
border-green-600 text-green-400 hover:bg-green-600/10

// Background gradient
from-green-900/20 to-green-800/20 border-green-700/30

// Connected status
text-green-400 bg-green-400 (indicator dot)
```

### **Consistency Benefits:**

✅ **Visual Harmony**: All green elements use the same shade progression  
✅ **Brand Recognition**: Consistent green reinforces your brand identity  
✅ **User Experience**: Familiar colors create intuitive interactions  
✅ **Design System**: Scalable color tokens for future components

### **Color Hierarchy:**

1. **Primary Actions**: `green-600` → `green-700` (solid buttons)
2. **Secondary Actions**: `green-400` → `green-300` (links, outlines)
3. **Status Indicators**: `green-400` (connection dots, badges)
4. **Backgrounds**: `green-900/20` to `green-800/20` (subtle gradients)
5. **Borders**: `green-700/30` to `green-400` (contextual weight)

This creates a cohesive, professional appearance where every wallet interaction feels seamlessly integrated with your app's design language.
