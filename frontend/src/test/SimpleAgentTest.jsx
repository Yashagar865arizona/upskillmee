import React, { useState } from 'react';
import { mockAgent } from './agentMocks';
import AgentModeSelector from '../components/Chat/AgentModeSelector';

const SimpleAgentTest = () => {
  const [agentMode, setAgentMode] = useState('chat');
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleModeChange = (newMode) => {
    setAgentMode(newMode);
    mockAgent.setMode(newMode);
    console.log('Mode changed to:', newMode);
  };

  const sendMessage = async () => {
    if (!message.trim()) return;
    
    setIsLoading(true);
    try {
      const result = await mockAgent.processMessage(message, agentMode);
      setResponse(result.text);
      console.log('Response received:', result);
    } catch (error) {
      console.error('Error:', error);
      setResponse('Error processing message');
    } finally {
      setIsLoading(false);
    }
  };

  const testScenarios = mockAgent.getTestScenarios();

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>🧪 Simple Agent Test</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <h3>Mode Selector Test</h3>
        <AgentModeSelector
          currentMode={agentMode}
          onModeChange={handleModeChange}
          availableModes={null}
        />
        <p>Current mode: <strong>{agentMode}</strong></p>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Message Test</h3>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type a message..."
          style={{ width: '300px', padding: '8px', marginRight: '10px' }}
        />
        <button onClick={sendMessage} disabled={isLoading}>
          {isLoading ? 'Processing...' : 'Send'}
        </button>
      </div>

      {response && (
        <div style={{ marginBottom: '20px', padding: '10px', background: '#f5f5f5', borderRadius: '8px' }}>
          <h4>Response:</h4>
          <p>{response}</p>
        </div>
      )}

      <div>
        <h3>Quick Test Scenarios</h3>
        {Object.entries(testScenarios).map(([mode, scenarios]) => (
          <div key={mode} style={{ marginBottom: '15px' }}>
            <h4>{mode.toUpperCase()} Mode Scenarios:</h4>
            {scenarios.map((scenario, index) => (
              <button
                key={index}
                onClick={() => setMessage(scenario)}
                style={{
                  display: 'block',
                  margin: '5px 0',
                  padding: '5px 10px',
                  background: '#e0e0e0',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  textAlign: 'left',
                  width: '100%'
                }}
              >
                {scenario}
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export default SimpleAgentTest; 