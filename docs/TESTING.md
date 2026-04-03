# Testing Guide for Ponder Application

This document provides comprehensive information about the testing infrastructure, how to run tests, and testing best practices for the Ponder application.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Backend Testing](#backend-testing)
- [Frontend Testing](#frontend-testing)
- [Integration Testing](#integration-testing)
- [Coverage Reports](#coverage-reports)
- [CI/CD Pipeline](#cicd-pipeline)
- [Writing Tests](#writing-tests)
- [Troubleshooting](#troubleshooting)

## Overview

The Ponder application uses a comprehensive testing strategy that includes:

- **Unit Tests**: Test individual components and functions in isolation
- **Integration Tests**: Test interactions between different parts of the system
- **API Tests**: Test REST API endpoints with authentication and authorization
- **Component Tests**: Test React components with user interactions
- **End-to-End Tests**: Test complete user workflows (planned)

### Testing Technologies

**Backend:**
- **pytest**: Python testing framework
- **pytest-asyncio**: Async testing support
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities
- **factory-boy**: Test data factories
- **httpx**: HTTP client for API testing

**Frontend:**
- **Jest**: JavaScript testing framework
- **React Testing Library**: React component testing
- **MSW (Mock Service Worker)**: API mocking
- **@testing-library/user-event**: User interaction simulation

## Test Structure

```
├── backend/
│   ├── tests/
│   │   ├── conftest.py              # Test configuration and fixtures
│   │   ├── unit/                    # Unit tests
│   │   │   ├── test_auth_service.py
│   │   │   ├── test_message_service.py
│   │   │   ├── test_learning_service.py
│   │   │   ├── test_ai_integration_service.py
│   │   │   ├── test_memory_service.py
│   │   │   └── test_database_models.py
│   │   └── integration/             # Integration tests
│   │       └── test_api_endpoints.py
│   └── requirements.txt             # Includes testing dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── **/__tests__/        # Component tests
│   │   ├── api/
│   │   │   └── __tests__/           # API service tests
│   │   └── setupTests.js            # Test setup configuration
│   └── package.json                 # Includes testing dependencies
├── run_tests.py                     # Comprehensive test runner
└── .github/workflows/test.yml       # CI/CD pipeline
```

## Running Tests

### Quick Start

Run all tests with the comprehensive test runner:

```bash
# Run all tests with coverage
python run_tests.py

# Run tests without coverage
python run_tests.py --no-coverage

# Run only backend tests
python run_tests.py --components backend

# Run only frontend tests
python run_tests.py --components frontend

# Verbose output
python run_tests.py --verbose

# Skip environment setup (if already set up)
python run_tests.py --skip-setup
```

### Individual Test Suites

**Backend Tests:**
```bash
cd backend
python -m pytest tests/ --cov=app --cov-report=html
```

**Frontend Tests:**
```bash
cd frontend
npm test -- --coverage --watchAll=false
```

## Backend Testing

### Unit Tests

Backend unit tests are located in `backend/tests/unit/` and cover:

- **AuthService**: Authentication, JWT tokens, user management
- **MessageService**: Chat processing, AI integration, agent modes
- **LearningService**: Learning plan management, progress tracking
- **AIIntegrationService**: OpenAI/DeepSeek integration, retry logic
- **MemoryService**: Memory storage, vector database operations
- **Database Models**: Model creation, relationships, validation

### Test Configuration

The `conftest.py` file provides:
- Database fixtures with SQLite in-memory testing
- Mock services and external dependencies
- Test user and data factories
- Environment variable mocking

### Running Backend Tests

```bash
cd backend

# Run all backend tests
python -m pytest

# Run specific test file
python -m pytest tests/unit/test_auth_service.py

# Run with coverage
python -m pytest --cov=app --cov-report=html

# Run with verbose output
python -m pytest -v

# Run specific test method
python -m pytest tests/unit/test_auth_service.py::TestAuthService::test_verify_password_success
```

### Backend Test Examples

```python
# Example unit test
def test_create_access_token(auth_service):
    user_id = "test-user-123"
    token = auth_service.create_access_token(user_id)
    
    assert isinstance(token, str)
    assert len(token) > 100
    
    # Decode and verify token content
    payload = auth_service.decode_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "access"

# Example async test
@pytest.mark.asyncio
async def test_register_user_success(auth_service, test_db_session):
    result = await auth_service.register_user(
        "testuser", "test@example.com", "password123"
    )
    
    assert "user_id" in result
    
    # Verify user was created in database
    user = test_db_session.query(User).filter(User.email == "test@example.com").first()
    assert user is not None
```

## Frontend Testing

### Component Tests

Frontend tests are located alongside components in `__tests__/` directories and cover:

- **MainChat**: Chat interface, WebSocket integration, message handling
- **AgentModeSelector**: Mode selection, dropdown functionality
- **ProjectBoard**: Project management, learning plan integration
- **API Services**: HTTP requests, error handling, data transformation

### Test Setup

The `setupTests.js` file provides:
- Jest and React Testing Library configuration
- Mock implementations for browser APIs
- Global test utilities and helpers
- CSS module mocking

### Running Frontend Tests

```bash
cd frontend

# Run all frontend tests
npm test

# Run tests with coverage
npm test -- --coverage --watchAll=false

# Run specific test file
npm test MainChat.test.js

# Run tests in watch mode
npm test -- --watch

# Update snapshots
npm test -- --updateSnapshot
```

### Frontend Test Examples

```javascript
// Example component test
test('renders main chat interface', () => {
  renderMainChat();
  
  expect(screen.getByTestId('agent-mode-selector')).toBeInTheDocument();
  expect(screen.getByPlaceholderText(/type your message/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
});

// Example user interaction test
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
      message: 'Test message'
    })
  );
});
```

## Integration Testing

Integration tests verify that different parts of the system work together correctly:

### API Integration Tests

Located in `backend/tests/integration/test_api_endpoints.py`, these tests cover:

- Authentication flows (login, registration, token refresh)
- Protected route access with JWT tokens
- CRUD operations for users, projects, and learning plans
- WebSocket connections and messaging
- Error handling and status codes

### Running Integration Tests

```bash
cd backend

# Run only integration tests
python -m pytest tests/integration/

# Run with test database
DATABASE_URL=sqlite:///test.db python -m pytest tests/integration/
```

## Coverage Reports

### Backend Coverage

Coverage reports are generated in multiple formats:

```bash
cd backend
python -m pytest --cov=app --cov-report=html --cov-report=xml --cov-report=term-missing
```

- **HTML Report**: `backend/htmlcov/index.html`
- **XML Report**: `backend/coverage.xml` (for CI/CD)
- **Terminal**: Shows missing lines in terminal output

### Frontend Coverage

```bash
cd frontend
npm test -- --coverage --coverageDirectory=coverage
```

- **HTML Report**: `frontend/coverage/lcov-report/index.html`
- **LCOV Report**: `frontend/coverage/lcov.info` (for CI/CD)

### Coverage Targets

- **Backend**: Aim for >80% overall coverage
- **Frontend**: Aim for >75% overall coverage
- **Critical Services**: Aim for >90% coverage (AuthService, MessageService)

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/test.yml`) runs:

1. **Backend Tests**: Unit and integration tests with PostgreSQL and Redis
2. **Frontend Tests**: Component and API service tests
3. **Integration Tests**: Full-stack integration testing
4. **Code Quality**: Linting, formatting, and security checks
5. **Coverage Upload**: Results sent to Codecov

### Pipeline Triggers

- **Push** to `main` or `develop` branches
- **Pull Requests** to `main` or `develop` branches

### Environment Variables

The CI pipeline uses these environment variables:

```yaml
DATABASE_URL: postgresql://postgres:postgres@localhost:5432/ponder_test
REDIS_URL: redis://localhost:6379
JWT_SECRET: test-secret-key-for-ci
JWT_ALGORITHM: HS256
OPENAI_API_KEY: test-openai-key
ENVIRONMENT: test
```

## Writing Tests

### Best Practices

1. **Test Structure**: Follow Arrange-Act-Assert pattern
2. **Descriptive Names**: Use clear, descriptive test names
3. **Single Responsibility**: Each test should verify one specific behavior
4. **Mock External Dependencies**: Mock APIs, databases, and external services
5. **Test Edge Cases**: Include error conditions and boundary cases
6. **Keep Tests Fast**: Unit tests should run quickly
7. **Independent Tests**: Tests should not depend on each other

### Backend Test Guidelines

```python
class TestAuthService:
    """Test suite for AuthService."""
    
    def test_verify_password_success(self, auth_service):
        """Test successful password verification."""
        # Arrange
        plain_password = "test_password_123"
        hashed_password = auth_service.get_password_hash(plain_password)
        
        # Act
        result = auth_service.verify_password(plain_password, hashed_password)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, auth_service, test_user):
        """Test registration with duplicate email."""
        # Arrange
        email = test_user.email
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email already registered"):
            await auth_service.register_user("testuser2", email, "password")
```

### Frontend Test Guidelines

```javascript
describe('MainChat Component', () => {
  const renderMainChat = (props = {}) => {
    return render(
      <AuthContext.Provider value={mockAuthContext}>
        <TaskContext.Provider value={mockTaskContext}>
          <MainChat {...props} />
        </TaskContext.Provider>
      </AuthContext.Provider>
    );
  };

  test('sends message when Enter key is pressed', async () => {
    // Arrange
    const user = userEvent.setup();
    renderMainChat();
    
    // Act
    const messageInput = screen.getByPlaceholderText(/type your message/i);
    await user.type(messageInput, 'Test message{enter}');
    
    // Assert
    expect(websocketService.send).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'message',
        message: 'Test message'
      })
    );
  });
});
```

### Test Data Factories

Use factories for creating test data:

```python
# Backend factory example
def create_test_user(email="test@example.com", **kwargs):
    user = User()
    setattr(user, 'email', email)
    setattr(user, 'name', kwargs.get('name', 'Test User'))
    setattr(user, 'password_hash', kwargs.get('password_hash', 'hashed_password'))
    return user

# Frontend test utility example
const createMockProject = (overrides = {}) => ({
  id: 'project-123',
  title: 'Test Project',
  status: 'in_progress',
  completion_percentage: 50,
  ...overrides
});
```

## Troubleshooting

### Common Issues

**Backend Tests:**

1. **Database Connection Errors**
   ```bash
   # Ensure test database is properly configured
   export DATABASE_URL=sqlite:///test.db
   ```

2. **Import Errors**
   ```bash
   # Install test dependencies
   pip install -r requirements.txt
   ```

3. **Async Test Issues**
   ```python
   # Use pytest-asyncio marker
   @pytest.mark.asyncio
   async def test_async_function():
       result = await async_function()
       assert result is not None
   ```

**Frontend Tests:**

1. **Module Not Found Errors**
   ```bash
   # Clear node modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **WebSocket Mock Issues**
   ```javascript
   // Ensure WebSocket is properly mocked in setupTests.js
   global.WebSocket = class WebSocket { /* mock implementation */ };
   ```

3. **Async Component Testing**
   ```javascript
   // Use waitFor for async operations
   await waitFor(() => {
     expect(screen.getByText('Expected text')).toBeInTheDocument();
   });
   ```

### Debug Mode

**Backend:**
```bash
# Run with debug output
python -m pytest -v -s --tb=long

# Run single test with debugging
python -m pytest tests/unit/test_auth_service.py::test_name -v -s
```

**Frontend:**
```bash
# Run with debug output
npm test -- --verbose --no-coverage

# Debug specific test
npm test -- --testNamePattern="test name"
```

### Performance Issues

1. **Slow Tests**: Check for unnecessary database operations or network calls
2. **Memory Leaks**: Ensure proper cleanup in test teardown
3. **Timeout Issues**: Increase timeout for slow operations

```python
# Backend timeout example
@pytest.mark.timeout(30)
def test_slow_operation():
    # Test implementation
    pass
```

```javascript
// Frontend timeout example
test('slow operation', async () => {
  // Test implementation
}, 30000); // 30 second timeout
```

## Continuous Improvement

### Metrics to Track

- Test coverage percentage
- Test execution time
- Flaky test identification
- Code quality metrics

### Regular Maintenance

1. **Update Dependencies**: Keep testing libraries up to date
2. **Review Test Coverage**: Identify untested code paths
3. **Refactor Tests**: Keep tests maintainable and readable
4. **Performance Monitoring**: Ensure tests run efficiently

### Adding New Tests

When adding new features:

1. Write tests first (TDD approach)
2. Ensure adequate coverage for new code
3. Update integration tests for new API endpoints
4. Add component tests for new UI features
5. Update documentation as needed

For questions or issues with testing, please refer to the project documentation or create an issue in the repository.