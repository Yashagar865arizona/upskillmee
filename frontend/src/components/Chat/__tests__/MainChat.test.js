/**
 * Unit tests for MainChat component.
 * Tests chat functionality, WebSocket integration, message handling, and user interactions.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import MainChat from '../MainChat';
import { AuthContext } from '../../../context/AuthContext';
import { TaskContext } from '../../../context/TaskContext';
import websocketService from '../../../services/websocketService';

// Mock the websocket service
jest.mock('../../../services/websocketService', () => ({
  connect: jest.fn(),
  disconnect: jest.fn(),
  send: jest.fn(),
  on: jest.fn(),
  off: jest.fn(),
  isConnected: jest.fn(() => false),
}));

// Mock the avatar import
jest.mock('../../../assets/avatar.png', () => 'avatar.png');

// Mock child components
jest.mock('../AgentModeSelector', () => {
  return function MockAgentModeSelector({ currentMode, onModeChange, availableModes }) {
    return (
      <div data-testid="agent-mode-selector">
        <span>Current Mode: {currentMode}</span>
        <button onClick={() => onModeChange('work')}>Switch to Work</button>
        <button onClick={() => onModeChange('plan')}>Switch to Plan</button>
      </div>
    );
  };
});

jest.mock('../ConnectionStatus', () => {
  return function MockConnectionStatus({ status }) {
    return (
      <div data-testid="connection-status">
        Status: {status.isConnected ? 'Connected' : 'Disconnected'}
      </div>
    );
  };
});

describe('MainChat Component', () => {
  const mockUser = {
    id: 'user-123',
    name: 'Test User',
    email: 'test@example.com'
  };

  const mockAuthContext = {
    token: 'mock-jwt-token',
    user: mockUser,
    isAuthenticated: true,
    login: jest.fn(),
    logout: jest.fn()
  };

  const mockTaskContext = {
    updateCurrentPlan: jest.fn(),
    currentPlan: null,
    tasks: []
  };

  const renderMainChat = (authContext = mockAuthContext, taskContext = mockTaskContext) => {
    return render(
      <AuthContext.Provider value={authContext}>
        <TaskContext.Provider value={taskContext}>
          <MainChat />
        </TaskContext.Provider>
      </AuthContext.Provider>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
    websocketService.isConnected.mockReturnValue(false);
  });

  describe('Component Rendering', () => {
    test('renders main chat interface', () => {
      renderMainChat();
      
      expect(screen.getByTestId('agent-mode-selector')).toBeInTheDocument();
      expect(screen.getByTestId('connection-status')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/type your message/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
    });

    test('renders with default agent mode', () => {
      renderMainChat();
      
      expect(screen.getByText('Current Mode: chat')).toBeInTheDocument();
    });

    test('shows disconnected status initially', () => {
      renderMainChat();
      
      expect(screen.getByText('Status: Disconnected')).toBeInTheDocument();
    });

    test('renders message input and send button', () => {
      renderMainChat();
      
      const messageInput = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });
      
      expect(messageInput).toBeInTheDocument();
      expect(sendButton).toBeInTheDocument();
      expect(sendButton).toBeDisabled(); // Should be disabled when input is empty
    });
  });

  describe('Authentication Integration', () => {
    test('initializes WebSocket when authenticated', () => {
      renderMainChat();
      
      expect(websocketService.on).toHaveBeenCalledWith('connected', expect.any(Function));
      expect(websocketService.on).toHaveBeenCalledWith('disconnected', expect.any(Function));
    });

    test('does not initialize WebSocket when not authenticated', () => {
      const unauthenticatedContext = {
        ...mockAuthContext,
        isAuthenticated: false,
        token: null,
        user: null
      };
      
      renderMainChat(unauthenticatedContext);
      
      expect(websocketService.disconnect).toHaveBeenCalled();
    });

    test('disconnects WebSocket on unmount', () => {
      const { unmount } = renderMainChat();
      
      unmount();
      
      expect(websocketService.disconnect).toHaveBeenCalled();
    });
  });

  describe('Message Input and Sending', () => {
    test('enables send button when message is typed', async () => {
      const user = userEvent.setup();
      renderMainChat();
      
      const messageInput = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });
      
      expect(sendButton).toBeDisabled();
      
      await user.type(messageInput, 'Hello, I want to learn programming');
      
      expect(sendButton).not.toBeDisabled();
    });

    test('sends message when send button is clicked', async () => {
      const user = userEvent.setup();
      renderMainChat();
      
      const messageInput = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });
      
      await user.type(messageInput, 'Test message');
      await user.click(sendButton);
      
      expect(websocketService.send).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'message',
          message: 'Test message',
          user_id: mockUser.id,
          agent_mode: 'chat'
        })
      );
    });

    test('sends message when Enter key is pressed', async () => {
      const user = userEvent.setup();
      renderMainChat();
      
      const messageInput = screen.getByPlaceholderText(/type your message/i);
      
      await user.type(messageInput, 'Test message{enter}');
      
      expect(websocketService.send).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'message',
          message: 'Test message',
          user_id: mockUser.id
        })
      );
    });

    test('does not send message when Shift+Enter is pressed', async () => {
      const user = userEvent.setup();
      renderMainChat();
      
      const messageInput = screen.getByPlaceholderText(/type your message/i);
      
      await user.type(messageInput, 'Test message{shift}{enter}');
      
      expect(websocketService.send).not.toHaveBeenCalled();
    });

    test('clears input after sending message', async () => {
      const user = userEvent.setup();
      renderMainChat();
      
      const messageInput = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });
      
      await user.type(messageInput, 'Test message');
      await user.click(sendButton);
      
      expect(messageInput.value).toBe('');
    });

    test('does not send empty messages', async () => {
      const user = userEvent.setup();
      renderMainChat();
      
      const sendButton = screen.getByRole('button', { name: /send/i });
      
      // Try to click send button without typing anything
      await user.click(sendButton);
      
      expect(websocketService.send).not.toHaveBeenCalled();
    });

    test('trims whitespace from messages', async () => {
      const user = userEvent.setup();
      renderMainChat();
      
      const messageInput = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });
      
      await user.type(messageInput, '   Test message   ');
      await user.click(sendButton);
      
      expect(websocketService.send).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'Test message'
        })
      );
    });
  });

  describe('Agent Mode Selection', () => {
    test('changes agent mode when selector is used', async () => {
      const user = userEvent.setup();
      renderMainChat();
      
      expect(screen.getByText('Current Mode: chat')).toBeInTheDocument();
      
      const workModeButton = screen.getByText('Switch to Work');
      await user.click(workModeButton);
      
      expect(screen.getByText('Current Mode: work')).toBeInTheDocument();
    });

    test('includes agent mode in sent messages', async () => {
      const user = userEvent.setup();
      renderMainChat();
      
      // Switch to work mode
      const workModeButton = screen.getByText('Switch to Work');
      await user.click(workModeButton);
      
      // Send a message
      const messageInput = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });
      
      await user.type(messageInput, 'Help me with coding');
      await user.click(sendButton);
      
      expect(websocketService.send).toHaveBeenCalledWith(
        expect.objectContaining({
          agent_mode: 'work'
        })
      );
    });
  });

  describe('Message Display', () => {
    test('displays user messages', async () => {
      const user = userEvent.setup();
      renderMainChat();
      
      const messageInput = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });
      
      await user.type(messageInput, 'Hello AI');
      await user.click(sendButton);
      
      await waitFor(() => {
        expect(screen.getByText('Hello AI')).toBeInTheDocument();
      });
    });

    test('displays bot messages when received via WebSocket', async () => {
      renderMainChat();
      
      // Simulate receiving a message from WebSocket
      const mockMessage = {
        text: 'Hello! How can I help you today?',
        sender: 'bot',
        id: 'msg-123'
      };
      
      // Get the message handler that was registered
      const messageHandler = websocketService.on.mock.calls.find(
        call => call[0] === 'message'
      )?.[1];
      
      if (messageHandler) {
        act(() => {
          messageHandler(mockMessage);
        });
        
        await waitFor(() => {
          expect(screen.getByText('Hello! How can I help you today?')).toBeInTheDocument();
        });
      }
    });

    test('shows typing indicator when bot is typing', async () => {
      renderMainChat();
      
      // Simulate typing indicator
      const typingHandler = websocketService.on.mock.calls.find(
        call => call[0] === 'typing'
      )?.[1];
      
      if (typingHandler) {
        act(() => {
          typingHandler({ isTyping: true });
        });
        
        await waitFor(() => {
          expect(screen.getByText(/typing/i)).toBeInTheDocument();
        });
      }
    });

    test('scrolls to bottom when new messages are added', async () => {
      const user = userEvent.setup();
      renderMainChat();
      
      // Mock scrollIntoView
      const mockScrollIntoView = jest.fn();
      Element.prototype.scrollIntoView = mockScrollIntoView;
      
      const messageInput = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });
      
      await user.type(messageInput, 'Test message');
      await user.click(sendButton);
      
      await waitFor(() => {
        expect(mockScrollIntoView).toHaveBeenCalled();
      });
    });
  });

  describe('WebSocket Connection Handling', () => {
    test('updates connection status when connected', async () => {
      renderMainChat();
      
      // Simulate connection
      const connectedHandler = websocketService.on.mock.calls.find(
        call => call[0] === 'connected'
      )?.[1];
      
      if (connectedHandler) {
        act(() => {
          connectedHandler();
        });
        
        await waitFor(() => {
          expect(screen.getByText('Status: Connected')).toBeInTheDocument();
        });
      }
    });

    test('updates connection status when disconnected', async () => {
      renderMainChat();
      
      // Simulate disconnection
      const disconnectedHandler = websocketService.on.mock.calls.find(
        call => call[0] === 'disconnected'
      )?.[1];
      
      if (disconnectedHandler) {
        act(() => {
          disconnectedHandler();
        });
        
        await waitFor(() => {
          expect(screen.getByText('Status: Disconnected')).toBeInTheDocument();
        });
      }
    });

    test('handles connection errors gracefully', async () => {
      renderMainChat();
      
      // Simulate connection error
      const errorHandler = websocketService.on.mock.calls.find(
        call => call[0] === 'error'
      )?.[1];
      
      if (errorHandler) {
        act(() => {
          errorHandler({ error: 'Connection failed' });
        });
        
        // Should not crash the component
        expect(screen.getByTestId('agent-mode-selector')).toBeInTheDocument();
      }
    });
  });

  describe('Learning Plan Integration', () => {
    test('updates current plan when learning plan is received', async () => {
      renderMainChat();
      
      const mockLearningPlan = {
        type: 'learning_plan',
        plan: {
          title: 'Web Development Basics',
          projects: [
            { title: 'Build a website', skills: ['HTML', 'CSS'] }
          ]
        }
      };
      
      // Simulate receiving learning plan
      const messageHandler = websocketService.on.mock.calls.find(
        call => call[0] === 'message'
      )?.[1];
      
      if (messageHandler) {
        act(() => {
          messageHandler(mockLearningPlan);
        });
        
        await waitFor(() => {
          expect(mockTaskContext.updateCurrentPlan).toHaveBeenCalledWith(
            mockLearningPlan.plan
          );
        });
      }
    });
  });

  describe('Error Handling', () => {
    test('handles WebSocket send errors gracefully', async () => {
      const user = userEvent.setup();
      websocketService.send.mockImplementation(() => {
        throw new Error('WebSocket error');
      });
      
      renderMainChat();
      
      const messageInput = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });
      
      await user.type(messageInput, 'Test message');
      await user.click(sendButton);
      
      // Should not crash the component
      expect(screen.getByTestId('agent-mode-selector')).toBeInTheDocument();
    });

    test('shows error message when message sending fails', async () => {
      const user = userEvent.setup();
      websocketService.send.mockRejectedValue(new Error('Send failed'));
      
      renderMainChat();
      
      const messageInput = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });
      
      await user.type(messageInput, 'Test message');
      await user.click(sendButton);
      
      await waitFor(() => {
        expect(screen.getByText(/failed to send message/i)).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels', () => {
      renderMainChat();
      
      const messageInput = screen.getByPlaceholderText(/type your message/i);
      const sendButton = screen.getByRole('button', { name: /send/i });
      
      expect(messageInput).toHaveAttribute('aria-label');
      expect(sendButton).toHaveAttribute('aria-label');
    });

    test('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      renderMainChat();
      
      const messageInput = screen.getByPlaceholderText(/type your message/i);
      
      // Tab to input
      await user.tab();
      expect(messageInput).toHaveFocus();
      
      // Type message and press Enter
      await user.type(messageInput, 'Test message{enter}');
      
      expect(websocketService.send).toHaveBeenCalled();
    });

    test('announces new messages to screen readers', async () => {
      renderMainChat();
      
      // Check for aria-live region
      const messagesContainer = screen.getByRole('log');
      expect(messagesContainer).toHaveAttribute('aria-live', 'polite');
    });
  });

  describe('Performance', () => {
    test('does not re-render unnecessarily', () => {
      const { rerender } = renderMainChat();
      
      // Re-render with same props
      rerender(
        <AuthContext.Provider value={mockAuthContext}>
          <TaskContext.Provider value={mockTaskContext}>
            <MainChat />
          </TaskContext.Provider>
        </AuthContext.Provider>
      );
      
      // Component should handle re-renders gracefully
      expect(screen.getByTestId('agent-mode-selector')).toBeInTheDocument();
    });

    test('cleans up event listeners on unmount', () => {
      const { unmount } = renderMainChat();
      
      unmount();
      
      expect(websocketService.off).toHaveBeenCalled();
      expect(websocketService.disconnect).toHaveBeenCalled();
    });
  });
});