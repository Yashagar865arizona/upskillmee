import React, { useState, useRef, useEffect } from 'react';
import { mockAgent } from './agentMocks';
import AgentModeSelector from '../components/Chat/AgentModeSelector';
import './AgentTestHarness.css';

const AgentTestHarness = () => {
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [agentMode, setAgentMode] = useState('chat');
  const [isProcessing, setIsProcessing] = useState(false);
  const [testResults, setTestResults] = useState({});
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Update mock agent mode when selector changes
    mockAgent.setMode(agentMode);
  }, [agentMode]);

  const sendMessage = async (message) => {
    if (!message.trim()) return;

    // Add user message
    const userMessage = {
      id: Date.now(),
      text: message,
      sender: 'user',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsProcessing(true);

    try {
      // Process with mock agent
      const response = await mockAgent.processMessage(message, agentMode);
      
      // Add bot response
      const botMessage = {
        id: Date.now() + 1,
        text: response.text,
        sender: 'bot',
        mode: response.mode,
        timestamp: new Date(),
        agentName: response.agent_info.agent_name
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error processing message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Error processing message',
        sender: 'bot',
        isError: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  };

  const runTestScenario = async (scenarios, mode) => {
    setTestResults(prev => ({ ...prev, [mode]: { running: true, results: [] } }));
    
    for (const scenario of scenarios) {
      try {
        const response = await mockAgent.processMessage(scenario, mode);
        const result = {
          input: scenario,
          output: response.text,
          mode: response.mode,
          success: true,
          timestamp: new Date()
        };
        
        setTestResults(prev => ({
          ...prev,
          [mode]: {
            ...prev[mode],
            results: [...(prev[mode]?.results || []), result]
          }
        }));
        
        // Small delay between tests
        await new Promise(resolve => setTimeout(resolve, 500));
      } catch (error) {
        const result = {
          input: scenario,
          output: `Error: ${error.message}`,
          mode: mode,
          success: false,
          timestamp: new Date()
        };
        
        setTestResults(prev => ({
          ...prev,
          [mode]: {
            ...prev[mode],
            results: [...(prev[mode]?.results || []), result]
          }
        }));
      }
    }
    
    setTestResults(prev => ({ ...prev, [mode]: { ...prev[mode], running: false } }));
  };

  const runAllTests = async () => {
    const scenarios = mockAgent.getTestScenarios();
    
    for (const [mode, modeScenarios] of Object.entries(scenarios)) {
      await runTestScenario(modeScenarios, mode);
    }
  };

  const clearMessages = () => {
    setMessages([]);
    mockAgent.conversationHistory = [];
  };

  const clearTestResults = () => {
    setTestResults({});
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(currentMessage);
  };

  const sendPredefinedMessage = (message) => {
    sendMessage(message);
  };

  const scenarios = mockAgent.getTestScenarios();

  return (
    <div className="agent-test-harness">
      <div className="test-header">
        <h1>🧪 Agent Testing Lab</h1>
        <p>Test all agent modes without API costs!</p>
        
        <div className="test-controls">
          <button onClick={runAllTests} className="run-all-btn">
            🚀 Run All Tests
          </button>
          <button onClick={clearMessages} className="clear-btn">
            🗑️ Clear Chat
          </button>
          <button onClick={clearTestResults} className="clear-results-btn">
            📊 Clear Results
          </button>
        </div>
      </div>

      <div className="test-layout">
        {/* Chat Interface */}
        <div className="chat-section">
          <div className="chat-header">
            <h3>💬 Interactive Chat</h3>
            <AgentModeSelector
              currentMode={agentMode}
              onModeChange={setAgentMode}
              availableModes={null}
            />
          </div>

          <div className="messages-container">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'} ${message.isError ? 'error-message' : ''}`}
              >
                <div className="message-content">
                  <div className="message-header">
                    <span className="sender">
                      {message.sender === 'user' ? '👤 You' : `🤖 ${message.agentName || 'Agent'}`}
                    </span>
                    {message.mode && (
                      <span className={`mode-badge mode-${message.mode}`}>
                        {message.mode}
                      </span>
                    )}
                    <span className="timestamp">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="message-text">
                    {message.text.split('\n').map((line, index) => (
                      <div key={index}>{line}</div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
            {isProcessing && (
              <div className="message bot-message">
                <div className="message-content">
                  <div className="typing-indicator">
                    <span>🤖 Agent is thinking</span>
                    <div className="dots">
                      <span>.</span><span>.</span><span>.</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="message-form">
            <input
              type="text"
              value={currentMessage}
              onChange={(e) => setCurrentMessage(e.target.value)}
              placeholder={`Message ${agentMode} agent...`}
              className="message-input"
              disabled={isProcessing}
            />
            <button type="submit" disabled={isProcessing} className="send-btn">
              Send
            </button>
          </form>
        </div>

        {/* Test Scenarios */}
        <div className="scenarios-section">
          <h3>🎯 Quick Test Scenarios</h3>
          
          {Object.entries(scenarios).map(([mode, modeScenarios]) => (
            <div key={mode} className="mode-scenarios">
              <h4 className={`mode-title mode-${mode}`}>
                {mode === 'chat' ? '💬 Mentor' : mode === 'work' ? '🔧 Project Partner' : '📋 Learning Path'} Mode
              </h4>
              <div className="scenario-buttons">
                {modeScenarios.map((scenario, index) => (
                  <button
                    key={index}
                    onClick={() => sendPredefinedMessage(scenario)}
                    className="scenario-btn"
                    disabled={isProcessing}
                  >
                    {scenario}
                  </button>
                ))}
              </div>
              
              {/* Individual mode test runner */}
              <button
                onClick={() => runTestScenario(modeScenarios, mode)}
                className="test-mode-btn"
                disabled={testResults[mode]?.running}
              >
                {testResults[mode]?.running ? '⏳ Testing...' : `🧪 Test ${mode} Mode`}
              </button>
            </div>
          ))}
        </div>

        {/* Test Results */}
        {Object.keys(testResults).length > 0 && (
          <div className="results-section">
            <h3>📊 Test Results</h3>
            
            {Object.entries(testResults).map(([mode, data]) => (
              <div key={mode} className="mode-results">
                <h4 className={`mode-title mode-${mode}`}>
                  {mode.toUpperCase()} Mode Results
                  {data.running && <span className="running-indicator">⏳</span>}
                </h4>
                
                {data.results && data.results.length > 0 && (
                  <div className="test-cases">
                    {data.results.map((result, index) => (
                      <div key={index} className={`test-case ${result.success ? 'success' : 'failure'}`}>
                        <div className="test-input">
                          <strong>Input:</strong> {result.input}
                        </div>
                        <div className="test-output">
                          <strong>Output:</strong> {result.output.substring(0, 200)}
                          {result.output.length > 200 && '...'}
                        </div>
                        <div className="test-meta">
                          <span className={`status ${result.success ? 'success' : 'failure'}`}>
                            {result.success ? '✅ Success' : '❌ Failed'}
                          </span>
                          <span className="mode-used">Mode: {result.mode}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentTestHarness; 