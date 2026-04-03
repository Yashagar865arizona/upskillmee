# Agent Testing System 🧪

A comprehensive testing framework for the Ponder AI agent modes without any API costs.

## Overview

This testing system allows you to:
- **Test all 3 agent modes** (Mentor, Project Partner, Learning Path) 
- **Interactive chat testing** with real-time mode switching
- **Automated test scenarios** for each mode
- **No API costs** - everything runs locally with intelligent mocks
- **Realistic agent behavior** simulation

## Files

### Core Testing Files
- `agentMocks.js` - Mock agent system with realistic responses
- `AgentTestHarness.jsx` - Interactive testing interface
- `AgentTestHarness.css` - Styling for the test interface
- `AgentModeSelector.test.js` - Unit tests for the mode selector component

### Integration
- `../pages/AgentTest/AgentTestPage.jsx` - Simple page wrapper

## Quick Start

### 1. Access the Test Interface

Navigate to `/agent-test` in your browser (you'll need to add this route to your router).

### 2. Interactive Testing

- **Chat Interface**: Test conversations with real-time mode switching
- **Mode Selector**: Switch between Mentor, Project Partner, and Learning Path
- **Quick Scenarios**: Click predefined test scenarios for each mode

### 3. Automated Testing

- **Run All Tests**: Test all modes with comprehensive scenarios
- **Individual Mode Tests**: Test specific modes
- **View Results**: See detailed test results with pass/fail status

## Agent Modes

### 🗣️ Mentor Mode (`chat`)
**Purpose**: General guidance and mentoring
**Behavior**: 
- Encouraging and supportive
- Asks thoughtful questions
- Provides emotional support
- Offers personalized advice

**Test Scenarios**:
- "I'm feeling overwhelmed with learning programming"
- "What should I focus on as a beginner?"
- "I just completed my first project!"
- "How do I stay motivated when learning gets tough?"

### 🔧 Project Partner Mode (`work`)
**Purpose**: Execute projects and learning plans
**Behavior**:
- Systematic and step-by-step
- Technical and practical
- Problem-solving focused
- Provides code examples and implementation guidance

**Test Scenarios**:
- "I'm getting an error in my React component"
- "Help me build a todo app with authentication"
- "How do I implement API calls in JavaScript?"
- "My code isn't working, can you help debug it?"

### 📋 Learning Path Mode (`plan`)
**Purpose**: Create learning roadmaps
**Behavior**:
- Structured and goal-oriented
- Progressive learning approach
- Time-aware planning
- Milestone-focused

**Test Scenarios**:
- "Create a learning plan for full stack development"
- "I want to learn data science in 3 months"
- "Update my current learning progress"
- "Plan a roadmap for becoming a frontend developer"

## Mock System Features

### Intelligent Response Generation
The mock system analyzes your input and provides contextually appropriate responses:

```javascript
// Example: Keyword-based response selection
if (messageWords.some(word => ['error', 'bug', 'broken'].includes(word))) {
  return debuggingResponse; // In work mode
}
```

### Realistic Behavior Patterns
Each mode has distinct behavioral characteristics:

- **Mentor**: Motivational, questioning, encouraging
- **Project Partner**: Systematic, technical, practical
- **Learning Path**: Structured, goal-oriented, progressive

### Conversation History
The mock agent maintains conversation context and can reference previous messages.

## Running Tests

### Unit Tests
```bash
npm test AgentModeSelector.test.js
```

### Interactive Testing
1. Start your development server
2. Navigate to the test interface
3. Use the interactive chat or run automated scenarios

### Automated Test Scenarios
Click "🚀 Run All Tests" to execute comprehensive testing across all modes.

## Test Results Analysis

The system provides detailed test results:

### Success Metrics
- ✅ **Response Generation**: Agent responds to all inputs
- ✅ **Mode Consistency**: Responses match the selected mode's behavior
- ✅ **Context Awareness**: Agent provides relevant responses

### Failure Detection
- ❌ **No Response**: Agent fails to generate a response
- ❌ **Wrong Mode**: Response doesn't match expected mode behavior
- ❌ **Context Ignored**: Response is irrelevant to input

## Customization

### Adding New Test Scenarios
```javascript
// In agentMocks.js
const newScenarios = {
  chat: [
    "Your new test scenario here",
    // ... more scenarios
  ]
};
```

### Modifying Agent Responses
```javascript
// In agentMocks.js
const mockAgentResponses = {
  chat: {
    responses: [
      "Your custom response here",
      // ... more responses
    ]
  }
};
```

### Custom Behavior Patterns
```javascript
// Add new behavior logic
generateChatResponse(messageWords, responses) {
  if (messageWords.some(word => ['your', 'custom', 'keywords'].includes(word))) {
    return 'Your custom response logic';
  }
  // ... existing logic
}
```

## Benefits

### 🚀 **Zero API Costs**
Test extensively without worrying about API usage fees.

### 🧠 **Realistic Simulation**
Mock system provides intelligent, contextual responses that simulate real agent behavior.

### 🔄 **Rapid Iteration**
Test changes immediately without waiting for API responses.

### 📊 **Comprehensive Coverage**
Automated scenarios ensure all modes and edge cases are tested.

### 🎯 **User Experience Testing**
Interactive interface lets you experience the agent modes as a user would.

## Development Workflow

1. **Write New Features**: Add new agent functionality
2. **Update Mocks**: Extend mock responses to cover new features
3. **Add Test Scenarios**: Create scenarios to test new functionality
4. **Run Tests**: Verify everything works as expected
5. **Deploy Confidently**: Know your agents work before going live

## Troubleshooting

### Common Issues

**Mock Agent Not Responding**
- Check console for JavaScript errors
- Verify mock system is properly imported

**Test Scenarios Not Running**
- Ensure test data is properly formatted
- Check for timing issues in async operations

**Mode Switching Not Working**
- Verify AgentModeSelector integration
- Check mode state management

### Debug Mode
Enable detailed logging by adding to localStorage:
```javascript
localStorage.setItem('debug_agent_testing', 'true');
```

## Future Enhancements

- **Performance Metrics**: Track response times and system performance
- **A/B Testing**: Compare different response strategies
- **User Journey Testing**: Simulate complete learning workflows
- **Integration Testing**: Test with real backend components

---

**Happy Testing!** 🎉

This system ensures your agent modes work perfectly before users interact with them, saving time, money, and potential user frustration. 