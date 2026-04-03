/**
 * AGENT INTEGRATION TESTS
 * Tests the complete integration between AgentModeSelector, chat system, and mock agents
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import userEvent from '@testing-library/user-event';
import AgentModeSelector from '../components/Chat/AgentModeSelector';
import { mockAgent } from './agentMocks.js';

// Mock a complete chat interface
const MockChatInterface = ({ onMessageSend }) => {
  const [message, setMessage] = React.useState('');
  const [agentMode, setAgentMode] = React.useState('chat');
  const [conversation, setConversation] = React.useState([]);
  const [isLoading, setIsLoading] = React.useState(false);

  const handleModeChange = (newMode) => {
    setAgentMode(newMode);
    mockAgent.setMode(newMode);
  };

  const sendMessage = async () => {
    if (!message.trim()) return;
    
    setIsLoading(true);
    const userMessage = { type: 'user', text: message, timestamp: Date.now() };
    setConversation(prev => [...prev, userMessage]);
    
    try {
      const response = await mockAgent.processMessage(message, agentMode);
      const agentMessage = { 
        type: 'agent', 
        text: response.text, 
        mode: response.mode,
        timestamp: Date.now() 
      };
      setConversation(prev => [...prev, agentMessage]);
      onMessageSend?.(userMessage, agentMessage);
    } catch (error) {
      const errorMessage = { 
        type: 'error', 
        text: 'Failed to get response', 
        timestamp: Date.now() 
      };
      setConversation(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setMessage('');
    }
  };

  return (
    <div data-testid="chat-interface">
      <div data-testid="conversation">
        {conversation.map((msg, index) => (
          <div key={index} data-testid={`message-${msg.type}`}>
            {msg.text}
          </div>
        ))}
      </div>
      
      <div data-testid="chat-input-area">
        <AgentModeSelector
          currentMode={agentMode}
          onModeChange={handleModeChange}
          availableModes={null}
        />
        
        <input
          data-testid="message-input"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type a message..."
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
        />
        
        <button 
          data-testid="send-button"
          onClick={sendMessage}
          disabled={isLoading || !message.trim()}
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

describe('Agent Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAgent.conversationHistory = [];
    mockAgent.setMode('chat');
  });

  describe('Complete Chat Workflow', () => {
    test('should handle complete conversation workflow', async () => {
      const user = userEvent.setup();
      const messageHandler = jest.fn();
      
      render(<MockChatInterface onMessageSend={messageHandler} />);

      // Type and send a message
      const input = screen.getByTestId('message-input');
      const sendButton = screen.getByTestId('send-button');

      await user.type(input, 'Hello, I need help with programming');
      await user.click(sendButton);

      // Wait for response
      await waitFor(() => {
        expect(screen.getByTestId('message-user')).toHaveTextContent('Hello, I need help with programming');
      }, { timeout: 3000 });

      await waitFor(() => {
        expect(screen.getByTestId('message-agent')).toBeInTheDocument();
      }, { timeout: 3000 });

      expect(messageHandler).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'user',
          text: 'Hello, I need help with programming'
        }),
        expect.objectContaining({
          type: 'agent',
          mode: 'chat'
        })
      );
    });

    test('should switch modes during conversation', async () => {
      const user = userEvent.setup();
      
      render(<MockChatInterface />);

      // Start in chat mode
      const modeSelector = screen.getByLabelText('AI mode selector');
      expect(screen.getByText('Mentor')).toBeInTheDocument();

      // Send a message in chat mode
      const input = screen.getByTestId('message-input');
      await user.type(input, 'I need motivation');
      await user.click(screen.getByTestId('send-button'));

      // Wait for response
      await waitFor(() => {
        expect(screen.getByTestId('message-agent')).toBeInTheDocument();
      }, { timeout: 3000 });

      // Switch to work mode
      await user.click(modeSelector);
      await waitFor(() => {
        const workOptions = screen.getAllByText('Project Partner');
        const dropdownOption = workOptions.find(el => el.className === 'optionName');
        expect(dropdownOption).toBeInTheDocument();
      });

      const workOptions = screen.getAllByText('Project Partner');
      const dropdownOption = workOptions.find(el => el.className === 'optionName');
      await user.click(dropdownOption.closest('button'));

      // Verify mode changed
      await waitFor(() => {
        expect(screen.getByText('Project Partner')).toBeInTheDocument();
      });

      // Send message in work mode
      await user.type(input, 'Help me debug this code');
      await user.click(screen.getByTestId('send-button'));

      // Verify response is in work mode
      await waitFor(() => {
        const messages = screen.getAllByTestId('message-agent');
        expect(messages).toHaveLength(2);
      }, { timeout: 3000 });
    });

    test('should handle rapid mode switching', async () => {
      const user = userEvent.setup();
      
      render(<MockChatInterface />);

      const modeSelector = screen.getByLabelText('AI mode selector');
      const modes = ['chat', 'work', 'plan'];
      const expectedTexts = ['Mentor', 'Project Partner', 'Learning Path'];

      // Rapidly switch modes
      for (let i = 0; i < 5; i++) {
        const targetMode = modes[i % 3];
        const expectedText = expectedTexts[i % 3];

        await user.click(modeSelector);
        
        // Find the correct option based on the expected text
        await waitFor(() => {
          const options = screen.getAllByText(expectedText);
          const dropdownOption = options.find(el => el.className === 'optionName');
          expect(dropdownOption).toBeInTheDocument();
        });

        const options = screen.getAllByText(expectedText);
        const dropdownOption = options.find(el => el.className === 'optionName');
        await user.click(dropdownOption.closest('button'));

        // Verify mode changed
        await waitFor(() => {
          expect(screen.getByText(expectedText)).toBeInTheDocument();
        });
      }
    });
  });

  describe('Error Handling Integration', () => {
    test('should handle agent errors gracefully', async () => {
      const user = userEvent.setup();
      
      // Mock agent to throw error
      const originalProcess = mockAgent.processMessage;
      mockAgent.processMessage = jest.fn().mockRejectedValue(new Error('Mock error'));

      render(<MockChatInterface />);

      const input = screen.getByTestId('message-input');
      await user.type(input, 'This should cause an error');
      await user.click(screen.getByTestId('send-button'));

      // Should show error message
      await waitFor(() => {
        expect(screen.getByTestId('message-error')).toBeInTheDocument();
      }, { timeout: 3000 });

      // Restore original function
      mockAgent.processMessage = originalProcess;
    });

    test('should handle empty messages', async () => {
      const user = userEvent.setup();
      
      render(<MockChatInterface />);

      const sendButton = screen.getByTestId('send-button');
      
      // Button should be disabled for empty message
      expect(sendButton).toBeDisabled();

      // Type spaces only
      const input = screen.getByTestId('message-input');
      await user.type(input, '   ');
      
      // Button should still be disabled
      expect(sendButton).toBeDisabled();
    });

    test('should prevent double submission', async () => {
      const user = userEvent.setup();
      
      render(<MockChatInterface />);

      const input = screen.getByTestId('message-input');
      const sendButton = screen.getByTestId('send-button');

      await user.type(input, 'Test message');
      
      // Click send button multiple times rapidly
      await user.click(sendButton);
      await user.click(sendButton);
      await user.click(sendButton);

      // Should only send one message
      await waitFor(() => {
        const userMessages = screen.getAllByTestId('message-user');
        expect(userMessages).toHaveLength(1);
      });
    });
  });

  describe('Performance Integration', () => {
    test('should handle multiple rapid messages', async () => {
      const user = userEvent.setup();
      
      render(<MockChatInterface />);

      const input = screen.getByTestId('message-input');
      const sendButton = screen.getByTestId('send-button');

      // Send multiple messages rapidly
      const messages = ['Message 1', 'Message 2', 'Message 3'];
      
      for (const message of messages) {
        await user.clear(input);
        await user.type(input, message);
        await user.click(sendButton);
        
        // Wait a bit between messages
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Wait for all responses
      await waitFor(() => {
        const userMessages = screen.getAllByTestId('message-user');
        expect(userMessages).toHaveLength(3);
      }, { timeout: 10000 });

      await waitFor(() => {
        const agentMessages = screen.getAllByTestId('message-agent');
        expect(agentMessages).toHaveLength(3);
      }, { timeout: 10000 });
    });

    test('should maintain performance with long conversation', async () => {
      const user = userEvent.setup();
      
      render(<MockChatInterface />);

      const input = screen.getByTestId('message-input');
      const sendButton = screen.getByTestId('send-button');

      // Create a longer conversation
      for (let i = 0; i < 10; i++) {
        await user.clear(input);
        await user.type(input, `Performance test message ${i}`);
        await user.click(sendButton);
        
        // Wait for response before sending next
        await waitFor(() => {
          const agentMessages = screen.getAllByTestId('message-agent');
          expect(agentMessages).toHaveLength(i + 1);
        }, { timeout: 5000 });
      }

      // Verify all messages are present
      const userMessages = screen.getAllByTestId('message-user');
      const agentMessages = screen.getAllByTestId('message-agent');
      
      expect(userMessages).toHaveLength(10);
      expect(agentMessages).toHaveLength(10);
    });
  });

  describe('Accessibility Integration', () => {
    test('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      
      render(<MockChatInterface />);

      const input = screen.getByTestId('message-input');
      
      // Type message and press Enter
      await user.type(input, 'Test keyboard navigation');
      await user.keyboard('{Enter}');

      // Should send message
      await waitFor(() => {
        expect(screen.getByTestId('message-user')).toBeInTheDocument();
      });
    });

    test('should maintain focus management', async () => {
      const user = userEvent.setup();
      
      render(<MockChatInterface />);

      const input = screen.getByTestId('message-input');
      const modeSelector = screen.getByLabelText('AI mode selector');

      // Focus input
      await user.click(input);
      expect(input).toHaveFocus();

      // Click mode selector
      await user.click(modeSelector);
      
      // Should be able to navigate back to input
      await user.tab();
      expect(input).toHaveFocus();
    });
  });

  describe('Real-world Scenarios', () => {
    test('should handle learning workflow scenario', async () => {
      const user = userEvent.setup();
      
      render(<MockChatInterface />);

      const input = screen.getByTestId('message-input');
      const modeSelector = screen.getByLabelText('AI mode selector');

      // 1. Start with planning
      await user.click(modeSelector);
      const planOptions = screen.getAllByText('Learning Path');
      const planDropdownOption = planOptions.find(el => el.className === 'optionName');
      await user.click(planDropdownOption.closest('button'));

      await user.type(input, 'Create a learning plan for React development');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByTestId('message-agent')).toBeInTheDocument();
      }, { timeout: 3000 });

      // 2. Switch to work mode for implementation
      await user.click(modeSelector);
      const workOptions = screen.getAllByText('Project Partner');
      const workDropdownOption = workOptions.find(el => el.className === 'optionName');
      await user.click(workDropdownOption.closest('button'));

      await user.clear(input);
      await user.type(input, 'Help me implement my first React component');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        const agentMessages = screen.getAllByTestId('message-agent');
        expect(agentMessages).toHaveLength(2);
      }, { timeout: 3000 });

      // 3. Switch to chat mode for support
      await user.click(modeSelector);
      const chatOptions = screen.getAllByText('Mentor');
      const chatDropdownOption = chatOptions.find(el => el.className === 'optionName');
      await user.click(chatDropdownOption.closest('button'));

      await user.clear(input);
      await user.type(input, 'I am struggling with understanding React concepts');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        const agentMessages = screen.getAllByTestId('message-agent');
        expect(agentMessages).toHaveLength(3);
      }, { timeout: 3000 });

      // Verify we have the complete workflow
      const userMessages = screen.getAllByTestId('message-user');
      expect(userMessages).toHaveLength(3);
      expect(userMessages[0]).toHaveTextContent('Create a learning plan for React development');
      expect(userMessages[1]).toHaveTextContent('Help me implement my first React component');
      expect(userMessages[2]).toHaveTextContent('I am struggling with understanding React concepts');
    });

    test('should handle debugging workflow', async () => {
      const user = userEvent.setup();
      
      render(<MockChatInterface />);

      const input = screen.getByTestId('message-input');
      const modeSelector = screen.getByLabelText('AI mode selector');

      // Switch to work mode for debugging
      await user.click(modeSelector);
      const workOptions = screen.getAllByText('Project Partner');
      const workDropdownOption = workOptions.find(el => el.className === 'optionName');
      await user.click(workDropdownOption.closest('button'));

      // Send debugging request
      await user.type(input, 'I have a bug in my JavaScript code, can you help?');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        const agentMessages = screen.getAllByTestId('message-agent');
        expect(agentMessages).toHaveLength(1);
        expect(agentMessages[0]).toBeInTheDocument();
      }, { timeout: 3000 });

      // Follow up with more specific question
      await user.clear(input);
      await user.type(input, 'The error says "Cannot read property of undefined"');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        const agentMessages = screen.getAllByTestId('message-agent');
        expect(agentMessages).toHaveLength(2);
      }, { timeout: 3000 });
    });
  });
});

export default describe; 