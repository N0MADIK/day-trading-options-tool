/**
 * API Client for communicating with the FastAPI backend.
 * 
 * Features:
 * - Automatic Authorization header injection from localStorage token
 * - Global 401 error handling with auto-logout
 * - Type-safe request/response handling
 */

// When VITE_API_URL is empty/unset (Docker), use relative /api/v1 path (nginx proxy)
// For local dev, set VITE_API_URL=http://localhost:8420/api/v1
const API_URL = import.meta.env.VITE_API_URL || '/api/v1';
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

interface ApiError extends Error {
    status?: number;
    data?: unknown;
}

function createApiError(message: string, status?: number, data?: unknown): ApiError {
    const error = new Error(message) as ApiError;
    error.status = status;
    error.data = data;
    return error;
}

function getAuthToken(): string | null {
    const session = localStorage.getItem('auth_session');
    if (!session) return null;

    try {
        const parsed = JSON.parse(session);
        return parsed.access_token || null;
    } catch {
        return null;
    }
}

function clearSession(): void {
    localStorage.removeItem('auth_session');
    localStorage.removeItem('user');
}

async function handleUnauthorized(): Promise<void> {
    clearSession();
    // Trigger a page reload to redirect to login
    window.location.href = '/auth';
}

interface RequestOptions extends Omit<RequestInit, 'body'> {
    body?: unknown;
    skipAuth?: boolean;
}

async function request<T>(
    endpoint: string,
    options: RequestOptions = {}
): Promise<T> {
    const { body, skipAuth = false, ...restOptions } = options;

    const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...restOptions.headers,
    };

    // Inject Authorization header if token exists and not skipped
    if (!skipAuth) {
        const token = getAuthToken();
        if (token) {
            (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
        }
    }

    const config: RequestInit = {
        ...restOptions,
        headers,
    };

    if (body !== undefined) {
        // Don't stringify if body is already a string (e.g., form-urlencoded data)
        config.body = typeof body === 'string' ? body : JSON.stringify(body);
    }

    const url = `${API_URL}${endpoint}`;

    try {
        const response = await fetch(url, config);

        // Handle 401 Unauthorized - auto logout
        if (response.status === 401) {
            await handleUnauthorized();
            throw createApiError('Unauthorized - Session expired', 401);
        }

        // Try to parse response as JSON
        let data: T;
        const contentType = response.headers.get('content-type');
        if (contentType?.includes('application/json')) {
            data = await response.json();
        } else {
            data = await response.text() as unknown as T;
        }

        if (!response.ok) {
            const errorMessage =
                (data as { detail?: string })?.detail ||
                (data as { message?: string })?.message ||
                `Request failed with status ${response.status}`;
            throw createApiError(errorMessage, response.status, data);
        }

        return data;
    } catch (error) {
        if (error instanceof Error && 'status' in error) {
            throw error;
        }
        throw createApiError(
            error instanceof Error ? error.message : 'Network error',
            undefined
        );
    }
}

export const api = {
    get: <T>(endpoint: string, options?: RequestOptions) =>
        request<T>(endpoint, { ...options, method: 'GET' }),

    post: <T>(endpoint: string, body?: unknown, options?: RequestOptions) =>
        request<T>(endpoint, { ...options, method: 'POST', body }),

    put: <T>(endpoint: string, body?: unknown, options?: RequestOptions) =>
        request<T>(endpoint, { ...options, method: 'PUT', body }),

    patch: <T>(endpoint: string, body?: unknown, options?: RequestOptions) =>
        request<T>(endpoint, { ...options, method: 'PATCH', body }),

    delete: <T>(endpoint: string, options?: RequestOptions) =>
        request<T>(endpoint, { ...options, method: 'DELETE' }),
};

// Export utilities for use in auth
export { getAuthToken, clearSession };
