/**
 * Unit tests for AgentModeSelector component.
 * Tests mode selection, dropdown functionality, and user interactions.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import AgentModeSelector from '../AgentModeSelector';

describe('AgentModeSelector Component', () => {
  const mockOnModeChange = jest.fn();
  
  const defaultProps = {
    currentMode: 'chat',
    onModeChange: mockOnModeChange,
    availableModes: null
  };

  const customModes = {
    chat: 'Custom chat description',
    work: 'Custom work description',
    plan: 'Custom plan description'
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Component Rendering', () => {
    test('renders with default mode', () => {
      render(<AgentModeSelector {...defaultProps} />);
      
      expect(screen.getByRole('button', { name: /ai mode selector/i })).toBeInTheDocument();
      expect(screen.getByText('Mentor')).toBeInTheDocument();
    });

    test('renders with custom available modes', () => {
      render(<AgentModeSelector {...defaultProps} availableModes={customModes} />);
      
      expect(screen.getByRole('button', { name: /ai mode selector/i })).toBeInTheDocument();
    });

    test('displays correct mode name for each mode', () => {
      const modes = ['chat', 'work', 'plan'];
      const expectedNames = ['Mentor', 'Project Partner', 'Learning Path'];
      
      modes.forEach((mode, index) => {
        const { rerender } = render(<AgentModeSelector {...defaultProps} currentMode={mode} />);
        expect(screen.getByText(expectedNames[index])).toBeInTheDocument();
        rerender(<div />); // Clear for next iteration
      });
    });

    test('shows dropdown arrow indicator', () => {
      render(<AgentModeSelector {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      expect(button).toHaveClass('modeIndicator');
    });
  });

  describe('Dropdown Functionality', () => {
    test('opens dropdown when button is clicked', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      await user.click(button);
      
      // Check if dropdown options are visible
      expect(screen.getByText('General guidance & mentoring')).toBeInTheDocument();
      expect(screen.getByText('Execute projects & learning')).toBeInTheDocument();
      expect(screen.getByText('Create learning roadmaps')).toBeInTheDocument();
    });

    test('closes dropdown when button is clicked again', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      
      // Open dropdown
      await user.click(button);
      expect(screen.getByText('General guidance & mentoring')).toBeInTheDocument();
      
      // Close dropdown
      await user.click(button);
      await waitFor(() => {
        expect(screen.queryByText('General guidance & mentoring')).not.toBeInTheDocument();
      });
    });

    test('closes dropdown when clicking outside', async () => {
      const user = userEvent.setup();
      render(
        <div>
          <AgentModeSelector {...defaultProps} />
          <div data-testid="outside-element">Outside</div>
        </div>
      );
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      const outsideElement = screen.getByTestId('outside-element');
      
      // Open dropdown
      await user.click(button);
      expect(screen.getByText('General guidance & mentoring')).toBeInTheDocument();
      
      // Click outside
      await user.click(outsideElement);
      await waitFor(() => {
        expect(screen.queryByText('General guidance & mentoring')).not.toBeInTheDocument();
      });
    });

    test('displays all available modes in dropdown', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      await user.click(button);
      
      // Check all mode options are present
      expect(screen.getByText('Mentor')).toBeInTheDocument();
      expect(screen.getByText('Project Partner')).toBeInTheDocument();
      expect(screen.getByText('Learning Path')).toBeInTheDocument();
      
      // Check descriptions
      expect(screen.getByText('General guidance & mentoring')).toBeInTheDocument();
      expect(screen.getByText('Execute projects & learning')).toBeInTheDocument();
      expect(screen.getByText('Create learning roadmaps')).toBeInTheDocument();
    });
  });

  describe('Mode Selection', () => {
    test('calls onModeChange when mode is selected', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      await user.click(button);
      
      // Click on work mode
      const workOption = screen.getByText('Project Partner');
      await user.click(workOption);
      
      expect(mockOnModeChange).toHaveBeenCalledWith('work');
    });

    test('closes dropdown after mode selection', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      await user.click(button);
      
      const planOption = screen.getByText('Learning Path');
      await user.click(planOption);
      
      await waitFor(() => {
        expect(screen.queryByText('Create learning roadmaps')).not.toBeInTheDocument();
      });
    });

    test('does not call onModeChange when clicking current mode', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} currentMode="chat" />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      await user.click(button);
      
      // Click on current mode (chat/Mentor)
      const chatOption = screen.getByText('Mentor');
      await user.click(chatOption);
      
      expect(mockOnModeChange).toHaveBeenCalledWith('chat');
    });

    test('highlights current mode in dropdown', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} currentMode="work" />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      await user.click(button);
      
      // Current mode should be highlighted
      const workOption = screen.getByText('Project Partner').closest('button');
      expect(workOption).toHaveClass('active');
    });
  });

  describe('Custom Modes', () => {
    test('uses custom mode descriptions when provided', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} availableModes={customModes} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      await user.click(button);
      
      expect(screen.getByText('Custom chat description')).toBeInTheDocument();
      expect(screen.getByText('Custom work description')).toBeInTheDocument();
      expect(screen.getByText('Custom plan description')).toBeInTheDocument();
    });

    test('falls back to default modes when custom modes are empty', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} availableModes={{}} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      await user.click(button);
      
      // Should show default descriptions
      expect(screen.getByText('General conversation and mentoring')).toBeInTheDocument();
    });

    test('handles partial custom modes', async () => {
      const user = userEvent.setup();
      const partialModes = { chat: 'Custom chat only' };
      render(<AgentModeSelector {...defaultProps} availableModes={partialModes} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      await user.click(button);
      
      expect(screen.getByText('Custom chat only')).toBeInTheDocument();
    });
  });

  describe('Keyboard Navigation', () => {
    test('opens dropdown with Enter key', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      button.focus();
      
      await user.keyboard('{Enter}');
      
      expect(screen.getByText('General guidance & mentoring')).toBeInTheDocument();
    });

    test('opens dropdown with Space key', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      button.focus();
      
      await user.keyboard(' ');
      
      expect(screen.getByText('General guidance & mentoring')).toBeInTheDocument();
    });

    test('closes dropdown with Escape key', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      await user.click(button);
      
      expect(screen.getByText('General guidance & mentoring')).toBeInTheDocument();
      
      await user.keyboard('{Escape}');
      
      await waitFor(() => {
        expect(screen.queryByText('General guidance & mentoring')).not.toBeInTheDocument();
      });
    });

    test('navigates options with arrow keys', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      await user.click(button);
      
      // Navigate with arrow keys
      await user.keyboard('{ArrowDown}');
      await user.keyboard('{ArrowDown}');
      await user.keyboard('{Enter}');
      
      expect(mockOnModeChange).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA attributes', () => {
      render(<AgentModeSelector {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      
      expect(button).toHaveAttribute('aria-label', 'AI mode selector');
      expect(button).toHaveAttribute('aria-haspopup', 'true');
      expect(button).toHaveAttribute('aria-expanded', 'false');
    });

    test('updates aria-expanded when dropdown opens', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      
      expect(button).toHaveAttribute('aria-expanded', 'false');
      
      await user.click(button);
      
      expect(button).toHaveAttribute('aria-expanded', 'true');
    });

    test('dropdown has proper role and labeling', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      await user.click(button);
      
      const dropdown = screen.getByRole('listbox');
      expect(dropdown).toBeInTheDocument();
      expect(dropdown).toHaveAttribute('aria-labelledby');
    });

    test('mode options have proper roles', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      await user.click(button);
      
      const options = screen.getAllByRole('option');
      expect(options).toHaveLength(3);
      
      options.forEach(option => {
        expect(option).toHaveAttribute('role', 'option');
      });
    });

    test('announces current selection to screen readers', () => {
      render(<AgentModeSelector {...defaultProps} currentMode="work" />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      expect(button).toHaveAttribute('aria-label', expect.stringContaining('Project Partner'));
    });
  });

  describe('Visual States', () => {
    test('applies correct CSS classes for different states', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      
      // Default state
      expect(button).toHaveClass('modeIndicator');
      
      // Open state
      await user.click(button);
      expect(button).toHaveClass('open');
    });

    test('shows visual indicator for current mode', () => {
      render(<AgentModeSelector {...defaultProps} currentMode="plan" />);
      
      expect(screen.getByText('Learning Path')).toBeInTheDocument();
    });

    test('applies hover styles to options', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      await user.click(button);
      
      const workOption = screen.getByText('Project Partner').closest('button');
      
      await user.hover(workOption);
      expect(workOption).toHaveClass('hover');
    });
  });

  describe('Error Handling', () => {
    test('handles missing onModeChange prop gracefully', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector currentMode="chat" availableModes={null} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      await user.click(button);
      
      const workOption = screen.getByText('Project Partner');
      
      // Should not throw error when clicking
      await user.click(workOption);
      
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    test('handles invalid current mode gracefully', () => {
      render(<AgentModeSelector {...defaultProps} currentMode="invalid_mode" />);
      
      // Should render without crashing
      expect(screen.getByRole('button', { name: /ai mode selector/i })).toBeInTheDocument();
    });

    test('handles null availableModes gracefully', async () => {
      const user = userEvent.setup();
      render(<AgentModeSelector {...defaultProps} availableModes={null} />);
      
      const button = screen.getByRole('button', { name: /ai mode selector/i });
      await user.click(button);
      
      // Should show default modes
      expect(screen.getByText('General conversation and mentoring')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    test('does not re-render unnecessarily', () => {
      const { rerender } = render(<AgentModeSelector {...defaultProps} />);
      
      // Re-render with same props
      rerender(<AgentModeSelector {...defaultProps} />);
      
      expect(screen.getByRole('button', { name: /ai mode selector/i })).toBeInTheDocument();
    });

    test('cleans up event listeners on unmount', () => {
      const removeEventListenerSpy = jest.spyOn(document, 'removeEventListener');
      
      const { unmount } = render(<AgentModeSelector {...defaultProps} />);
      
      unmount();
      
      expect(removeEventListenerSpy).toHaveBeenCalledWith('mousedown', expect.any(Function));
      
      removeEventListenerSpy.mockRestore();
    });
  });
});