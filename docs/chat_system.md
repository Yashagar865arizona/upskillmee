# Ponder Chat System Documentation

## Overview
The Ponder chat system is a real-time learning platform that integrates AI-generated learning plans with an interactive project board. The system consists of both frontend React components and backend WebSocket services.

## Key Components

### 1. Chat Components

#### `Chat.jsx`
- **Purpose**: Main chat container that handles WebSocket connection and message state
- **Key Features**:
  - WebSocket connection management
  - Message history state
  - Learning plan integration
  - Auto-scrolling to latest messages
- **State Management**:
  ```javascript
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [currentPlan, setCurrentPlan] = useState(null);
  ```

#### `ChatContainer.jsx`
- **Purpose**: Handles WebSocket message processing and UI rendering
- **Key Features**:
  - WebSocket reconnection logic
  - Message processing with learning plan detection
  - Initial message loading
- **Dependencies**:
  ```javascript
  useCallback(() => {
    // WebSocket connection logic
  }, [messages.length]);
  ```

#### `ChatMessage.jsx`
- **Purpose**: Individual message component with plan indicators
- **Props**:
  - `content`: Message text
  - `isUser`: Boolean indicating if message is from user
  - `userName`: Display name
  - `plan`: Optional learning plan data

### 2. Project Board Components

#### `ProjectBoard.jsx`
- **Purpose**: Displays learning plans in a structured timeline
- **Key Features**:
  - Phase-based learning display
  - Intersection Observer for animations
  - Empty state handling
- **Data Structure**:
  ```javascript
  const phases = [
    {
      id: 1,
      weeks: "1-2",
      title: "Getting Started",
      description: plan.overview,
      tasks: plan.timeline.daily[0].tasks,
      tags: plan.timeline.daily[0].learning_concepts
    },
    // ... more phases
  ];
  ```

#### `ProjectCard.jsx`
- **Purpose**: Individual project phase card
- **Props**:
  - `title`: Phase title
  - `description`: Phase description
  - `tasks`: Array of tasks
  - `skills`: Array of skill tags
  - `weeks`: Timeline indicator

### 3. Navigation Components

#### `ChatSidebar.jsx`
- **Purpose**: Navigation and quick actions sidebar
- **Features**:
  - Editing actions
  - Learning recommendations
  - Project suggestions
- **Action Categories**:
  - Editing actions (Schedule, Personalization, Questions)
  - Learning actions (Courses, Networking, Interviews)
  - Project actions (Marketing, E-commerce, Social Media)

## Data Flow

1. **Learning Plan Creation**:
   ```javascript
   // Backend sends plan
   {
     type: 'learning_plan',
     plan: {
       title: string,
       overview: string,
       timeline: {
         daily: [{
           tasks: string[],
           learning_concepts: string[]
         }],
         weekly: [{
           milestones: string[],
           projects: string[]
         }],
         monthly: {
           final_objectives: string[]
         }
       }
     }
   }
   ```

2. **Message Processing**:
   - Regular messages are added to chat history
   - Learning plan messages update both chat and project board
   - Plan indicators show in chat messages

## CSS Modules

### `Chat.module.css`
- Message styling
- Plan badge styling
- Layout management

### `ProjectBoard.module.css`
- Phase card styling
- Animation classes
- Empty state styling

### `ChatSidebar.module.css`
- Sidebar layout
- Action button styling
- Section containers

## Recent Updates

1. **Hook Fixes**:
   - Added proper dependencies to useCallback in ChatContainer
   - Moved useEffect before conditional returns in ProjectBoard
   - Added null checks for refs in ChatSidebar

2. **UI Improvements**:
   - Added plan indicators to chat messages
   - Improved empty state handling in project board
   - Enhanced animation reliability with null checks

## Next Steps

1. **Planned Improvements**:
   - Enhanced error handling for WebSocket connections
   - Better loading states for plan generation
   - More interactive project board features

2. **Known Issues**:
   - WebSocket reconnection could be more robust
   - Project board animations might need performance optimization
   - Plan data structure could be more flexible

## Environment Setup

1. **WebSocket Connection**:
   - Default URL: `ws://localhost:8000/ws/${userId}`
   - Reconnection interval: 2000ms

2. **Required Environment Variables**:
   - None currently in frontend (handled by backend)

## Development Guidelines

1. **React Hooks**:
   - Always place hooks before conditional returns
   - Include all dependencies in useEffect/useCallback
   - Add null checks for refs and DOM queries

2. **State Management**:
   - Use local state for UI components
   - WebSocket state in main Chat component
   - Plan data flows down through props

3. **CSS Modules**:
   - Keep styles modular and scoped
   - Use consistent naming conventions
   - Maintain separate files for major components
