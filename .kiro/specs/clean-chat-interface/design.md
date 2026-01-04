# Design Document

## Overview

The SportAI Chat Interface is a modern cross-platform React Native application that provides users with a premium chat experience for interacting with sports-focused AI capabilities across iOS, Android, and web platforms. The design emphasizes clean aesthetics, intuitive navigation, and seamless performance while maintaining the professional quality found in leading AI chat applications like Kiro, ChatGPT, and Claude.

The interface features a sophisticated blue-based color palette with full light and dark mode support, Inter typography with careful attention to spacing and hierarchy, and strategic use of SportAI's brand colors to create an engaging yet professional experience that embodies the brand promise: "The future of fantasy sports" with "Lineups, optimized" to help users "Start winning" through "One platform for everything".

Built with React Native and React Native Web, the application ensures consistent user experience across mobile devices (iOS/Android) and web browsers, while leveraging a FastAPI backend for robust sports AI capabilities.

### UI Layout Behavior

**Initial State**: 
- Clean interface with SportAI branding in header
- Hamburger menu icon in top-left corner
- Large, centered chat input bubble in the middle of the screen with send button
- Welcoming message or prompt encouraging user interaction
- Input bubble expands vertically as user types longer messages

**After First Message**:
- Input bubble smoothly transitions from center to bottom of screen
- Scrollable message history area appears above the input area
- Message history automatically scrolls to show latest messages
- Users can scroll up to view conversation history
- Conversation layout with distinct message styling:
  - **User Messages**: Displayed in styled bubbles taking 60% of screen width, right-aligned
  - **AI Responses**: Displayed as plain text taking 100% of screen width, left-aligned, with theme-appropriate colors (white text in dark mode, black text in light mode)
  - **AI Animation**: LLM responses fade in character by character with smooth animation
- Input area remains fixed at bottom for continued interaction
- Text input expands vertically based on content length
- Send button always visible and accessible
- Input area scrolls internally for very long messages

**Side Menu**:
- Hamburger menu in top-left opens slide-out menu
- Menu contains chat history list with previous conversations
- Each history item shows conversation title, last message preview, and timestamp
- "New Chat" option to start fresh conversation
- Menu slides in from left side with smooth animation

**Footer**:
- Fixed at bottom of screen showing subscription information
- Format: "Sport AI [Subscription Type] ([tokens used]/[tokens left]) ([x days left]) updated [x minutes/hours/days ago]"
- Example: "Sport AI Premium (1,250/5,000) (23 days left) updated 5 minutes ago"
- Subtle styling that doesn't interfere with chat interface
- Real-time updates of token usage and time information

### Cross-Platform Compatibility

The application supports multiple platforms with consistent functionality:

- **iOS**: Native iOS app with platform-specific design guidelines and behavior patterns
- **Android**: Native Android app following Material Design principles and interaction patterns  
- **Web**: Browser-based application using React Native Web for desktop and mobile web access
- **Universal Features**: Touch gestures, keyboard handling, and smooth animations across all platforms

### Microservice Architecture

The application follows a microservice architecture pattern:

**Frontend Service**:
- React Native application serving iOS, Android, and Web platforms
- Independent deployment and scaling
- Communicates with backend services via REST APIs

**Backend Microservices**:
- **Chat Service**: Handles conversation management, message routing, and chat history
- **Sports LLM Service**: Existing sports AI processing (no modifications to LLM/modeling)
- **User Service**: User authentication, preferences, and session management
- **API Gateway**: Routes requests between frontend and appropriate microservices

### Backend Integration Constraints

The frontend will integrate with the existing microservice infrastructure:

- **Preserve Existing LLM**: No modifications to the LLM model, training, or inference logic
- **Preserve Modeling**: No changes to sports data modeling, vector collections, or AI processing
- **Service Boundaries**: Clean separation between chat management and AI processing services
- **API Gateway Integration**: All frontend requests routed through centralized API gateway
- **Service Communication**: Microservices communicate via REST APIs and message queues
- **Independent Scaling**: Each service can scale independently based on demand

The interface will replace the current basic testing setup with a production-ready solution that showcases the SportAI brand through thoughtful visual design, smooth animations, and responsive interactions optimized for both iOS and Android platforms.

## Architecture

