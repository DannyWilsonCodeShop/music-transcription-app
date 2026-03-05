/**
 * Unit tests for KeyConfirmation component
 * Tests key confirmation, validation, and user interactions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { KeyConfirmation } from '../KeyConfirmation';
import * as transcriptionService from '../../services/transcriptionService';

// Mock the transcription service
vi.mock('../../services/transcriptionService', () => ({
  confirmKey: vi.fn(),
}));

describe('KeyConfirmation', () => {
  const mockJobId = 'test-job-123';
  const mockDetectedKey = 'C major';
  const mockKeyConfidence = 0.85;
  const mockOnKeyConfirmed = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render the component with title', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('Confirm Musical Key')).toBeInTheDocument();
    });

    it('should display detected key', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('C major')).toBeInTheDocument();
    });

    it('should display confidence percentage', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={0.85}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('85%')).toBeInTheDocument();
    });

    it('should display high confidence label for confidence >= 0.8', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={0.85}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('High')).toBeInTheDocument();
    });

    it('should display medium confidence label for confidence >= 0.5', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={0.65}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('Medium')).toBeInTheDocument();
    });

    it('should display low confidence label for confidence < 0.5', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={0.35}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('Low')).toBeInTheDocument();
    });

    it('should display timeout notice', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText(/Auto-confirms detected key in 5 minutes/)).toBeInTheDocument();
    });

    it('should display explanation of why key matters', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText(/Why does this matter?/)).toBeInTheDocument();
      expect(screen.getByText(/Nashville Numbers/)).toBeInTheDocument();
    });
  });

  describe('Key Selection', () => {
    it('should have detected key selected by default', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey="G major"
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      const select = screen.getByRole('combobox') as HTMLSelectElement;
      expect(select.value).toBe('G major');
    });

    it('should allow selecting different key', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey="C major"
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      const select = screen.getByRole('combobox') as HTMLSelectElement;
      fireEvent.change(select, { target: { value: 'A minor' } });

      expect(select.value).toBe('A minor');
    });

    it('should include all 24 keys in dropdown', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      const select = screen.getByRole('combobox');
      const options = select.querySelectorAll('option');

      // Should have 24 keys (12 major + 12 minor)
      expect(options.length).toBe(24);
    });

    it('should include major keys', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      const majorKeys = ['C major', 'G major', 'D major', 'A major', 'E major', 'B major'];
      
      majorKeys.forEach(key => {
        expect(screen.getByRole('option', { name: key })).toBeInTheDocument();
      });
    });

    it('should include minor keys', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      const minorKeys = ['A minor', 'E minor', 'B minor', 'F# minor', 'C# minor', 'G# minor'];
      
      minorKeys.forEach(key => {
        expect(screen.getByRole('option', { name: key })).toBeInTheDocument();
      });
    });
  });

  describe('Confirmation', () => {
    it('should call confirmKey with correct parameters', async () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmKey);
      mockConfirm.mockResolvedValue();

      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey="C major"
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      // Select different key
      const select = screen.getByRole('combobox');
      fireEvent.change(select, { target: { value: 'G major' } });

      // Click confirm
      const confirmButton = screen.getByText('Confirm Key');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockConfirm).toHaveBeenCalledWith(mockJobId, 'G major');
      });
    });

    it('should call onKeyConfirmed callback on successful confirmation', async () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmKey);
      mockConfirm.mockResolvedValue();

      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey="C major"
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      // Select different key
      const select = screen.getByRole('combobox');
      fireEvent.change(select, { target: { value: 'A minor' } });

      // Click confirm
      const confirmButton = screen.getByText('Confirm Key');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockOnKeyConfirmed).toHaveBeenCalledWith('A minor');
      });
    });

    it('should allow confirming detected key without change', async () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmKey);
      mockConfirm.mockResolvedValue();

      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey="C major"
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      // Don't change selection, just confirm
      const confirmButton = screen.getByText('Confirm Key');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockConfirm).toHaveBeenCalledWith(mockJobId, 'C major');
        expect(mockOnKeyConfirmed).toHaveBeenCalledWith('C major');
      });
    });

    it('should show loading state while submitting', async () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmKey);
      mockConfirm.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      const confirmButton = screen.getByText('Confirm Key');
      fireEvent.click(confirmButton);

      expect(screen.getByText('Confirming...')).toBeInTheDocument();
    });

    it('should disable buttons while submitting', async () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmKey);
      mockConfirm.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      const confirmButton = screen.getByText('Confirm Key');
      fireEvent.click(confirmButton);

      const cancelButton = screen.getByText('Cancel');
      const select = screen.getByRole('combobox');
      
      expect(cancelButton).toBeDisabled();
      expect(confirmButton).toBeDisabled();
      expect(select).toBeDisabled();
    });
  });

  describe('Error Handling', () => {
    it('should display error message on API failure', async () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmKey);
      mockConfirm.mockRejectedValue(new Error('API Error'));

      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      const confirmButton = screen.getByText('Confirm Key');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText('API Error')).toBeInTheDocument();
      });
    });

    it('should not call onKeyConfirmed on error', async () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmKey);
      mockConfirm.mockRejectedValue(new Error('API Error'));

      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      const confirmButton = screen.getByText('Confirm Key');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText('API Error')).toBeInTheDocument();
      });

      expect(mockOnKeyConfirmed).not.toHaveBeenCalled();
    });

    it('should re-enable buttons after error', async () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmKey);
      mockConfirm.mockRejectedValue(new Error('API Error'));

      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      const confirmButton = screen.getByText('Confirm Key');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText('API Error')).toBeInTheDocument();
      });

      expect(confirmButton).not.toBeDisabled();
    });
  });

  describe('Cancel Functionality', () => {
    it('should call onCancel when cancel button is clicked', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalled();
    });

    it('should not call confirmKey when cancelled', () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmKey);

      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);

      expect(mockConfirm).not.toHaveBeenCalled();
    });
  });

  describe('Confidence Display', () => {
    it('should format confidence as percentage', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={0.7543}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    it('should handle 100% confidence', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={1.0}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('100%')).toBeInTheDocument();
      expect(screen.getByText('High')).toBeInTheDocument();
    });

    it('should handle 0% confidence', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={0.0}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('0%')).toBeInTheDocument();
      expect(screen.getByText('Low')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper select role', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('should have proper button roles', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBe(2); // Confirm and Cancel
    });

    it('should be keyboard navigable', () => {
      render(
        <KeyConfirmation
          jobId={mockJobId}
          detectedKey={mockDetectedKey}
          keyConfidence={mockKeyConfidence}
          onKeyConfirmed={mockOnKeyConfirmed}
          onCancel={mockOnCancel}
        />
      );

      const select = screen.getByRole('combobox');
      select.focus();
      expect(document.activeElement).toBe(select);
    });
  });
});
