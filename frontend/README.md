# ProjectAria Frontend 🎨

The React-based frontend for ProjectAria.PA - a Multi-Service Business Intelligence Platform.

## 🎯 Overview

This frontend provides a modern, responsive web interface for interacting with ProjectAria's AI-powered business management system. It includes real-time chat, calendar management, accounting integration, and more.

## 🛠️ Tech Stack

- **React 18** - Modern React with hooks and concurrent features
- **Vite** - Fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router v6** - Client-side routing
- **WebSocket** - Real-time communication
- **Lucide React** - Beautiful icon library

## 🚀 Features

### **🤖 AI Chat Interface**
- **Real-time Chat**: WebSocket-powered chat with AI assistant
- **Rich Formatting**: Markdown support with clickable links and emails
- **Message History**: Persistent chat history with local timestamps
- **Typing Indicators**: Real-time typing status
- **Connection Status**: Visual connection state indicators

### **📅 Calendar Integration**
- **Event Management**: View and manage Google Calendar events
- **Smart Scheduling**: Natural language event creation
- **Conflict Detection**: Automatic scheduling conflict resolution
- **Rich Event Details**: Clickable meeting links and organizer emails

### **💼 Accounting Dashboard**
- **Tally Integration**: Direct connection to Tally ERP
- **Financial Data**: Ledger balances, transactions, and reports
- **Stock Management**: Inventory tracking and item management
- **Party Management**: Customer and vendor information

### **🔐 Authentication**
- **Google OAuth**: Secure authentication with Google
- **JWT Sessions**: Secure session management
- **Protected Routes**: Route protection based on authentication
- **User Context**: Personalized experience

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── MinimalNavbar.jsx    # Main navigation
│   │   └── ProtectedRoute.jsx   # Route protection
│   ├── context/             # React context providers
│   │   └── AuthContext.jsx      # Authentication context
│   ├── hooks/              # Custom React hooks
│   │   ├── useAuth.js           # Authentication hook
│   │   └── useWebSocket.js      # WebSocket hook
│   ├── layouts/            # Page layouts
│   │   ├── AuthLayout.jsx        # Authentication layout
│   │   ├── DashboardLayout.jsx  # Main dashboard layout
│   │   └── MainLayout.jsx       # Root layout
│   ├── pages/              # Page components
│   │   ├── Chat.jsx             # AI chat interface
│   │   ├── MinimalDashboard.jsx # Main dashboard
│   │   ├── TallyDashboard.jsx   # Accounting dashboard
│   │   ├── MinimalIntegration.jsx # Integration settings
│   │   └── ...                  # Other pages
│   ├── router/             # Routing configuration
│   │   └── index.jsx            # Route definitions
│   ├── services/           # API services
│   │   ├── api.js               # Base API client
│   │   ├── userService.js      # User API calls
│   │   └── chatService.js       # Chat API calls
│   ├── styles/             # Global styles
│   │   └── globals.css           # Global CSS
│   └── utils/              # Utility functions
│       ├── constants.js         # App constants
│       └── formatDate.js        # Date formatting
├── public/                 # Static assets
└── package.json           # Dependencies and scripts
```

## 🚀 Getting Started

### **Prerequisites**
- Node.js 16+ 
- npm or yarn
- Backend server running (see main README)

### **Installation**
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### **Environment Variables**
Create `.env.local` file:
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## 🎨 UI Components

### **Chat Interface**
- **Modern Design**: Clean, professional chat interface
- **Message Bubbles**: Distinct styling for user and AI messages
- **Rich Content**: Support for links, emails, and formatting
- **Responsive**: Works on desktop and mobile devices
- **Accessibility**: Keyboard navigation and screen reader support

### **Navigation**
- **Minimal Design**: Clean, uncluttered navigation
- **Responsive Menu**: Mobile-friendly navigation
- **User Profile**: User information and logout functionality
- **Status Indicators**: Connection and system status

### **Dashboard**
- **Overview Cards**: Key metrics and information
- **Quick Actions**: Fast access to common tasks
- **Integration Status**: Service connection indicators
- **Recent Activity**: Latest actions and updates

## 🔧 Development

### **Available Scripts**
```bash
npm run dev          # Start development server
npm run build         # Build for production
npm run preview       # Preview production build
npm run lint          # Run ESLint
npm run lint:fix      # Fix ESLint issues
```

### **Code Style**
- **ESLint**: Configured with React and accessibility rules
- **Prettier**: Code formatting (if configured)
- **Conventional Commits**: Standardized commit messages
- **Component Structure**: Functional components with hooks

### **State Management**
- **React Context**: Global state (authentication, theme)
- **Local State**: Component-level state with useState
- **Custom Hooks**: Reusable stateful logic
- **WebSocket State**: Real-time connection management

## 🌐 API Integration

### **Authentication**
```javascript
// Login with Google OAuth
const { login, logout, user, token } = useAuth();

