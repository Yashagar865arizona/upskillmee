/**
 * Integration tests for Project API service.
 * Tests API calls, error handling, and data transformation.
 */

import axios from 'axios';
import {
  getUserProjects,
  createProjectFromPlan,
  updateProjectStatus,
  getUserLearningPlans
} from '../projectApi';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

describe('Project API Service', () => {
  const mockToken = 'mock-jwt-token';
  const mockUserId = 'user-123';

  beforeEach(() => {
    jest.clearAllMocks();
    mockedAxios.get.mockClear();
    mockedAxios.post.mockClear();
    mockedAxios.put.mockClear();
  });

  describe('getUserProjects', () => {
    test('fetches user projects successfully', async () => {
      const mockProjects = [
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

      mockedAxios.get.mockResolvedValue({ data: mockProjects });

      const result = await getUserProjects(mockUserId, mockToken);

      expect(mockedAxios.get).toHaveBeenCalledWith(
        `/api/v1/projects/user/${mockUserId}`,
        {
          headers: {
            Authorization: `Bearer ${mockToken}`,
            'Content-Type': 'application/json'
          }
        }
      );
      expect(result).toEqual(mockProjects);
    });

    test('handles API errors gracefully', async () => {
      const errorMessage = 'Failed to fetch projects';
      mockedAxios.get.mockRejectedValue(new Error(errorMessage));

      await expect(getUserProjects(mockUserId, mockToken)).rejects.toThrow(errorMessage);
    });

    test('handles network errors', async () => {
      mockedAxios.get.mockRejectedValue({
        code: 'NETWORK_ERROR',
        message: 'Network Error'
      });

      await expect(getUserProjects(mockUserId, mockToken)).rejects.toMatchObject({
        code: 'NETWORK_ERROR'
      });
    });

    test('handles 401 unauthorized errors', async () => {
      mockedAxios.get.mockRejectedValue({
        response: {
          status: 401,
          data: { message: 'Unauthorized' }
        }
      });

      await expect(getUserProjects(mockUserId, mockToken)).rejects.toMatchObject({
        response: { status: 401 }
      });
    });

    test('handles empty response', async () => {
      mockedAxios.get.mockResolvedValue({ data: [] });

      const result = await getUserProjects(mockUserId, mockToken);

      expect(result).toEqual([]);
    });

    test('validates required parameters', async () => {
      await expect(getUserProjects(null, mockToken)).rejects.toThrow();
      await expect(getUserProjects(mockUserId, null)).rejects.toThrow();
    });
  });

  describe('createProjectFromPlan', () => {
    test('creates project from learning plan successfully', async () => {
      const mockPlan = {
        id: 'plan-1',
        title: 'Web Development Basics',
        description: 'Learn HTML, CSS, and JavaScript',
        content: {
          projects: [
            { title: 'Personal Website', skills: ['HTML', 'CSS'] }
          ]
        }
      };

      const mockCreatedProject = {
        id: 'project-3',
        title: 'Web Development Basics',
        description: 'Learn HTML, CSS, and JavaScript',
        status: 'accepted',
        completion_percentage: 0,
        created_from_plan: 'plan-1'
      };

      mockedAxios.post.mockResolvedValue({ data: mockCreatedProject });

      const result = await createProjectFromPlan(mockPlan, mockUserId, mockToken);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/v1/projects/from-plan',
        {
          plan: mockPlan,
          user_id: mockUserId
        },
        {
          headers: {
            Authorization: `Bearer ${mockToken}`,
            'Content-Type': 'application/json'
          }
        }
      );
      expect(result).toEqual(mockCreatedProject);
    });

    test('handles plan creation errors', async () => {
      const mockPlan = { id: 'plan-1', title: 'Test Plan' };
      
      mockedAxios.post.mockRejectedValue({
        response: {
          status: 400,
          data: { message: 'Invalid plan data' }
        }
      });

      await expect(createProjectFromPlan(mockPlan, mockUserId, mockToken))
        .rejects.toMatchObject({
          response: { status: 400 }
        });
    });

    test('validates plan object', async () => {
      await expect(createProjectFromPlan(null, mockUserId, mockToken))
        .rejects.toThrow();
      
      await expect(createProjectFromPlan({}, mockUserId, mockToken))
        .rejects.toThrow();
    });

    test('handles server errors during creation', async () => {
      const mockPlan = { id: 'plan-1', title: 'Test Plan' };
      
      mockedAxios.post.mockRejectedValue({
        response: {
          status: 500,
          data: { message: 'Internal server error' }
        }
      });

      await expect(createProjectFromPlan(mockPlan, mockUserId, mockToken))
        .rejects.toMatchObject({
          response: { status: 500 }
        });
    });
  });

  describe('updateProjectStatus', () => {
    test('updates project status successfully', async () => {
      const projectId = 'project-1';
      const newStatus = 'completed';
      const mockUpdatedProject = {
        id: projectId,
        status: newStatus,
        completion_percentage: 100,
        updated_at: '2024-01-15T10:00:00Z'
      };

      mockedAxios.put.mockResolvedValue({ data: mockUpdatedProject });

      const result = await updateProjectStatus(projectId, newStatus, mockToken);

      expect(mockedAxios.put).toHaveBeenCalledWith(
        `/api/v1/projects/${projectId}/status`,
        { status: newStatus },
        {
          headers: {
            Authorization: `Bearer ${mockToken}`,
            'Content-Type': 'application/json'
          }
        }
      );
      expect(result).toEqual(mockUpdatedProject);
    });

    test('handles invalid status values', async () => {
      const projectId = 'project-1';
      const invalidStatus = 'invalid_status';
      
      mockedAxios.put.mockRejectedValue({
        response: {
          status: 400,
          data: { message: 'Invalid status value' }
        }
      });

      await expect(updateProjectStatus(projectId, invalidStatus, mockToken))
        .rejects.toMatchObject({
          response: { status: 400 }
        });
    });

    test('handles project not found errors', async () => {
      const nonExistentProjectId = 'project-999';
      const status = 'completed';
      
      mockedAxios.put.mockRejectedValue({
        response: {
          status: 404,
          data: { message: 'Project not found' }
        }
      });

      await expect(updateProjectStatus(nonExistentProjectId, status, mockToken))
        .rejects.toMatchObject({
          response: { status: 404 }
        });
    });

    test('validates required parameters', async () => {
      await expect(updateProjectStatus(null, 'completed', mockToken))
        .rejects.toThrow();
      
      await expect(updateProjectStatus('project-1', null, mockToken))
        .rejects.toThrow();
      
      await expect(updateProjectStatus('project-1', 'completed', null))
        .rejects.toThrow();
    });
  });

  describe('getUserLearningPlans', () => {
    test('fetches user learning plans successfully', async () => {
      const mockLearningPlans = [
        {
          id: 'plan-1',
          title: 'Web Development Basics',
          description: 'Learn HTML, CSS, and JavaScript',
          content: {
            projects: [
              { title: 'Personal Website', skills: ['HTML', 'CSS'] }
            ],
            total_estimated_hours: 40
          },
          created_at: '2024-01-15T10:00:00Z'
        },
        {
          id: 'plan-2',
          title: 'Python Programming',
          description: 'Learn Python fundamentals',
          content: {
            projects: [
              { title: 'Calculator App', skills: ['Python'] }
            ],
            total_estimated_hours: 30
          },
          created_at: '2024-01-14T10:00:00Z'
        }
      ];

      mockedAxios.get.mockResolvedValue({ data: mockLearningPlans });

      const result = await getUserLearningPlans(mockUserId, mockToken);

      expect(mockedAxios.get).toHaveBeenCalledWith(
        `/api/v1/learning/plans/user/${mockUserId}`,
        {
          headers: {
            Authorization: `Bearer ${mockToken}`,
            'Content-Type': 'application/json'
          }
        }
      );
      expect(result).toEqual(mockLearningPlans);
    });

    test('handles empty learning plans response', async () => {
      mockedAxios.get.mockResolvedValue({ data: [] });

      const result = await getUserLearningPlans(mockUserId, mockToken);

      expect(result).toEqual([]);
    });

    test('handles API errors when fetching learning plans', async () => {
      mockedAxios.get.mockRejectedValue({
        response: {
          status: 500,
          data: { message: 'Server error' }
        }
      });

      await expect(getUserLearningPlans(mockUserId, mockToken))
        .rejects.toMatchObject({
          response: { status: 500 }
        });
    });

    test('handles malformed learning plan data', async () => {
      const malformedData = [
        { id: 'plan-1' }, // Missing required fields
        { title: 'Plan without ID' }, // Missing ID
        null, // Null entry
        undefined // Undefined entry
      ];

      mockedAxios.get.mockResolvedValue({ data: malformedData });

      const result = await getUserLearningPlans(mockUserId, mockToken);

      // Should still return the data, let the component handle validation
      expect(result).toEqual(malformedData);
    });
  });

  describe('API Configuration', () => {
    test('uses correct base URL for all endpoints', async () => {
      mockedAxios.get.mockResolvedValue({ data: [] });

      await getUserProjects(mockUserId, mockToken);
      await getUserLearningPlans(mockUserId, mockToken);

      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/'),
        expect.any(Object)
      );
    });

    test('includes proper headers in all requests', async () => {
      mockedAxios.get.mockResolvedValue({ data: [] });
      mockedAxios.post.mockResolvedValue({ data: {} });
      mockedAxios.put.mockResolvedValue({ data: {} });

      await getUserProjects(mockUserId, mockToken);
      await createProjectFromPlan({ id: 'plan-1', title: 'Test' }, mockUserId, mockToken);
      await updateProjectStatus('project-1', 'completed', mockToken);

      // Check that all calls include proper headers
      const expectedHeaders = {
        Authorization: `Bearer ${mockToken}`,
        'Content-Type': 'application/json'
      };

      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ headers: expectedHeaders })
      );

      expect(mockedAxios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(Object),
        expect.objectContaining({ headers: expectedHeaders })
      );

      expect(mockedAxios.put).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(Object),
        expect.objectContaining({ headers: expectedHeaders })
      );
    });

    test('handles timeout errors', async () => {
      mockedAxios.get.mockRejectedValue({
        code: 'ECONNABORTED',
        message: 'timeout of 5000ms exceeded'
      });

      await expect(getUserProjects(mockUserId, mockToken))
        .rejects.toMatchObject({
          code: 'ECONNABORTED'
        });
    });

    test('handles CORS errors', async () => {
      mockedAxios.get.mockRejectedValue({
        message: 'Network Error',
        config: { url: '/api/v1/projects/user/user-123' }
      });

      await expect(getUserProjects(mockUserId, mockToken))
        .rejects.toMatchObject({
          message: 'Network Error'
        });
    });
  });

  describe('Data Transformation', () => {
    test('preserves data structure from API response', async () => {
      const mockApiResponse = {
        id: 'project-1',
        title: 'Test Project',
        metadata: {
          custom_field: 'custom_value',
          nested: {
            deep_field: 'deep_value'
          }
        }
      };

      mockedAxios.get.mockResolvedValue({ data: [mockApiResponse] });

      const result = await getUserProjects(mockUserId, mockToken);

      expect(result[0]).toEqual(mockApiResponse);
      expect(result[0].metadata.custom_field).toBe('custom_value');
      expect(result[0].metadata.nested.deep_field).toBe('deep_value');
    });

    test('handles date strings correctly', async () => {
      const mockProjectWithDates = {
        id: 'project-1',
        title: 'Test Project',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-16T15:30:00Z',
        due_date: '2024-02-15T23:59:59Z'
      };

      mockedAxios.get.mockResolvedValue({ data: [mockProjectWithDates] });

      const result = await getUserProjects(mockUserId, mockToken);

      expect(result[0].created_at).toBe('2024-01-15T10:00:00Z');
      expect(result[0].updated_at).toBe('2024-01-16T15:30:00Z');
      expect(result[0].due_date).toBe('2024-02-15T23:59:59Z');
    });
  });

  describe('Error Response Handling', () => {
    test('extracts error messages from API responses', async () => {
      const errorResponse = {
        response: {
          status: 400,
          data: {
            message: 'Validation failed',
            errors: [
              { field: 'title', message: 'Title is required' },
              { field: 'description', message: 'Description too long' }
            ]
          }
        }
      };

      mockedAxios.post.mockRejectedValue(errorResponse);

      try {
        await createProjectFromPlan({ id: 'plan-1' }, mockUserId, mockToken);
      } catch (error) {
        expect(error.response.data.message).toBe('Validation failed');
        expect(error.response.data.errors).toHaveLength(2);
      }
    });

    test('handles different error response formats', async () => {
      const errorFormats = [
        { response: { status: 400, data: 'Simple string error' } },
        { response: { status: 500, data: { error: 'Object with error field' } } },
        { response: { status: 404, data: { detail: 'Object with detail field' } } },
        { message: 'Network error without response' }
      ];

      for (const errorFormat of errorFormats) {
        mockedAxios.get.mockRejectedValue(errorFormat);

        await expect(getUserProjects(mockUserId, mockToken))
          .rejects.toMatchObject(errorFormat);
      }
    });
  });
});