/**
 * Simple integration test for chat enhancements
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import MainChat from '../MainChat';

// Mock the contexts
const mockAuthContext = {
  user: { id: 'user-123', name: 'Test User' },
  token: 'mock-token',
  isAuthenticated: true
};

const mockTaskContext = {
  updateCurrentPlan: jest.fn()
};

// Mock the context providers
jest.mock('../../../context/AuthContext', () => ({
  useAuth: () => mockAuthContext
}));

jest.mock('../../../context/TaskContext', () => ({
  useTasks: () => mockTaskContext
}));

// Mock websocket service
jest.mock('../../../services/websocketService', () => ({
  connect: jest.fn(),
  disconnect: jest.fn(),
  sendMessage: jest.fn(),
  sendTypingIndicator: jest.fn(),
  sendMessageStatus: jest.fn(),
  on: jest.fn(),
  off: jest.fn(),
  getStatus: () => ({
    isConnected: false,
    isConnecting: false,
    reconnectAttempts: 0,
    queuedMessages: 0
  })
}));

describe('Chat Enhancements', () => {
  test('renders enhanced chat interface', () => {
    render(<MainChat />);
    
    // Check for main chat elements
    expect(screen.getByText('Welcome to Ponder AI')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/connecting/i)).toBeInTheDocument();
    // Check for send button (it's disabled when not connected, but should exist)
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
  });

  test('renders message thread component', () => {
    render(<MainChat />);
    
    // Check for conversation thread
    expect(screen.getByText('Conversations')).toBeInTheDocument();
  });

  test('renders connection status', () => {
    render(<MainChat />);
    
    // Check for connection status (should show connecting initially)
    expect(screen.getByText(/connecting/i)).toBeInTheDocument();
  });

  test('renders agent mode selector', () => {
    render(<MainChat />);
    
    // Check for agent mode selector
    expect(screen.getByText('Mentor')).toBeInTheDocument();
  });

  test('renders file upload button', () => {
    render(<MainChat />);
    
    // Check for file upload button
    const attachButton = screen.getByTitle('Attach files');
    expect(attachButton).toBeInTheDocument();
  });
});