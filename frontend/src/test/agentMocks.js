/**
 * Mock Agent System for Testing Different Modes
 * Simulates all agent modes without API calls
 */

// Mock responses for each agent mode
export const mockAgentResponses = {
  chat: {
    responses: [
      "I'm here to help guide you on your learning journey! What are you currently working on or interested in learning?",
      "That's a great question! Let me share some insights that might help you think through this differently...",
      "Learning programming can feel overwhelming at first, but remember that every expert was once a beginner. What specific area would you like to focus on?",
      "I understand you're feeling stuck. This is completely normal in the learning process. Let's break this down into smaller, manageable steps.",
      "Your progress sounds impressive! It's important to celebrate these wins. What challenge would you like to tackle next?",
      "I can see you're passionate about this topic. That enthusiasm will be your greatest asset. How can I help you channel it effectively?"
    ],
    behaviorPatterns: {
      motivational: true,
      askingQuestions: true,
      providingEncouragement: true,
      personalizedAdvice: true
    }
  },

  work: {
    responses: [
      "Let's tackle this project step by step. First, can you tell me more about what you're trying to build?",
      "I see the issue! This is a common problem when working with APIs. Here's how we can approach it systematically...",
      "Great project idea! Let's break this down into actionable tasks:\n\n1. Set up the basic structure\n2. Implement core functionality\n3. Add error handling\n4. Test and refine",
      "For this feature, you'll need to consider both the frontend and backend components. Let me walk you through the implementation strategy...",
      "I notice you're working with React. Here's a practical approach that follows best practices for this type of component...",
      "Let's debug this together. Can you share the error message you're seeing? I'll help you identify the root cause and fix it.",
      "This is an excellent learning opportunity! While we solve this immediate problem, I'll also explain the underlying concepts so you understand the 'why' behind the solution."
    ],
    behaviorPatterns: {
      systematic: true,
      stepByStep: true,
      technical: true,
      practical: true,
      problemSolving: true
    },
    projectTypes: [
      "web application",
      "mobile app", 
      "data analysis project",
      "automation script",
      "portfolio website",
      "learning management system"
    ]
  },

  plan: {
    responses: [
      "I'd love to create a personalized learning plan for you! To get started, tell me:\n- What do you want to learn?\n- What's your current experience level?\n- How much time can you dedicate weekly?",
      "Based on your goals, I'm creating a structured 12-week learning roadmap. This will include:\n\n📚 Core concepts\n🛠️ Hands-on projects\n🎯 Milestones\n📈 Progress tracking",
      "Excellent choice! Here's your customized learning path:\n\n**Week 1-3:** Foundations\n**Week 4-6:** Core Skills\n**Week 7-9:** Projects\n**Week 10-12:** Advanced Topics",
      "I've updated your learning plan based on your progress! Here are the next recommended steps to keep you moving forward effectively.",
      "Your learning plan is now ready! I've structured it to build knowledge progressively while keeping you engaged with practical projects.",
      "Let me adjust your plan based on your available time. I'm optimizing it for maximum learning efficiency within your schedule."
    ],
    behaviorPatterns: {
      structured: true,
      goalOriented: true,
      progressive: true,
      timeAware: true,
      milestone_focused: true
    },
    planTypes: [
      "Full Stack Development",
      "Data Science Fundamentals", 
      "Mobile App Development",
      "Machine Learning Basics",
      "Web Design & UX",
      "Python Programming",
      "JavaScript Mastery"
    ]
  }
};

// Simulate different conversation contexts
export const mockContexts = {
  beginner: {
    experience: "beginner",
    tone: "encouraging",
    detailLevel: "high",
    examples: "basic"
  },
  intermediate: {
    experience: "intermediate", 
    tone: "collaborative",
    detailLevel: "medium",
    examples: "practical"
  },
  advanced: {
    experience: "advanced",
    tone: "technical",
    detailLevel: "low", 
    examples: "complex"
  }
};

