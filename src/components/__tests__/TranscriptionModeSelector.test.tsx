/**
 * Unit tests for TranscriptionModeSelector component
 * Tests mode selection, validation, and user interactions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TranscriptionModeSelector } from '../TranscriptionModeSelector';
import * as transcriptionService from '../../services/transcriptionService';

// Mock the transcription service
vi.mock('../../services/transcriptionService', () => ({
  confirmTranscriptionMode: vi.fn(),
}));

describe('TranscriptionModeSelector', () => {
  const mockJobId = 'test-job-123';
  const mockOnModeSelected = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render the component with title', () => {
      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('Select Transcription Mode')).toBeInTheDocument();
    });

    it('should render all four mode options', () => {
      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('Bass Only')).toBeInTheDocument();
      expect(screen.getByText('Bass + Piano')).toBeInTheDocument();
      expect(screen.getByText('Bass + Guitar')).toBeInTheDocument();
      expect(screen.getByText('All Instruments')).toBeInTheDocument();
    });

    it('should display processing time estimates', () => {
      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText(/~3 min/)).toBeInTheDocument();
      expect(screen.getByText(/~5 min/)).toBeInTheDocument();
      expect(screen.getByText(/~8 min/)).toBeInTheDocument();
    });

    it('should display timeout notice', () => {
      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText(/Auto-selects "Bass Only" in 5 minutes/)).toBeInTheDocument();
    });

    it('should have bass-only selected by default', () => {
      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      const bassOnlyButton = screen.getByText('Bass Only').closest('button');
      expect(bassOnlyButton).toHaveClass('border-blue-500');
    });
  });

  describe('Mode Selection', () => {
    it('should allow selecting bass-only mode', async () => {
      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      const bassOnlyButton = screen.getByText('Bass Only').closest('button');
      fireEvent.click(bassOnlyButton!);

      expect(bassOnlyButton).toHaveClass('border-blue-500');
    });

    it('should allow selecting bass+piano mode', async () => {
      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      const pianoButton = screen.getByText('Bass + Piano').closest('button');
      fireEvent.click(pianoButton!);

      expect(pianoButton).toHaveClass('border-blue-500');
    });

    it('should allow selecting bass+guitar mode', async () => {
      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      const guitarButton = screen.getByText('Bass + Guitar').closest('button');
      fireEvent.click(guitarButton!);

      expect(guitarButton).toHaveClass('border-blue-500');
    });

    it('should allow selecting all instruments mode', async () => {
      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      const allButton = screen.getByText('All Instruments').closest('button');
      fireEvent.click(allButton!);

      expect(allButton).toHaveClass('border-blue-500');
    });

    it('should change selection when clicking different modes', async () => {
      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      // Initially bass-only is selected
      const bassOnlyButton = screen.getByText('Bass Only').closest('button');
      expect(bassOnlyButton).toHaveClass('border-blue-500');

      // Click piano mode
      const pianoButton = screen.getByText('Bass + Piano').closest('button');
      fireEvent.click(pianoButton!);

      // Piano should now be selected
      expect(pianoButton).toHaveClass('border-blue-500');
      expect(bassOnlyButton).not.toHaveClass('border-blue-500');
    });
  });

  describe('Confirmation', () => {
    it('should call confirmTranscriptionMode with correct parameters', async () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmTranscriptionMode);
      mockConfirm.mockResolvedValue();

      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      // Select bass+piano mode
      const pianoButton = screen.getByText('Bass + Piano').closest('button');
      fireEvent.click(pianoButton!);

      // Click confirm
      const confirmButton = screen.getByText('Confirm Selection');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockConfirm).toHaveBeenCalledWith(mockJobId, 'bass+piano');
      });
    });

    it('should call onModeSelected callback on successful confirmation', async () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmTranscriptionMode);
      mockConfirm.mockResolvedValue();

      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      // Select all mode
      const allButton = screen.getByText('All Instruments').closest('button');
      fireEvent.click(allButton!);

      // Click confirm
      const confirmButton = screen.getByText('Confirm Selection');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockOnModeSelected).toHaveBeenCalledWith('all');
      });
    });

    it('should show loading state while submitting', async () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmTranscriptionMode);
      mockConfirm.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      const confirmButton = screen.getByText('Confirm Selection');
      fireEvent.click(confirmButton);

      expect(screen.getByText('Confirming...')).toBeInTheDocument();
    });

    it('should disable buttons while submitting', async () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmTranscriptionMode);
      mockConfirm.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      const confirmButton = screen.getByText('Confirm Selection');
      fireEvent.click(confirmButton);

      const cancelButton = screen.getByText('Cancel');
      expect(cancelButton).toBeDisabled();
      expect(confirmButton).toBeDisabled();
    });
  });

  describe('Error Handling', () => {
    it('should display error message on API failure', async () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmTranscriptionMode);
      mockConfirm.mockRejectedValue(new Error('API Error'));

      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      const confirmButton = screen.getByText('Confirm Selection');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText('API Error')).toBeInTheDocument();
      });
    });

    it('should not call onModeSelected on error', async () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmTranscriptionMode);
      mockConfirm.mockRejectedValue(new Error('API Error'));

      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      const confirmButton = screen.getByText('Confirm Selection');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText('API Error')).toBeInTheDocument();
      });

      expect(mockOnModeSelected).not.toHaveBeenCalled();
    });

    it('should re-enable buttons after error', async () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmTranscriptionMode);
      mockConfirm.mockRejectedValue(new Error('API Error'));

      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      const confirmButton = screen.getByText('Confirm Selection');
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
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalled();
    });

    it('should not call confirmTranscriptionMode when cancelled', () => {
      const mockConfirm = vi.mocked(transcriptionService.confirmTranscriptionMode);

      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);

      expect(mockConfirm).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have proper button roles', () => {
      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('should be keyboard navigable', () => {
      render(
        <TranscriptionModeSelector
          jobId={mockJobId}
          onModeSelected={mockOnModeSelected}
          onCancel={mockOnCancel}
        />
      );

      const confirmButton = screen.getByText('Confirm Selection');
      confirmButton.focus();
      expect(document.activeElement).toBe(confirmButton);
    });
  });
});