### Component Hierarchy
```
App
├── ChatScreen
│   ├── Header
│   │   ├── HamburgerMenu (top-left)
│   │   └── SportAI Branding (center)
│   ├── SideMenu (chat history)
│   │   ├── ChatHistoryList
│   │   └── NewChatButton
│   ├── MessageArea
│   │   ├── CenteredInputBubble (initial state)
│   │   ├── ScrollableMessageHistory (after first message)
│   │   │   ├── UserMessageBubble (User messages in bubbles)
│   │   │   ├── AIMessageText (AI responses as plain text)
│   │   │   └── TypingIndicator
│   │   └── BottomInputArea (after first message)
│   │       ├── MultilineTextInput (auto-expanding based on content)
│   │       ├── SendButton (always visible)
│   │       └── LoadingIndicator
│   └── Footer
│       ├── SubscriptionInfo
│       ├── TokenUsage
│       └── LastUpdated
└── Theme Provider
```

### Technology Stack
- **Frontend Framework**: React Native with TypeScript for cross-platform development
- **Platform Support**: iOS, Android, and Web (React Native Web)
- **Backend Architecture**: Microservice architecture with existing FastAPI services (no modifications to LLM/modeling components)
- **State Management**: React Context API with useReducer for chat state
- **Styling**: React Native StyleSheet with theme system (compatible across all platforms)
- **Navigation**: React Navigation for multi-platform navigation
- **Platform Integration**: React Native's Platform API for iOS/Android/Web differences
- **Backend Integration**: Fetch API for HTTP requests to microservice architecture via API Gateway
- **API Communication**: RESTful endpoints using microservice infrastructure with JSON responses
- **Service Discovery**: API Gateway handles routing to appropriate microservices
- **Backend Constraints**: No modifications to existing LLM or modeling components - only new chat service creation
- **Web Deployment**: React Native Web for browser compatibility
- **Mobile Deployment**: Native iOS and Android applications

### Code Quality Standards
- **Zero Technical Debt**: All code must be production-ready with no shortcuts or temporary solutions
- **Clean Architecture**: Strict separation of concerns with clear component boundaries
- **TypeScript Strict Mode**: Full type safety with no `any` types or type assertions
- **Functional Components**: Modern React patterns with hooks, no class components
- **Immutable State**: All state updates through proper reducers and immutable patterns
- **Error Boundaries**: Comprehensive error handling at component and application levels
- **Performance Optimization**: Lazy loading, memoization, and efficient re-rendering patterns
- **Animation Performance**: Optimized character-by-character animations using React Native Animated API with native driver support
- **Code Documentation**: Clear JSDoc comments for all public interfaces and complex logic
- **Consistent Formatting**: Prettier and ESLint configuration for uniform code style
- **Modular Design**: Reusable components with single responsibility principle

### Security Requirements
- **Authentication**: Secure JWT token-based authentication with refresh tokens
- **API Security**: All API requests authenticated with Bearer tokens
- **Data Encryption**: Sensitive data encrypted in transit (HTTPS) and at rest
- **Input Validation**: All user inputs sanitized and validated on both client and server
- **Token Management**: Secure storage of authentication tokens using platform-specific secure storage
- **Session Management**: Automatic token refresh and secure session handling
- **Rate Limiting**: Protection against API abuse and token exhaustion
- **CORS Configuration**: Proper cross-origin resource sharing configuration
- **Data Privacy**: No sensitive user data logged or exposed in client-side code
- **Secure Communication**: All microservice communication over encrypted channels

