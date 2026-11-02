import { describe, expect, it } from 'vitest';
import { extractErrorMessage } from './authErrors';

describe('extractErrorMessage', () => {
  it('explains network failures instead of a generic registration message', () => {
    const message = extractErrorMessage(
      { message: 'Network Error', code: 'ERR_NETWORK' },
      'Registration failed. Please check form inputs.'
    );
    expect(message).toMatch(/Unable to connect/i);
  });

  it('surfaces Django field errors', () => {
    const message = extractErrorMessage({
      response: {
        status: 400,
        data: { email: ['user with this email already exists.'] },
      },
    });
    expect(message).toBe('Email: user with this email already exists.');
  });

  it('maps invalid login credentials', () => {
    const message = extractErrorMessage({
      response: {
        status: 401,
        data: { detail: 'No active account found with the given credentials' },
      },
    });
    expect(message).toBe('Invalid email or password.');
  });

  it('does not expose HTML 500 bodies', () => {
    const message = extractErrorMessage({
      response: {
        status: 500,
        data: '<html><body>Traceback</body></html>',
      },
    });
    expect(message).toMatch(/Server error \(500\)/);
    expect(message).not.toMatch(/Traceback/);
  });
});