// Protected routes
<ProtectedRoute>
  <DashboardLayout />
</ProtectedRoute>
```

### **WebSocket Chat**
```javascript
// Real-time chat connection
const { 
  connectionStatus, 
  sendMessage, 
  isConnected 
} = useWebSocket(wsUrl, {
  onMessage: handleMessage
});
```

### **API Services**
```javascript
// User service
import { userService } from './services/userService';
const user = await userService.getProfile();

// Chat service
import { chatService } from './services/chatService';
const history = await chatService.getHistory();
```

## 📱 Responsive Design

### **Breakpoints**
- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

### **Mobile Features**
- **Touch-friendly**: Large touch targets
- **Swipe Navigation**: Gesture-based navigation
- **Responsive Typography**: Scalable text sizes
- **Optimized Layout**: Mobile-first design

## 🎨 Styling

### **Tailwind CSS**
- **Utility Classes**: Rapid styling with utility classes
- **Custom Components**: Reusable styled components
- **Dark Mode**: Theme switching support
- **Responsive**: Mobile-first responsive design

### **Design System**
- **Colors**: Consistent color palette
- **Typography**: Hierarchical text styles
- **Spacing**: Consistent spacing scale
- **Components**: Reusable UI components

## 🔒 Security

### **Authentication**
- **JWT Tokens**: Secure token-based authentication
- **Route Protection**: Protected routes and components
- **Token Refresh**: Automatic token refresh
- **Logout**: Secure session termination

### **Data Protection**
- **HTTPS**: Secure data transmission
- **Input Validation**: Client-side validation
- **XSS Protection**: Content sanitization
- **CSRF Protection**: Cross-site request forgery protection

## 🧪 Testing

### **Test Setup**
```bash
# Install testing dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom

# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

### **Testing Strategy**
- **Unit Tests**: Component testing
- **Integration Tests**: API integration testing
- **E2E Tests**: End-to-end user flows
- **Accessibility Tests**: Screen reader compatibility

## 🚀 Deployment

### **Build Process**
```bash
# Production build
npm run build

# Output directory: dist/
# Static files ready for deployment
```

### **Deployment Options**
- **Static Hosting**: Netlify, Vercel, GitHub Pages
- **CDN**: CloudFlare, AWS CloudFront
- **Server**: Nginx, Apache
- **Docker**: Containerized deployment

## 🔧 Configuration

### **Vite Configuration**
```javascript
// vite.config.js
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
});
```

### **Tailwind Configuration**
```javascript
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#3B82F6',
        secondary: '#6B7280'
      }
    }
  }
};
```

## 📚 Documentation

### **Component Documentation**
- **Props**: Component prop types and descriptions
- **Examples**: Usage examples and code snippets
- **Styling**: CSS classes and styling options
- **Accessibility**: ARIA attributes and keyboard navigation

### **API Documentation**
- **Endpoints**: Available API endpoints
- **Authentication**: Authentication requirements
- **WebSocket**: Real-time communication protocol
- **Error Handling**: Error responses and handling

## 🤝 Contributing

### **Development Workflow**
1. **Fork Repository**: Create your own fork
2. **Create Branch**: `git checkout -b feature/amazing-feature`
3. **Make Changes**: Implement your feature
4. **Test Changes**: Run tests and linting
5. **Commit Changes**: `git commit -m 'Add amazing feature'`
6. **Push Branch**: `git push origin feature/amazing-feature`
7. **Create PR**: Open a pull request

### **Code Standards**
- **ESLint**: Follow configured linting rules
- **Prettier**: Use consistent code formatting
- **Conventional Commits**: Use standard commit messages
- **Documentation**: Update documentation for new features

## 📞 Support

For questions and support:
- **Email**: projectaria.pa@gmail.com
- **Issues**: GitHub Issues
- **Documentation**: Project documentation

## 📄 License

MIT License - see main project LICENSE file.

---

⭐ **Star this repo if you find it helpful!**