### Design System
- **Typography**: Inter font family with -3% letter spacing for titles, Semi-bold weight for titles
- **Color Palette**: 
  - **Main Themes**: White backgrounds (#FAFAFA, #FFFFFF) for light mode, Black backgrounds (#000000, #494949) for dark mode
  - **Accent Blues**: #007AFF (Primary accent for buttons/highlights), #1C3E63 (Dark Blue), #3A98FE (Light Blue), #DFEEFF (Background Blue)
  - **Neutrals**: #000000 (Black), #494949 (Dark Gray), #C6C6C6 (Medium Gray), #E6E6E6 (Light Gray), #FAFAFA (Off White), #FFFFFF (White)
  - **Error States**: #FF0000 (Error Red), #FFB9B9 (Background Red)
- **Themes**: Primary white/black themes with blue accents for light and dark modes
- **Spacing**: 8px grid system for consistent layout
- **Animations**: React Native Animated API for smooth transitions
  - **Input Transition**: Smooth animation from center to bottom on first message
  - **AI Text Animation**: Character-by-character fade-in for LLM responses
  - **Menu Slide**: Smooth slide-in/out animation for hamburger menu
  - **Loading States**: Subtle pulse animations for loading indicators
- **Icons**: React Native Vector Icons for UI elements
- **Brand Slogans**: "The future of fantasy sports", "Lineups, optimized", "Start winning", "One platform for everything"

## Components and Interfaces

### ChatScreen Component
```typescript
interface ChatScreenProps {
  theme: Theme;
}

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  inputText: string;
  error: string | null;
}
```

### Message Component
```typescript
interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  status: 'sent' | 'delivered' | 'error';
}

interface MessageBubbleProps {
  message: Message;
  theme: Theme;
  displayStyle: 'bubble' | 'text'; // bubble for user, text for AI
}

interface UserMessageBubbleProps {
  message: Message;
  theme: Theme;
  width: '60%';
  alignment: 'right';
}

interface AIMessageTextProps {
  message: Message;
  theme: Theme;
  animationSpeed?: number; // Characters per second for fade-in animation
  width: '100%';
  alignment: 'left';
}

interface MessageLayoutProps {
  width: '60%' | '100%'; // 60% for user bubbles, 100% for AI text
  alignment: 'left' | 'right'; // left for AI responses, right for user messages
}

interface TextAnimationConfig {
  charactersPerSecond: number; // Speed of character-by-character animation
  fadeInDuration: number; // Duration for each character fade-in (ms)
  staggerDelay: number; // Delay between character animations (ms)
}

interface ScrollableMessageHistoryProps {
  messages: Message[];
  theme: Theme;
  autoScroll: boolean; // Automatically scroll to bottom on new messages
  onScroll?: (event: ScrollEvent) => void;
}

interface MultilineTextInputProps {
  value: string;
  onChangeText: (text: string) => void;
  placeholder: string;
  maxHeight: number; // Maximum height before scrolling
  autoExpand: boolean; // Expand height based on content
  theme: Theme;
}

interface SendButtonProps {
  onPress: () => void;
  disabled: boolean; // Disabled when input is empty or loading
  isLoading: boolean;
  theme: Theme;
}
```

### InputArea Component
```typescript
interface InputAreaProps {
  onSendMessage: (text: string) => void;
  isLoading: boolean;
  theme: Theme;
  position: 'centered' | 'bottom'; // Centered initially, moves to bottom after first message
}

interface CenteredInputBubbleProps {
  onSendMessage: (text: string) => void;
  isLoading: boolean;
  theme: Theme;
  onFirstMessage: () => void; // Triggers transition to bottom layout
}
```

### HamburgerMenu Component
```typescript
interface HamburgerMenuProps {
  onToggleMenu: () => void;
  theme: Theme;
}

interface SideMenuProps {
  isVisible: boolean;
  onClose: () => void;
  chatHistory: ChatHistoryItem[];
  onSelectChat: (chatId: string) => void;
  onNewChat: () => void;
  theme: Theme;
}

interface ChatHistoryItem {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messageCount: number;
}
```

### Footer Component
```typescript
interface FooterProps {
  subscriptionInfo: SubscriptionInfo;
  theme: Theme;
}

interface SubscriptionInfo {
  subscriptionType: string; // e.g., "Sport AI Premium", "Sport AI Basic"
  tokensUsed: number;
  tokensRemaining: number;
  daysLeft: number;
  lastUpdated: Date;
}

interface TokenUsageProps {
  tokensUsed: number;
  tokensRemaining: number;
  theme: Theme;
}
```

### Theme System
```typescript
interface Theme {
  colors: {
    // Main Theme Colors (White/Black based)
    background: string; // #FAFAFA (light mode) / #000000 (dark mode)
    surface: string; // #FFFFFF (light mode) / #494949 (dark mode)
    text: string; // #000000 (light mode) / #FAFAFA (dark mode) - for AI responses
    textSecondary: string; // #494949 (light mode) / #C6C6C6 (dark mode)
    border: string; // #E6E6E6 (light mode) / #494949 (dark mode)
    
    // Message-specific colors
    userBubbleBackground: string; // User message bubble background
    userBubbleText: string; // User message text color
    aiResponseText: string; // AI response plain text color (follows main text color)
    
    // Accent Blues (for buttons, highlights, and attention)
    primaryDark: '#1C3E63';
    primary: '#007AFF'; // Main accent color for buttons and highlights
    primaryLight: '#3A98FE';
    primaryBackground: '#DFEEFF'; // Light blue backgrounds
    
    // Neutral Grays
    black: '#000000';
    darkGray: '#494949';
    mediumGray: '#C6C6C6';
    lightGray: '#E6E6E6';
    offWhite: '#FAFAFA';
    white: '#FFFFFF';
    
    // Error States
    error: '#FF0000';
    errorBackground: '#FFB9B9';
  };
  typography: {
    title: {
      fontFamily: 'Inter';
      fontWeight: '600'; // Semi-bold
      letterSpacing: '-3%';
    };
    body: TextStyle;
    caption: TextStyle;
  };
  spacing: {
    xs: 4;
    sm: 8;
    md: 16;
    lg: 24;
    xl: 32;
  };
}
```

## Data Models

### Chat State Model
```typescript
interface ChatState {
  messages: Message[];
  isLoading: boolean;
  inputText: string;
  error: string | null;
  conversationId?: string;
  layoutMode: 'initial' | 'conversation'; // Initial: centered input, Conversation: bottom input with history
  sideMenuVisible: boolean;
  chatHistory: ChatHistoryItem[];
  currentChatId?: string;
  subscriptionInfo: SubscriptionInfo;
  user: UserInfo;
}

interface UserInfo {
  id: string;
  email: string;
  subscriptionTier: string;
  isAuthenticated: boolean;
  authToken: string;
}
```

### Microservice API Integration Model
```typescript
// React Native client interfaces for microservice communication
interface SportAIRequest {
  message: string;
  conversationId?: string;
  timestamp: Date;
  userId?: string;
}

interface SportAIResponse {
  response: string;
  conversationId: string;
  timestamp: Date;
  status: 'success' | 'error';
  error?: string;
}

// Microservice API endpoints through API Gateway
interface APIEndpoints {
  // Chat Service endpoints
  chat: '/api/v1/chat/message';
  conversation: '/api/v1/chat/conversation/{id}';
  chatHistory: '/api/v1/chat/history';
  
  // User Service endpoints
  userAuth: '/api/v1/user/auth';
  userPreferences: '/api/v1/user/preferences';
  subscription: '/api/v1/user/subscription';
  tokenUsage: '/api/v1/user/tokens';
  
  // Sports LLM Service endpoints (existing)
  sportsQuery: '/api/v1/sports/query';
  
  // System endpoints
  health: '/api/v1/health';
}

// Service-to-service communication interfaces
interface ChatServiceRequest {
  userId: string;
  message: string;
  conversationId?: string;
}

interface LLMServiceRequest {
  query: string;
  context?: string;
  userId?: string;
}
```
```

### Storage Model
```typescript
interface ConversationStorage {
  conversationId: string;
  messages: Message[];
  lastUpdated: Date;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Property 1: Input field focus provides visual feedback
*For any* input field focus event, the system should provide visual feedback indicating readiness for input
**Validates: Requirements 1.3**

Property 2: User messages appear with correct styling
*For any* user message sent, the message should appear in the message history with user-specific styling properties
**Validates: Requirements 2.1**

Property 3: AI messages have distinct styling
*For any* AI response received, the message should appear in the message history with AI-specific styling that differs from user messages
**Validates: Requirements 2.2**

Property 4: Auto-scroll to latest message
*For any* new message added to the conversation, the message history should automatically scroll to show the latest message
**Validates: Requirements 2.3**

Property 5: Messages include required metadata
*For any* message displayed, the message should include both timestamp and sender identification
**Validates: Requirements 2.4**

Property 6: Keyboard appearance preserves input accessibility
*For any* keyboard appearance event, the input field should remain visible and accessible
**Validates: Requirements 3.4**

Property 7: Loading indicator appears on message send
*For any* message submission, a loading indicator should immediately become visible
**Validates: Requirements 4.1**

Property 8: Typing indicator during AI processing
*For any* AI processing period, a typing indicator should be displayed
**Validates: Requirements 4.2**

Property 9: Loading indicators removed on completion
*For any* completed AI response, all loading indicators should be removed and the response displayed
**Validates: Requirements 4.3**

Property 10: Error messages displayed on processing errors
*For any* processing error, a clear error message should be displayed
**Validates: Requirements 4.4**

Property 11: Input field ready state management
*For any* system ready state, the input field should be available and focused
**Validates: Requirements 4.5**

Property 12: Text input acceptance within limits
*For any* reasonable-length text input, the input field should accept the text without character limit restrictions
**Validates: Requirements 5.1**

Property 13: Enter key message sending behavior
*For any* Enter key press (without Shift), the message should be sent; for Shift+Enter, a new line should be created
**Validates: Requirements 5.2**

Property 14: Send button state based on input content
*For any* input field with text content, the send button should be enabled and visually indicated
**Validates: Requirements 5.3**

Property 15: Empty input validation
*For any* empty input field, the send button should be disabled and empty message submission prevented
**Validates: Requirements 5.4**

Property 16: Input field reset after sending
*For any* successful message submission, the input field should be cleared and prepared for the next message
**Validates: Requirements 5.5**

Property 17: Complete message thread maintenance
*For any* conversation with multiple messages, all messages should remain visible in the message thread
**Validates: Requirements 6.1**

Property 18: Message persistence during scrolling
*For any* scrolling action in message history, all previous messages should remain preserved and accessible
**Validates: Requirements 6.2**

Property 19: Conversation state restoration
*For any* interface refresh, the current conversation state should be restored
**Validates: Requirements 6.3**

Property 20: Chronological message ordering
*For any* conversation display, messages should maintain chronological order
**Validates: Requirements 6.5**

Property 21: Backend functionality preservation
*For any* sports AI query, the system should maintain all existing AI functionality from the current backend
**Validates: Requirements 7.2**

Property 22: Seamless API communication
*For any* backend API interaction, communication should be handled seamlessly without exposing technical details
**Validates: Requirements 7.3**

Property 23: Sports AI capability consistency
*For any* user interaction, the system should provide the same sports AI capabilities as the existing testing interface
**Validates: Requirements 7.4**

## Error Handling

### Input Validation
- Empty message prevention with visual feedback
- Character limit handling for extremely long inputs
- Special character and emoji support
- Network connectivity validation before sending

### API Error Management
- Network timeout handling with retry mechanisms
- Backend service unavailability graceful degradation
- Malformed response handling with user-friendly messages
- Rate limiting awareness and user notification

### UI Error States
- Loading state timeout protection
- Scroll position recovery on errors
- Input field state preservation during errors
- Conversation state backup and recovery

### Platform-Specific Error Handling
- iOS keyboard handling edge cases
- Android back button behavior
- Memory management for long conversations
- Background/foreground state transitions

## Testing Strategy

### Unit Testing Approach
The application will use Jest and React Native Testing Library for unit testing, focusing on:

- Component rendering and prop handling
- State management and reducer logic
- API integration functions
- Theme and styling utilities
- Platform-specific behavior isolation

Unit tests will cover specific examples, edge cases, and error conditions to ensure individual components work correctly in isolation.

### Property-Based Testing Approach
The application will use fast-check (JavaScript property-based testing library) for property-based testing, configured to run a minimum of 100 iterations per property test.

Each property-based test will be tagged with comments explicitly referencing the correctness property from this design document using the format: **Feature: clean-chat-interface, Property {number}: {property_text}**

Property-based tests will verify universal properties that should hold across all inputs, providing comprehensive coverage of the system's behavior under various conditions.

### Integration Testing
- End-to-end message flow testing
- Backend API integration validation
- Platform-specific behavior verification
- Performance testing for long conversations

### Testing Requirements
- Unit tests and property tests are complementary and both must be included
- Property-based tests must run a minimum of 100 iterations
- Each correctness property must be implemented by a single property-based test
- Tests must be tagged with explicit references to design document properties
- Both testing approaches together provide comprehensive coverage: unit tests catch concrete bugs, property tests verify general correctness

### Clean Code Testing Standards
- **100% Test Coverage**: All components, utilities, and business logic must have comprehensive tests
- **Test-Driven Development**: Tests written before or alongside implementation
- **Clear Test Names**: Descriptive test names that explain the expected behavior
- **Isolated Tests**: No test dependencies or shared state between test cases
- **Mock Minimization**: Prefer integration testing over heavy mocking when possible
- **Performance Testing**: Automated performance benchmarks for critical user interactions
- **Accessibility Testing**: Automated accessibility compliance verification
- **Cross-Platform Testing**: Consistent behavior validation across iOS, Android, and Web