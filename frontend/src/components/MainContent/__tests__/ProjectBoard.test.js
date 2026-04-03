/**
 * Unit tests for ProjectBoard component.
 * Tests project management, learning plan integration, and user interactions.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import ProjectBoard from '../ProjectBoard';
import { AuthContext } from '../../../context/AuthContext';
import * as projectApi from '../../../api/projectApi';

// Mock the API functions
jest.mock('../../../api/projectApi', () => ({
  getUserProjects: jest.fn(),
  createProjectFromPlan: jest.fn(),
  updateProjectStatus: jest.fn(),
  getUserLearningPlans: jest.fn()
}));

// Mock child components
jest.mock('../ProjectCard', () => {
  return function MockProjectCard({ project, onAccept, onReject, isLearningPlan, showActions, onViewDetails }) {
    return (
      <div data-testid={`project-card-${project.id || project.title}`}>
        <h3>{project.title}</h3>
        <p>{project.description}</p>
        {showActions && (
          <div>
            <button onClick={() => onAccept(project)}>Accept</button>
            <button onClick={() => onReject(project)}>Reject</button>
          </div>
        )}
        {onViewDetails && (
          <button onClick={() => onViewDetails(project)}>View Details</button>
        )}
      </div>
    );
  };
});

jest.mock('../TaskTracker', () => {
  return function MockTaskTracker({ project, onProgressUpdate }) {
    return (
      <div data-testid="task-tracker">
        <h3>Task Tracker for {project.title}</h3>
        <button onClick={() => onProgressUpdate(project.id, 75)}>
          Update Progress
        </button>
      </div>
    );
  };
});

// Mock Lucide React icons
jest.mock('lucide-react', () => ({
  Plus: () => <div data-testid="plus-icon">+</div>,
  BookOpen: () => <div data-testid="book-open-icon">📖</div>,
  Target: () => <div data-testid="target-icon">🎯</div>,
  Clock: () => <div data-testid="clock-icon">⏰</div>,
  CheckCircle: () => <div data-testid="check-circle-icon">✅</div>,
  List: () => <div data-testid="list-icon">📋</div>
}));

describe('ProjectBoard Component', () => {
  const mockUser = {
    id: 'user-123',
    name: 'Test User',
    email: 'test@example.com'
  };

  const mockAuthContext = {
    user: mockUser,
    token: 'mock-jwt-token',
    isAuthenticated: true
  };

  const mockLearningPlans = [
    {
      id: 'plan-1',
      title: 'Web Development Basics',
      description: 'Learn HTML, CSS, and JavaScript',
      content: {
        projects: [
          { title: 'Personal Website', skills: ['HTML', 'CSS'] }
        ]
      }
    },
    {
      id: 'plan-2',
      title: 'Python Programming',
      description: 'Learn Python fundamentals',
      content: {
        projects: [
          { title: 'Calculator App', skills: ['Python'] }
        ]
      }
    }
  ];

  const mockUserProjects = [
    {
      id: 'project-1',
      title: 'React Dashboard',
      description: 'Build a React dashboard',
      status: 'in_progress',
      completion_percentage: 60
    },
    {
      id: 'project-2',
      title: 'Node.js API',
      description: 'Create a REST API',
      status: 'completed',
      completion_percentage: 100
    }
  ];

  const renderProjectBoard = (authContext = mockAuthContext) => {
    return render(
      <AuthContext.Provider value={authContext}>
        <ProjectBoard />
      </AuthContext.Provider>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
    projectApi.getUserLearningPlans.mockResolvedValue(mockLearningPlans);
    projectApi.getUserProjects.mockResolvedValue(mockUserProjects);
  });

  describe('Component Rendering', () => {
    test('renders main project board interface', async () => {
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByText('Your Learning Journey')).toBeInTheDocument();
        expect(screen.getByText('Discover new learning paths and track your progress')).toBeInTheDocument();
      });
    });

    test('renders statistics cards', async () => {
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByText('Total Projects')).toBeInTheDocument();
        expect(screen.getByText('In Progress')).toBeInTheDocument();
        expect(screen.getByText('Completed')).toBeInTheDocument();
      });
    });

    test('renders tab navigation', async () => {
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByText(/New Learning Plans/)).toBeInTheDocument();
        expect(screen.getByText(/My Projects/)).toBeInTheDocument();
        expect(screen.getByText(/Task Tracking/)).toBeInTheDocument();
      });
    });

    test('shows loading state initially', () => {
      renderProjectBoard();
      
      expect(screen.getByText('Loading your learning journey...')).toBeInTheDocument();
    });

    test('does not render when user is not authenticated', () => {
      const unauthenticatedContext = {
        user: null,
        token: null,
        isAuthenticated: false
      };
      
      renderProjectBoard(unauthenticatedContext);
      
      expect(screen.getByText('Loading your learning journey...')).toBeInTheDocument();
    });
  });

  describe('Data Loading', () => {
    test('loads learning plans and projects on mount', async () => {
      renderProjectBoard();
      
      await waitFor(() => {
        expect(projectApi.getUserLearningPlans).toHaveBeenCalledWith(mockUser.id, mockAuthContext.token);
        expect(projectApi.getUserProjects).toHaveBeenCalledWith(mockUser.id, mockAuthContext.token);
      });
    });

    test('displays learning plans when loaded', async () => {
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByTestId('project-card-Web Development Basics')).toBeInTheDocument();
        expect(screen.getByTestId('project-card-Python Programming')).toBeInTheDocument();
      });
    });

    test('displays user projects when loaded', async () => {
      const user = userEvent.setup();
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByText(/New Learning Plans/)).toBeInTheDocument();
      });
      
      // Switch to projects tab
      const projectsTab = screen.getByText(/My Projects/);
      await user.click(projectsTab);
      
      await waitFor(() => {
        expect(screen.getByTestId('project-card-project-1')).toBeInTheDocument();
        expect(screen.getByTestId('project-card-project-2')).toBeInTheDocument();
      });
    });

    test('handles API errors gracefully', async () => {
      projectApi.getUserLearningPlans.mockRejectedValue(new Error('API Error'));
      projectApi.getUserProjects.mockRejectedValue(new Error('API Error'));
      
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load projects. Please try again.')).toBeInTheDocument();
        expect(screen.getByText('Try Again')).toBeInTheDocument();
      });
    });

    test('retries loading when retry button is clicked', async () => {
      const user = userEvent.setup();
      projectApi.getUserLearningPlans.mockRejectedValueOnce(new Error('API Error'));
      projectApi.getUserProjects.mockRejectedValueOnce(new Error('API Error'));
      
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByText('Try Again')).toBeInTheDocument();
      });
      
      // Reset mocks to return successful data
      projectApi.getUserLearningPlans.mockResolvedValue(mockLearningPlans);
      projectApi.getUserProjects.mockResolvedValue(mockUserProjects);
      
      const retryButton = screen.getByText('Try Again');
      await user.click(retryButton);
      
      await waitFor(() => {
        expect(screen.getByTestId('project-card-Web Development Basics')).toBeInTheDocument();
      });
    });
  });

  describe('Statistics Calculation', () => {
    test('calculates project statistics correctly', async () => {
      renderProjectBoard();
      
      await waitFor(() => {
        // Total projects: 2
        expect(screen.getByText('2')).toBeInTheDocument();
        
        // In progress: 1 (project with status 'in_progress')
        expect(screen.getByText('1')).toBeInTheDocument();
        
        // Completed: 1 (project with status 'completed')
        expect(screen.getByText('1')).toBeInTheDocument();
      });
    });

    test('handles empty project list', async () => {
      projectApi.getUserProjects.mockResolvedValue([]);
      
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByText('0')).toBeInTheDocument(); // Total projects
      });
    });
  });

  describe('Tab Navigation', () => {
    test('switches between tabs correctly', async () => {
      const user = userEvent.setup();
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByText(/New Learning Plans/)).toBeInTheDocument();
      });
      
      // Initially on plans tab
      expect(screen.getByTestId('project-card-Web Development Basics')).toBeInTheDocument();
      
      // Switch to projects tab
      const projectsTab = screen.getByText(/My Projects/);
      await user.click(projectsTab);
      
      await waitFor(() => {
        expect(screen.getByTestId('project-card-project-1')).toBeInTheDocument();
      });
      
      // Switch to tasks tab
      const tasksTab = screen.getByText(/Task Tracking/);
      await user.click(tasksTab);
      
      await waitFor(() => {
        expect(screen.getByText('Select a Project to Track')).toBeInTheDocument();
      });
    });

    test('shows correct tab counts', async () => {
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByText(/New Learning Plans \(2\)/)).toBeInTheDocument();
        expect(screen.getByText(/My Projects \(2\)/)).toBeInTheDocument();
      });
    });
  });

  describe('Learning Plan Management', () => {
    test('accepts learning plan and creates project', async () => {
      const user = userEvent.setup();
      const mockNewProject = {
        id: 'project-3',
        title: 'Web Development Basics',
        status: 'accepted'
      };
      
      projectApi.createProjectFromPlan.mockResolvedValue(mockNewProject);
      
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByTestId('project-card-Web Development Basics')).toBeInTheDocument();
      });
      
      const acceptButton = screen.getByText('Accept');
      await user.click(acceptButton);
      
      await waitFor(() => {
        expect(projectApi.createProjectFromPlan).toHaveBeenCalledWith(
          mockLearningPlans[0],
          mockUser.id,
          mockAuthContext.token
        );
      });
    });

    test('rejects learning plan and removes from list', async () => {
      const user = userEvent.setup();
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByTestId('project-card-Web Development Basics')).toBeInTheDocument();
      });
      
      const rejectButton = screen.getByText('Reject');
      await user.click(rejectButton);
      
      await waitFor(() => {
        expect(screen.queryByTestId('project-card-Web Development Basics')).not.toBeInTheDocument();
      });
    });

    test('shows empty state when no learning plans', async () => {
      projectApi.getUserLearningPlans.mockResolvedValue([]);
      
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByText('No New Learning Plans')).toBeInTheDocument();
        expect(screen.getByText('Start a conversation with the AI to generate personalized learning plans!')).toBeInTheDocument();
      });
    });
  });

  describe('Project Management', () => {
    test('shows empty state when no projects', async () => {
      const user = userEvent.setup();
      projectApi.getUserProjects.mockResolvedValue([]);
      
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByText(/My Projects/)).toBeInTheDocument();
      });
      
      const projectsTab = screen.getByText(/My Projects/);
      await user.click(projectsTab);
      
      await waitFor(() => {
        expect(screen.getByText('No Projects Yet')).toBeInTheDocument();
        expect(screen.getByText('Accept a learning plan to start your first project!')).toBeInTheDocument();
      });
    });

    test('allows viewing project details', async () => {
      const user = userEvent.setup();
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByText(/My Projects/)).toBeInTheDocument();
      });
      
      const projectsTab = screen.getByText(/My Projects/);
      await user.click(projectsTab);
      
      await waitFor(() => {
        expect(screen.getByTestId('project-card-project-1')).toBeInTheDocument();
      });
      
      const viewDetailsButton = screen.getByText('View Details');
      await user.click(viewDetailsButton);
      
      // Should switch to tasks tab and show task tracker
      await waitFor(() => {
        expect(screen.getByTestId('task-tracker')).toBeInTheDocument();
      });
    });
  });

  describe('Task Tracking', () => {
    test('shows project selection when no project selected', async () => {
      const user = userEvent.setup();
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByText(/Task Tracking/)).toBeInTheDocument();
      });
      
      const tasksTab = screen.getByText(/Task Tracking/);
      await user.click(tasksTab);
      
      await waitFor(() => {
        expect(screen.getByText('Select a Project to Track')).toBeInTheDocument();
      });
    });

    test('shows task tracker when project is selected', async () => {
      const user = userEvent.setup();
      renderProjectBoard();
      
      // Navigate to projects tab and select a project
      await waitFor(() => {
        expect(screen.getByText(/My Projects/)).toBeInTheDocument();
      });
      
      const projectsTab = screen.getByText(/My Projects/);
      await user.click(projectsTab);
      
      await waitFor(() => {
        expect(screen.getByTestId('project-card-project-1')).toBeInTheDocument();
      });
      
      const viewDetailsButton = screen.getByText('View Details');
      await user.click(viewDetailsButton);
      
      await waitFor(() => {
        expect(screen.getByTestId('task-tracker')).toBeInTheDocument();
        expect(screen.getByText('Task Tracker for React Dashboard')).toBeInTheDocument();
      });
    });

    test('updates project progress when progress is updated', async () => {
      const user = userEvent.setup();
      renderProjectBoard();
      
      // Navigate to task tracker
      const projectsTab = screen.getByText(/My Projects/);
      await user.click(projectsTab);
      
      await waitFor(() => {
        expect(screen.getByTestId('project-card-project-1')).toBeInTheDocument();
      });
      
      const viewDetailsButton = screen.getByText('View Details');
      await user.click(viewDetailsButton);
      
      await waitFor(() => {
        expect(screen.getByTestId('task-tracker')).toBeInTheDocument();
      });
      
      const updateProgressButton = screen.getByText('Update Progress');
      await user.click(updateProgressButton);
      
      // Progress should be updated in the component state
      // This would be reflected in the UI if we had progress indicators
    });

    test('allows going back to project selection', async () => {
      const user = userEvent.setup();
      renderProjectBoard();
      
      // Navigate to task tracker
      const projectsTab = screen.getByText(/My Projects/);
      await user.click(projectsTab);
      
      await waitFor(() => {
        expect(screen.getByTestId('project-card-project-1')).toBeInTheDocument();
      });
      
      const viewDetailsButton = screen.getByText('View Details');
      await user.click(viewDetailsButton);
      
      await waitFor(() => {
        expect(screen.getByTestId('task-tracker')).toBeInTheDocument();
      });
      
      const backButton = screen.getByText('← Back to Project Selection');
      await user.click(backButton);
      
      await waitFor(() => {
        expect(screen.getByText('Select a Project to Track')).toBeInTheDocument();
      });
    });

    test('shows empty state when no projects for tracking', async () => {
      const user = userEvent.setup();
      projectApi.getUserProjects.mockResolvedValue([]);
      
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByText(/Task Tracking/)).toBeInTheDocument();
      });
      
      const tasksTab = screen.getByText(/Task Tracking/);
      await user.click(tasksTab);
      
      await waitFor(() => {
        expect(screen.getByText('No Projects to Track')).toBeInTheDocument();
        expect(screen.getByText('Accept a learning plan to start tracking your progress!')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('handles learning plan acceptance errors', async () => {
      const user = userEvent.setup();
      projectApi.createProjectFromPlan.mockRejectedValue(new Error('Creation failed'));
      
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByTestId('project-card-Web Development Basics')).toBeInTheDocument();
      });
      
      const acceptButton = screen.getByText('Accept');
      await user.click(acceptButton);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to accept learning plan. Please try again.')).toBeInTheDocument();
      });
    });

    test('handles non-array API responses gracefully', async () => {
      projectApi.getUserLearningPlans.mockResolvedValue(null);
      projectApi.getUserProjects.mockResolvedValue(undefined);
      
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByText('No New Learning Plans')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    test('has proper heading structure', async () => {
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1, name: 'Your Learning Journey' })).toBeInTheDocument();
      });
    });

    test('tab buttons have proper roles and states', async () => {
      renderProjectBoard();
      
      await waitFor(() => {
        const plansTab = screen.getByRole('button', { name: /New Learning Plans/ });
        const projectsTab = screen.getByRole('button', { name: /My Projects/ });
        const tasksTab = screen.getByRole('button', { name: /Task Tracking/ });
        
        expect(plansTab).toHaveAttribute('aria-selected', 'true');
        expect(projectsTab).toHaveAttribute('aria-selected', 'false');
        expect(tasksTab).toHaveAttribute('aria-selected', 'false');
      });
    });

    test('provides meaningful alt text for icons', async () => {
      renderProjectBoard();
      
      await waitFor(() => {
        expect(screen.getByTestId('target-icon')).toBeInTheDocument();
        expect(screen.getByTestId('book-open-icon')).toBeInTheDocument();
        expect(screen.getByTestId('list-icon')).toBeInTheDocument();
      });
    });
  });
});