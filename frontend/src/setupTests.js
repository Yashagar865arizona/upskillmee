/**
 * Test setup configuration for React Testing Library and Jest.
 * This file is automatically loaded by Create React App before running tests.
 */

import '@testing-library/jest-dom';
import React from 'react';

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock scrollIntoView
Element.prototype.scrollIntoView = jest.fn();

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.sessionStorage = sessionStorageMock;

// Mock console methods to reduce noise in tests
const originalError = console.error;
const originalWarn = console.warn;

beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };

  console.warn = (...args) => {
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('componentWillReceiveProps') ||
       args[0].includes('componentWillUpdate'))
    ) {
      return;
    }
    originalWarn.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
  console.warn = originalWarn;
});

// Mock fetch for API tests
global.fetch = jest.fn();

// Mock WebSocket
global.WebSocket = class WebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) this.onopen();
    }, 0);
  }

  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  send = jest.fn();
  close = jest.fn();
  addEventListener = jest.fn();
  removeEventListener = jest.fn();
};

// Mock URL.createObjectURL
global.URL.createObjectURL = jest.fn(() => 'mocked-url');
global.URL.revokeObjectURL = jest.fn();

// Mock File and FileReader
global.File = class File {
  constructor(chunks, filename, options = {}) {
    this.chunks = chunks;
    this.name = filename;
    this.size = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
    this.type = options.type || '';
    this.lastModified = options.lastModified || Date.now();
  }
};

global.FileReader = class FileReader {
  constructor() {
    this.readyState = 0;
    this.result = null;
    this.error = null;
  }

  readAsText = jest.fn(function() {
    this.readyState = 2;
    this.result = 'mocked file content';
    if (this.onload) this.onload();
  });

  readAsDataURL = jest.fn(function() {
    this.readyState = 2;
    this.result = 'data:text/plain;base64,bW9ja2VkIGZpbGUgY29udGVudA==';
    if (this.onload) this.onload();
  });
};

// Mock canvas context for chart.js
HTMLCanvasElement.prototype.getContext = jest.fn(() => ({
  fillRect: jest.fn(),
  clearRect: jest.fn(),
  getImageData: jest.fn(() => ({ data: new Array(4) })),
  putImageData: jest.fn(),
  createImageData: jest.fn(() => []),
  setTransform: jest.fn(),
  drawImage: jest.fn(),
  save: jest.fn(),
  fillText: jest.fn(),
  restore: jest.fn(),
  beginPath: jest.fn(),
  moveTo: jest.fn(),
  lineTo: jest.fn(),
  closePath: jest.fn(),
  stroke: jest.fn(),
  translate: jest.fn(),
  scale: jest.fn(),
  rotate: jest.fn(),
  arc: jest.fn(),
  fill: jest.fn(),
  measureText: jest.fn(() => ({ width: 0 })),
  transform: jest.fn(),
  rect: jest.fn(),
  clip: jest.fn(),
}));

// Mock CSS modules
const mockCSSModules = new Proxy({}, {
  get: function(target, property) {
    return property;
  }
});

// Mock all CSS module imports
jest.mock('*.module.css', () => mockCSSModules);
jest.mock('*.module.scss', () => mockCSSModules);

// Mock static asset imports
const mockAsset = 'test-file-stub';

// Create module name mapper for static assets
const assetExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.mp3', '.mp4'];
assetExtensions.forEach(ext => {
  jest.doMock(`*${ext}`, () => mockAsset, { virtual: true });
});

// Global test utilities
global.testUtils = {
  // Helper to create mock user
  createMockUser: (overrides = {}) => ({
    id: 'user-123',
    name: 'Test User',
    email: 'test@example.com',
    ...overrides
  }),

  // Helper to create mock auth context
  createMockAuthContext: (overrides = {}) => ({
    user: global.testUtils.createMockUser(),
    token: 'mock-jwt-token',
    isAuthenticated: true,
    login: jest.fn(),
    logout: jest.fn(),
    ...overrides
  }),

  // Helper to create mock project
  createMockProject: (overrides = {}) => ({
    id: 'project-123',
    title: 'Test Project',
    description: 'Test project description',
    status: 'in_progress',
    completion_percentage: 50,
    created_at: '2024-01-15T10:00:00Z',
    ...overrides
  }),

  // Helper to create mock learning plan
  createMockLearningPlan: (overrides = {}) => ({
    id: 'plan-123',
    title: 'Test Learning Plan',
    description: 'Test learning plan description',
    content: {
      projects: [
        { title: 'Test Project', skills: ['JavaScript', 'React'] }
      ],
      total_estimated_hours: 40
    },
    created_at: '2024-01-15T10:00:00Z',
    ...overrides
  }),

  // Helper to wait for async operations
  waitForAsync: () => new Promise(resolve => setTimeout(resolve, 0)),

  // Helper to create mock API responses
  createMockApiResponse: (data, status = 200) => ({
    data,
    status,
    statusText: 'OK',
    headers: {},
    config: {}
  }),

  // Helper to create mock API errors
  createMockApiError: (message, status = 500) => ({
    response: {
      data: { message },
      status,
      statusText: status === 404 ? 'Not Found' : 'Internal Server Error'
    },
    message
  })
};

// Setup and teardown for each test
beforeEach(() => {
  // Clear all mocks before each test
  jest.clearAllMocks();
  
  // Reset localStorage and sessionStorage
  localStorage.clear();
  sessionStorage.clear();
  
  // Reset fetch mock
  if (global.fetch) {
    global.fetch.mockClear();
  }
});

afterEach(() => {
  // Clean up any timers
  jest.clearAllTimers();
  
  // Clean up any DOM changes
  document.body.innerHTML = '';
  
  // Reset any global state
  delete window.location;
  window.location = { href: 'http://localhost:3000' };
});

// Custom matchers for better assertions
expect.extend({
  toBeInTheDocument(received) {
    const pass = received !== null && document.body.contains(received);
    return {
      message: () => `expected element ${pass ? 'not ' : ''}to be in the document`,
      pass,
    };
  },
  
  toHaveClass(received, className) {
    const pass = received && received.classList && received.classList.contains(className);
    return {
      message: () => `expected element ${pass ? 'not ' : ''}to have class "${className}"`,
      pass,
    };
  }
});

// Error boundary for catching React errors in tests
export class TestErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Test Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <div data-testid="error-boundary">Something went wrong: {this.state.error?.message}</div>;
    }

    return this.props.children;
  }
}