// Mock agent behavior simulator
export class MockAgentSimulator {
  constructor() {
    this.currentMode = 'chat';
    this.conversationHistory = [];
    this.userContext = mockContexts.beginner;
    this.performanceMode = false; // For high-load testing
    this.batchSize = 100; // Process in batches for memory efficiency
    this.autoOptimize = true; // Can be disabled for scalability tests
  }

  // Performance optimization methods
  enablePerformanceMode(batchSize = 100) {
    this.performanceMode = true;
    this.batchSize = batchSize;
    console.log(`🚀 Performance mode enabled with batch size: ${batchSize}`);
  }

  disablePerformanceMode() {
    this.performanceMode = false;
    console.log('🔄 Performance mode disabled');
  }

  // Disable auto-optimization for scalability tests
  disableAutoOptimization() {
    this.autoOptimize = false;
    console.log('🔧 Auto-optimization disabled for testing');
  }

  enableAutoOptimization() {
    this.autoOptimize = true;
    console.log('🔧 Auto-optimization enabled');
  }

  // Batch processing for high-load scenarios
  async processBatchMessages(messages, mode = null) {
    if (!Array.isArray(messages)) {
      throw new Error('Messages must be an array');
    }

    const results = [];
    const activeMode = mode || this.currentMode;
    
    // Process in smaller batches to manage memory
    for (let i = 0; i < messages.length; i += this.batchSize) {
      const batch = messages.slice(i, i + this.batchSize);
      
      // Process batch concurrently but with minimal delay in performance mode
      const batchPromises = batch.map(async (message, index) => {
        const actualMessage = typeof message === 'string' ? message : `Batch message ${i + index}`;
        
        // Minimal delay in performance mode
        if (!this.performanceMode) {
          await new Promise(resolve => setTimeout(resolve, 100 + Math.random() * 200));
        } else {
          // Very small delay to simulate minimal processing time
          await new Promise(resolve => setTimeout(resolve, 1 + Math.random() * 3));
        }
        
        return this.processMessageSync(actualMessage, activeMode);
      });
      
      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);
      
      // Yield to event loop between batches
      await new Promise(resolve => setTimeout(resolve, 0));
    }
    
