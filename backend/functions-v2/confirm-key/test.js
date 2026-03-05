/**
 * Unit tests for confirm-key Lambda function
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

describe('confirm-key Lambda', () => {
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
        body: JSON.stringify({ confirmedKey: 'C major' })
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

    test('should return 400 when confirmedKey is missing', async () => {
      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({})
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(400);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(false);
      expect(body.error).toContain('Missing confirmedKey');
    });

    test('should return 400 when key format is invalid', async () => {
      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ confirmedKey: 'Invalid Key' })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(400);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(false);
      expect(body.error).toContain('Invalid key format');
    });

    test('should accept all 12 major keys', async () => {
      const majorKeys = [
        'C major', 'C# major', 'Db major', 'D major', 'Eb major', 'E major',
        'F major', 'F# major', 'Gb major', 'G major', 'Ab major', 'A major',
        'Bb major', 'B major'
      ];

      for (const key of majorKeys) {
        mockGet.mockReturnValue({
          promise: () => Promise.resolve({
            Item: { jobId: 'test-job-123', detectedKey: 'C major' }
          })
        });

        mockUpdate.mockReturnValue({
          promise: () => Promise.resolve({
            Attributes: { jobId: 'test-job-123', confirmedKey: key }
          })
        });

        const event = {
          pathParameters: { jobId: 'test-job-123' },
          body: JSON.stringify({ confirmedKey: key })
        };

        const response = await handler(event);

        expect(response.statusCode).toBe(200);
        const body = JSON.parse(response.body);
        expect(body.confirmedKey).toBe(key);
      }
    });

    test('should accept all 12 minor keys', async () => {
      const minorKeys = [
        'C minor', 'C# minor', 'Db minor', 'D minor', 'Eb minor', 'E minor',
        'F minor', 'F# minor', 'Gb minor', 'G minor', 'Ab minor', 'A minor',
        'Bb minor', 'B minor'
      ];

      for (const key of minorKeys) {
        mockGet.mockReturnValue({
          promise: () => Promise.resolve({
            Item: { jobId: 'test-job-123', detectedKey: 'A minor' }
          })
        });

        mockUpdate.mockReturnValue({
          promise: () => Promise.resolve({
            Attributes: { jobId: 'test-job-123', confirmedKey: key }
          })
        });

        const event = {
          pathParameters: { jobId: 'test-job-123' },
          body: JSON.stringify({ confirmedKey: key })
        };

        const response = await handler(event);

        expect(response.statusCode).toBe(200);
        const body = JSON.parse(response.body);
        expect(body.confirmedKey).toBe(key);
      }
    });

    test('should reject key without mode (major/minor)', async () => {
      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ confirmedKey: 'C' })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(400);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(false);
    });

    test('should reject key with wrong case', async () => {
      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ confirmedKey: 'c Major' })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(400);
    });
  });

  describe('DynamoDB Operations', () => {
    test('should return 404 when job not found', async () => {
      mockGet.mockReturnValue({
        promise: () => Promise.resolve({ Item: null })
      });

      const event = {
        pathParameters: { jobId: 'nonexistent-job' },
        body: JSON.stringify({ confirmedKey: 'C major' })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(404);
      const body = JSON.parse(response.body);
      expect(body.success).toBe(false);
      expect(body.error).toContain('Job not found');
    });

    test('should update job with confirmedKey', async () => {
      const jobId = 'test-job-123';
      const key = 'G major';

      mockGet.mockReturnValue({
        promise: () => Promise.resolve({
          Item: { jobId, detectedKey: 'C major' }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.resolve({
          Attributes: { jobId, confirmedKey: key }
        })
      });

      const event = {
        pathParameters: { jobId },
        body: JSON.stringify({ confirmedKey: key })
      };

      const response = await handler(event);

      expect(mockUpdate).toHaveBeenCalledWith(
        expect.objectContaining({
          TableName: 'ChordScout-Jobs-V2-test',
          Key: { jobId },
          UpdateExpression: expect.stringContaining('confirmedKey'),
          ExpressionAttributeValues: expect.objectContaining({
            ':key': key
          })
        })
      );

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.confirmedKey).toBe(key);
    });

    test('should update updatedAt timestamp', async () => {
      mockGet.mockReturnValue({
        promise: () => Promise.resolve({
          Item: { jobId: 'test-job-123', detectedKey: 'C major' }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.resolve({
          Attributes: { jobId: 'test-job-123' }
        })
      });

      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ confirmedKey: 'C major' })
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

    test('should return detectedKey in response', async () => {
      const jobId = 'test-job-123';
      const detectedKey = 'D major';
      const confirmedKey = 'D minor';

      mockGet.mockReturnValue({
        promise: () => Promise.resolve({
          Item: { jobId, detectedKey }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.resolve({
          Attributes: { jobId, confirmedKey }
        })
      });

      const event = {
        pathParameters: { jobId },
        body: JSON.stringify({ confirmedKey })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.detectedKey).toBe(detectedKey);
      expect(body.confirmedKey).toBe(confirmedKey);
    });

    test('should handle missing detectedKey gracefully', async () => {
      mockGet.mockReturnValue({
        promise: () => Promise.resolve({
          Item: { jobId: 'test-job-123' }  // No detectedKey
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.resolve({
          Attributes: { jobId: 'test-job-123' }
        })
      });

      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ confirmedKey: 'C major' })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.detectedKey).toBe('Unknown');
    });
  });

  describe('Error Handling', () => {
    test('should return 500 on DynamoDB get error', async () => {
      mockGet.mockReturnValue({
        promise: () => Promise.reject(new Error('DynamoDB error'))
      });

      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ confirmedKey: 'C major' })
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
          Item: { jobId: 'test-job-123', detectedKey: 'C major' }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.reject(new Error('Update failed'))
      });

      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ confirmedKey: 'C major' })
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
          Item: { jobId: 'test-job-123', detectedKey: 'C major' }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.resolve({
          Attributes: { jobId: 'test-job-123' }
        })
      });

      const event = {
        pathParameters: { jobId: 'test-job-123' },
        body: JSON.stringify({ confirmedKey: 'C major' })
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
      const detectedKey = 'C major';
      const confirmedKey = 'G major';

      mockGet.mockReturnValue({
        promise: () => Promise.resolve({
          Item: { jobId, detectedKey }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.resolve({
          Attributes: { jobId, confirmedKey }
        })
      });

      const event = {
        pathParameters: { jobId },
        body: JSON.stringify({ confirmedKey })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body).toEqual({
        success: true,
        jobId,
        detectedKey,
        confirmedKey,
        message: 'Key confirmed'
      });
    });
  });

  describe('Key Correction Workflow', () => {
    test('should allow user to correct detected key', async () => {
      const jobId = 'test-job-123';
      const detectedKey = 'C major';  // System detected C major
      const confirmedKey = 'A minor';  // User corrects to A minor

      mockGet.mockReturnValue({
        promise: () => Promise.resolve({
          Item: { jobId, detectedKey }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.resolve({
          Attributes: { jobId, confirmedKey }
        })
      });

      const event = {
        pathParameters: { jobId },
        body: JSON.stringify({ confirmedKey })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.detectedKey).toBe(detectedKey);
      expect(body.confirmedKey).toBe(confirmedKey);
      expect(body.detectedKey).not.toBe(body.confirmedKey);
    });

    test('should allow user to confirm detected key', async () => {
      const jobId = 'test-job-123';
      const key = 'G major';  // Same for both detected and confirmed

      mockGet.mockReturnValue({
        promise: () => Promise.resolve({
          Item: { jobId, detectedKey: key }
        })
      });

      mockUpdate.mockReturnValue({
        promise: () => Promise.resolve({
          Attributes: { jobId, confirmedKey: key }
        })
      });

      const event = {
        pathParameters: { jobId },
        body: JSON.stringify({ confirmedKey: key })
      };

      const response = await handler(event);

      expect(response.statusCode).toBe(200);
      const body = JSON.parse(response.body);
      expect(body.detectedKey).toBe(key);
      expect(body.confirmedKey).toBe(key);
    });
  });
});
