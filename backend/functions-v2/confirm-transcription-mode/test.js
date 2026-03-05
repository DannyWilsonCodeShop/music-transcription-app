/**
 * Unit tests for confirm-transcription-mode Lambda function
 * Tests validation, DynamoDB updates, and error handling
 */

const { handler } = require('./index');

// Mock AWS SDK
const mockGet = jest.fn();
const mockUpdate = jest.fn();

jest.mock('aws-sdk', () => {
  return {
    DynamoDB: {
      DocumentClient: jest.fn(() => ({
        get: mockGet,
        update: mockUpdate
      }))
    }
  };
});

describe('confirm-transcription-mode Lambda', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    
    // Set default environment
    process.env.DYNAMODB_TABLE = 'ChordScout-Jobs-V2-test';
  });

  describe('Input Validation', () => {
    test('should return 400 when jobId is missing', async () => {
      const event = {
        pathParameters: {},
        body: JSON.stringify({ transcriptionMode: 'bass-only' })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(400);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(false);
      expect(body.error).toContain('Missing jobId');
    });

    test('should return 400 when body is invalid JSON', async () => {
      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: 'invalid json{'
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(400);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(false);
      expect(body.error).toContain('Invalid JSON');
    });

    test('should return 400 when transcriptionMode is missing', async () => {
      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({})
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(400);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(false);
      expect(body.error).toContain('Missing transcriptionMode');
    });

    test('should return 400 when transcriptionMode is invalid', async () => {
      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ transcriptionMode: 'invalid-mode' })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(400);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(false);
      expect(body.error).toContain('Invalid transcriptionMode');
    });

    test('should accept bass-only mode', async () => {
      mockGet.mockReturnValue({
        promise: () => Promise.resolve({
          Item: { jobId: 'test-job-123', status: 'PENDING_MODE_SELECTION' }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.resolve({
          Attributes: { jobId: 'test-job-123', transcriptionMode: 'bass-only' }
        })
      });

      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ transcriptionMode: 'bass-only' })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(true);
    });

    test('should accept bass+piano mode', async () => {
      mockGet.mockReturnValue({
        promise: () => Promise.resolve({
          Item: { jobId: 'test-job-123', status: 'PENDING_MODE_SELECTION' }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.resolve({
          Attributes: { jobId: 'test-job-123', transcriptionMode: 'bass+piano' }
        })
      });

      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ transcriptionMode: 'bass+piano' })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(200);
    });

    test('should accept bass+guitar mode', async () => {
      mockGet.mockReturnValue({
        promise: () => Promise.resolve({
          Item: { jobId: 'test-job-123', status: 'PENDING_MODE_SELECTION' }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.resolve({
          Attributes: { jobId: 'test-job-123', transcriptionMode: 'bass+guitar' }
        })
      });

      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ transcriptionMode: 'bass+guitar' })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(200);
    });

    test('should accept all mode', async () => {
      mockGet.mockReturnValue({
        promise: () => Promise.resolve({
          Item: { jobId: 'test-job-123', status: 'PENDING_MODE_SELECTION' }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.resolve({
          Attributes: { jobId: 'test-job-123', transcriptionMode: 'all' }
        })
      });

      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ transcriptionMode: 'all' })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(200);
    });
  });

  describe('DynamoDB Operations', () => {
    test('should return 404 when job not found', async () => {
      mockGet.mockReturnValue({
        promise: () => Promise.resolve({ Item: null })
      });

      const event = {
        pathParameters: { jobId: 'nonexistent-job' },
        body: JSON.stringify({ transcriptionMode: 'bass-only' })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(404);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(false);
      expect(body.error).toContain('Job not found');
    });

    test('should update job with transcriptionMode', async () => {
      const jobId = 'test-job-123';
      const mode = 'bass+piano';

      mockGet.mockReturnValue({
        promise: () => Promise.resolve({
          Item: { jobId, status: 'PENDING_MODE_SELECTION' }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.resolve({
          Attributes: { jobId, transcriptionMode: mode }
        })
      });

      const event = {
        pathParameters: { jobId },
        body: JSON.stringify({ transcriptionMode: mode })
      };

      const response = await handler(event);

      expect(mockUpdate).toHaveBeenCalledWith(
        expect.objectContaining({
          TableName: 'ChordScout-Jobs-V2-test',
          Key: { jobId },
          UpdateExpression: expect.stringContaining('transcriptionMode'),
          ExpressionAttributeValues: expect.objectContaining({
            ':mode': mode
          })
        })
      );

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.transcriptionMode).toBe(mode);
    });

    test('should update updatedAt timestamp', async () => {
      mockGet.mockReturnValue({
        promise: () => Promise.resolve({
          Item: { jobId: 'test-job-123' }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.resolve({
          Attributes: { jobId: 'test-job-123' }
        })
      });

      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ transcriptionMode: 'bass-only' })
      };

      await handler(event);

      expect(mockUpdate).toHaveBeenCalledWith(
        expect.objectContaining({
          UpdateExpression: expect.stringContaining('updatedAt'),
          ExpressionAttributeValues: expect.objectContaining({
            ':updatedAt': expect.any(String)
          })
        })
      );
    });
  });

  describe('Error Handling', () => {
    test('should return 500 on DynamoDB get error', async () => {
      mockGet.mockReturnValue({
        promise: () => Promise.reject(new Error('DynamoDB error'))
      });

      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ transcriptionMode: 'bass-only' })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(500);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(false);
      expect(body.error).toBe('Internal server error');
    });

    test('should return 500 on DynamoDB update error', async () => {
      mockGet.mockReturnValue({
        promise: () => Promise.resolve({
          Item: { jobId: 'test-job-123' }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.reject(new Error('Update failed'))
      });

      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ transcriptionMode: 'bass-only' })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(500);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(false);
    });
  });

  describe('CORS Headers', () => {
    test('should include CORS headers in response', async () => {
      mockGet.mockReturnValue({
        promise: () => Promise.resolve({
          Item: { jobId: 'test-job-123' }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.resolve({
          Attributes: { jobId: 'test-job-123' }
        })
      });

      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ transcriptionMode: 'bass-only' })
      };

      const response = await handler(event);

      expect(response.headers).toHaveProperty('Access-Control-Allow-Origin', '*');
      expect(response.headers).toHaveProperty('Access-Control-Allow-Headers');
      expect(response.headers).toHaveProperty('Access-Control-Allow-Methods');
    });
  });

  describe('Response Format', () => {
    test('should return success response with correct format', async () => {
      const jobId = 'test-job-123';
      const mode = 'bass+guitar';

      mockGet.mockReturnValue({
        promise: () => Promise.resolve({
          Item: { jobId }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.resolve({
          Attributes: { jobId, transcriptionMode: mode }
        })
      });

      const event = {
        pathParameters: { jobId },
        body: JSON.stringify({ transcriptionMode: mode })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body).toEqual({
        success: true,
        jobId,
        transcriptionMode: mode,
        message: 'Transcription mode confirmed'
      });
    });
  });
});