    return results;
  }

  // Synchronous message processing for high-performance scenarios
  processMessageSync(message, mode = null) {
    // Handle null/undefined/empty messages gracefully
    if (message === null || message === undefined || message === '' || 
        (typeof message === 'string' && message.trim() === '') ||
        typeof message === 'number' && (isNaN(message) || !isFinite(message))) {
      message = "Could you please provide more details about what you'd like help with?";
    }

    // Ensure message is a string
    if (typeof message !== 'string') {
      message = String(message || "How can I help you today?");
    }

    // Validate and normalize mode
    let activeMode = mode || this.currentMode;
    if (!mockAgentResponses[activeMode]) {
      activeMode = 'chat'; // Fallback to chat mode for invalid modes
    }
    
    // Add to conversation history with proper timestamp
    const userEntry = { sender: 'user', text: message, timestamp: new Date() };
    this.conversationHistory.push(userEntry);
    
    // Generate response based on mode and context
    const response = this.generateResponse(message, activeMode);
    
    // Add bot response to history
    const botEntry = { sender: 'bot', text: response, mode: activeMode, timestamp: new Date() };
    this.conversationHistory.push(botEntry);
    
    return {
      text: response,
      sender: 'bot',
      mode: activeMode,
      agent_info: {
        mode: activeMode,
        available_modes: Object.keys(mockAgentResponses),
        agent_name: this.getAgentName(activeMode),
        timestamp: new Date().toISOString(),
        response_id: `mock_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      }
    };
  }

  // Memory-efficient history management
  optimizeHistory(maxSize = 1000) {
    if (this.conversationHistory.length > maxSize) {
      // Keep only the most recent entries
      const keepSize = Math.floor(maxSize * 0.8); // Keep 80% when trimming
      this.conversationHistory = this.conversationHistory.slice(-keepSize);
      console.log(`📊 History optimized: kept ${keepSize} recent entries`);
    }
  }

  // Clear history for memory efficiency
  clearHistory() {
    this.conversationHistory = [];
    console.log('🧹 Conversation history cleared');
  }

  setMode(mode) {
    this.currentMode = mode;
    console.log(`🤖 Agent switched to ${mode} mode`);
  }

  setUserContext(context) {
    this.userContext = { ...this.userContext, ...context };
  }

  // Simulate processing delay (like real API)
  async processMessage(message, mode = null) {
    // Handle null/undefined/empty messages gracefully
    if (message === null || message === undefined || message === '' || 
        (typeof message === 'string' && message.trim() === '') ||
        typeof message === 'number' && (isNaN(message) || !isFinite(message))) {
      message = "Could you please provide more details about what you'd like help with?";
    }

    // Ensure message is a string
    if (typeof message !== 'string') {
      message = String(message || "How can I help you today?");
    }

    // Validate and normalize mode
    let activeMode = mode || this.currentMode;
    if (!mockAgentResponses[activeMode]) {
      activeMode = 'chat'; // Fallback to chat mode for invalid modes
    }
    
    // Simulate network delay (reduced in performance mode)
    if (this.performanceMode) {
      await new Promise(resolve => setTimeout(resolve, 2 + Math.random() * 5));
    } else {
      await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 1200));
    }
    
    // Add to conversation history
    this.conversationHistory.push({ sender: 'user', text: message, timestamp: new Date() });
    
    // Generate response based on mode and context
    const response = this.generateResponse(message, activeMode);
    
    this.conversationHistory.push({ sender: 'bot', text: response, mode: activeMode, timestamp: new Date() });
    
    // Auto-optimize history in performance mode (if enabled)
    if (this.performanceMode && this.autoOptimize && this.conversationHistory.length > 2000) {
      this.optimizeHistory(1000);
    }
    
    return {
      text: response,
      sender: 'bot',
      mode: activeMode,
      agent_info: {
        mode: activeMode,
        available_modes: Object.keys(mockAgentResponses),
        agent_name: this.getAgentName(activeMode),
        timestamp: new Date().toISOString(),
        response_id: `mock_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      }
    };
  }

  generateResponse(message, mode) {
    // Ensure valid mode and fallback
    const modeData = mockAgentResponses[mode] || mockAgentResponses['chat'];
    const responses = modeData?.responses || ["I'm here to help! How can I assist you today?"];
    
    // Ensure message is valid for processing
    if (!message || typeof message !== 'string') {
      return responses[0] || "How can I help you today?";
    }
    
    // Simple keyword-based response selection
    const messageWords = message.toLowerCase().split(' ').filter(word => word.length > 0);
    
    // Add context awareness based on user experience level
    let contextualResponse = '';
    
    // Mode-specific response logic with context awareness
    try {
      switch(mode) {
        case 'chat':
          contextualResponse = this.generateChatResponse(messageWords, responses);
          break;
        case 'work':
          contextualResponse = this.generateWorkResponse(messageWords, responses);
          break;
        case 'plan':
          contextualResponse = this.generatePlanResponse(messageWords, responses);
          break;
        default:
          contextualResponse = responses[Math.floor(Math.random() * responses.length)] || "I'm here to help!";
      }
      
      // Enhance response based on user context
      return this.enhanceResponseWithContext(contextualResponse, messageWords, mode);
      
    } catch (error) {
      return responses[0] || "I apologize, but I encountered an issue. How can I help you?";
    }
  }

  // Enhanced response with length awareness
  enhanceResponseWithContext(baseResponse, messageWords, mode) {
    let enhancedResponse = baseResponse;
    
    // Adjust response length based on message complexity
    const messageComplexity = this.assessMessageComplexity(messageWords);
    
    if (messageComplexity === 'high') {
      // Add detailed explanation for complex queries
      enhancedResponse += " This is a multi-faceted challenge that requires careful consideration. Let me break this down into several key components: first, we need to understand the underlying architecture and design patterns that would be most effective. Then we'll consider the implementation strategy, taking into account best practices, scalability requirements, and potential performance implications. I'll guide you through each step systematically to ensure we build a robust, maintainable solution.";
    } else if (messageComplexity === 'low') {
      // Keep simple responses concise
      enhancedResponse = this.simplifyResponse(enhancedResponse);
    }
    
    // ENSURE CONTEXT-SPECIFIC RESPONSES FOR DIFFERENT USER CONTEXTS
    if (this.userContext?.experience && this.userContext?.topic) {
      const experience = this.userContext.experience;
      const topic = this.userContext.topic;
      
      // Add unique context-specific content based on experience + topic combination
      if (experience === 'beginner' && topic === 'JavaScript') {
        enhancedResponse += ` As a JavaScript beginner, I'll focus on fundamental concepts and provide lots of examples to help you understand the basics step by step.`;
      } else if (experience === 'intermediate' && topic === 'React') {
        enhancedResponse += ` With your intermediate React knowledge, I can dive into component lifecycle, hooks, and state management patterns that will help you build more efficient applications.`;
      } else if (experience === 'advanced' && topic === 'Architecture') {
        enhancedResponse += ` Given your advanced architecture background, I'll discuss design patterns, scalability considerations, and enterprise-level solutions that match your expertise level.`;
      } else {
        // Fallback for other combinations to ensure uniqueness
        enhancedResponse += ` Tailored for ${experience} level ${topic} development, I'll adjust my explanation to match your specific experience and learning goals.`;
      }
    }
    
    // Add experience-level appropriate language
    if (this.userContext?.experience === 'beginner') {
      if (messageWords.some(word => ['complex', 'advanced', 'difficult'].includes(word))) {
        enhancedResponse += " Don't worry - I'll explain everything in simple terms and break it down step by step.";
      }
    } else if (this.userContext?.experience === 'advanced') {
      if (messageWords.some(word => ['simple', 'basic', 'easy'].includes(word))) {
        enhancedResponse += " I can dive deeper into the technical details if you'd like more advanced insights.";
      }
    }
    
    // Add topic-specific context if available
    if (this.userContext?.topic && !enhancedResponse.includes(this.userContext.topic)) {
      const topic = this.userContext.topic.toLowerCase();
      if (messageWords.some(word => [topic, 'help', 'learn'].includes(word))) {
        enhancedResponse += ` Since you're working with ${this.userContext.topic}, I'll tailor my guidance specifically for that context.`;
      }
    }
    
    // Reference conversation history for continuity
    if (this.conversationHistory?.length > 2) {
      const recentMessages = this.conversationHistory.slice(-4); // Last 2 exchanges
      const hasRecentContext = recentMessages.some(msg => 
        msg.sender === 'user' && (
          msg.text.toLowerCase().includes('project') ||
          msg.text.toLowerCase().includes('learning') ||
          msg.text.toLowerCase().includes('working')
        )
      );
      
      if (hasRecentContext && messageWords.some(word => ['progress', 'next', 'continue'].includes(word))) {
        enhancedResponse += " Based on our conversation, you're making great progress in your current work.";
      }
    }
    
    return enhancedResponse;
  }

  // Assess message complexity for appropriate response length
  assessMessageComplexity(messageWords) {
    const complexKeywords = [
      'architecture', 'microservices', 'scalability', 'optimization', 'database',
      'real-time', 'processing', 'high-traffic', 'system', 'complex', 'advanced',
      'integration', 'deployment', 'performance', 'distributed', 'enterprise'
    ];
    
    const simpleKeywords = ['hi', 'hello', 'thanks', 'yes', 'no', 'ok', 'good'];
    
    if (messageWords.length > 15 || messageWords.some(word => complexKeywords.includes(word))) {
      return 'high';
    } else if (messageWords.length < 3 || messageWords.some(word => simpleKeywords.includes(word))) {
      return 'low';
    }
    
    return 'medium';
  }

  // Simplify response for simple messages
  simplifyResponse(response) {
    // For very simple greetings, return a concise response
    const sentences = response.split('.').filter(s => s.trim().length > 0);
    if (sentences.length > 1) {
      return sentences[0].trim() + '.';
    }
    return response;
  }

  generateChatResponse(messageWords, responses) {
    if (!Array.isArray(messageWords) || messageWords.length === 0) {
      return responses[0] || "I'm here to support your learning journey! How can I help?";
    }
    
    // Enhanced keyword-based responses for chat mode
    if (messageWords.some(word => ['stuck', 'confused', 'difficult', 'frustrated', 'blocked'].includes(word))) {
      return "I understand you're feeling stuck. This is completely normal in the learning process. Let me help you break this down into manageable steps and provide the support you need.";
    }
    if (messageWords.some(word => ['progress', 'finished', 'completed', 'done', 'achieved'].includes(word))) {
      return "Congratulations on your progress! That's a great achievement and shows your dedication. What challenge would you like to tackle next?";
    }
    if (messageWords.some(word => ['learn', 'start', 'beginning', 'new', 'beginner'].includes(word))) {
      return "Great choice to start learning! I'm here to guide and encourage you every step of the way. What specific area interests you most?";
    }
    if (messageWords.some(word => ['motivation', 'discouraged', 'demotivated', 'quit', 'give', 'up'].includes(word))) {
      return "I understand you're feeling demotivated, and that's completely normal. Remember, every expert was once a beginner. Let me help encourage and support you through this phase.";
    }
    if (messageWords.some(word => ['career', 'job', 'work', 'professional', 'future'].includes(word))) {
      return "Career planning is exciting! I'm here to help guide your professional development and understand your goals. What direction interests you most?";
    }
    
    return responses[Math.floor(Math.random() * Math.max(responses.length, 1))] || "How can I help with your learning today?";
  }

  generateWorkResponse(messageWords, responses) {
    if (!Array.isArray(messageWords) || messageWords.length === 0) {
      return responses[0] || "Let's work on this step by step. What specific challenge can I help you with?";
    }
    
    // Enhanced technical responses for work mode
    if (messageWords.some(word => ['error', 'bug', 'broken', 'debug', 'issue', 'problem'].includes(word))) {
      return "I see you're facing a bug or error. This is a common challenge when developing. Let me help you debug this systematically and find a solution together.";
    }
    if (messageWords.some(word => ['build', 'create', 'make', 'project', 'develop', 'implement'].includes(word))) {
      return "Great project idea! Let's break this down into actionable tasks: 1. Set up the basic structure, 2. Implement core functionality, 3. Add error handling, 4. Test and refine. I'll guide you through each step.";
    }
    if (messageWords.some(word => ['how', 'implement', 'code', 'function', 'method'].includes(word))) {
      return "I'll help you implement this step by step. Let me walk you through the practical approach and best practices for this type of solution.";
    }
    if (messageWords.some(word => ['critical', 'urgent', 'blocking', 'deployment', 'production'].includes(word))) {
      return "I understand this is critical and blocking your progress. Let's tackle this systematically to get you unblocked quickly. What specific issue are you facing?";
    }
    if (messageWords.some(word => ['complex', 'architecture', 'system', 'design', 'scalability'].includes(word))) {
      return "Complex system architecture is challenging but manageable. Let me help you break down this complex problem into smaller, more manageable components and provide a structured solution approach.";
    }
    
    return responses[Math.floor(Math.random() * responses.length)] || "Let's solve this together. What specific technical challenge can I help with?";
  }

  generatePlanResponse(messageWords, responses) {
    if (!Array.isArray(messageWords) || messageWords.length === 0) {
      return responses[0] || "I'd love to create a structured learning plan for you! What are your goals?";
    }
    
    // Enhanced planning responses
    if (messageWords.some(word => ['plan', 'roadmap', 'learn', 'study', 'curriculum'].includes(word))) {
      if (messageWords.some(word => ['create', 'new', 'make', 'build'])) {
        return "I'd love to create a personalized learning plan for you! To build a structured roadmap, tell me: What do you want to learn? What's your current experience? How much time can you dedicate weekly?";
      }
      return "Based on your goals, I'm creating a structured learning roadmap. This will include core concepts, hands-on projects, clear milestones, and progress tracking to keep you on track.";
    }
    if (messageWords.some(word => ['update', 'progress', 'next', 'continue', 'advance'].includes(word))) {
      return "I've updated your learning plan based on your progress! Here are the next recommended steps to keep you moving forward effectively and efficiently.";
    }
    if (messageWords.some(word => ['time', 'schedule', 'weeks', 'months', 'duration'].includes(word))) {
      return "Let me adjust your plan based on your available time. I'm optimizing it for maximum learning efficiency within your schedule and commitments.";
    }
    if (messageWords.some(word => ['comprehensive', 'detailed', 'complete', 'thorough'].includes(word))) {
      return "Your comprehensive learning plan is now ready! I've structured it to build knowledge progressively while keeping you engaged with practical projects and real-world applications.";
    }
    
    return responses[Math.floor(Math.random() * responses.length)] || "Let me help you create a structured learning path. What's your goal?";
  }

  getAgentName(mode) {
    const names = {
      chat: 'Mentor Steve',
      work: 'Project Partner Steve', 
      plan: 'Learning Path Steve'
    };
    return names[mode] || 'Steve';
  }

  // Test scenarios for each mode
  getTestScenarios() {
    return {
      chat: [
        "I'm feeling overwhelmed with learning programming",
        "What should I focus on as a beginner?",
        "I just completed my first project!",
        "How do I stay motivated when learning gets tough?"
      ],
      work: [
        "I'm getting an error in my React component",
        "Help me build a todo app with authentication", 
        "How do I implement API calls in JavaScript?",
        "My code isn't working, can you help debug it?"
      ],
      plan: [
        "Create a learning plan for full stack development",
        "I want to learn data science in 3 months",
        "Update my current learning progress",
        "Plan a roadmap for becoming a frontend developer"
      ]
    };
  }

  // Generate learning plan mock data
  generateMockLearningPlan(topic, duration = "12 weeks") {
    const plans = {
      "full stack": {
        title: "Full Stack Development Mastery",
        duration: duration,
        overview: "Comprehensive path to becoming a full stack developer",
        phases: [
          { week: "1-3", focus: "Frontend Fundamentals", skills: ["HTML", "CSS", "JavaScript"] },
          { week: "4-6", focus: "React Development", skills: ["React", "State Management", "Hooks"] },
          { week: "7-9", focus: "Backend Basics", skills: ["Node.js", "Express", "Databases"] },
          { week: "10-12", focus: "Full Stack Projects", skills: ["Integration", "Deployment", "Testing"] }
        ]
      },
      "data science": {
        title: "Data Science Fundamentals",
        duration: duration,
        overview: "Essential skills for data analysis and machine learning",
        phases: [
          { week: "1-3", focus: "Python & Statistics", skills: ["Python", "Pandas", "Statistics"] },
          { week: "4-6", focus: "Data Visualization", skills: ["Matplotlib", "Seaborn", "Plotly"] },
          { week: "7-9", focus: "Machine Learning", skills: ["Scikit-learn", "Regression", "Classification"] },
          { week: "10-12", focus: "Real Projects", skills: ["End-to-end Projects", "Deployment"] }
        ]
      }
    };
    
    const key = Object.keys(plans).find(k => topic.toLowerCase().includes(k)) || "full stack";
    return plans[key];
  }
}

// Export singleton instance
export const mockAgent = new MockAgentSimulator(); 