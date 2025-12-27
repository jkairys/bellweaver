import type {
  UserDetailsResponse,
  EventsResponse,
  WeeklySummaryRequest,
  WeeklySummaryResponse,
} from '../types/api';

const API_BASE_URL = '/api';

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function fetchApi<T>(endpoint: string): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);

    if (!response.ok) {
      throw new ApiError(
        `API request failed: ${response.statusText}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(`Network error: ${(error as Error).message}`, 0);
  }
}

async function postApi<T, R>(endpoint: string, data: T): Promise<R> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.message || `API request failed: ${response.statusText}`,
        response.status
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(`Network error: ${(error as Error).message}`, 0);
  }
}

export async function getUserDetails(): Promise<UserDetailsResponse> {
  return fetchApi<UserDetailsResponse>('/user');
}

export async function getEvents(): Promise<EventsResponse> {
  return fetchApi<EventsResponse>('/events');
}

export async function getWeeklySummary(
  weekStart: string
): Promise<WeeklySummaryResponse> {
  return postApi<WeeklySummaryRequest, WeeklySummaryResponse>(
    '/summary/weekly',
    { week_start: weekStart }
  );
}
