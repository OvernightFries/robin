import { QueryResponse, InitializeTickerResponse } from '@/types';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const TIMEOUT = 10000; // 10 seconds
const MAX_RETRIES = 2;

// Validate environment variables
if (!process.env.NEXT_PUBLIC_API_URL && process.env.NODE_ENV === 'production') {
  console.warn('NEXT_PUBLIC_API_URL environment variable not set in production');
}

export interface QueryRequest {
  query: string;
  symbol?: string;
}

// Specific error types for better error handling
export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// Helper function to validate numeric arrays
function isValidNumericArray(arr: any[]): boolean {
  return Array.isArray(arr) && arr.every(item => typeof item === 'number' && !isNaN(item));
}

// Helper function to validate date strings
function isValidDateArray(arr: any[]): boolean {
  return Array.isArray(arr) && arr.every(item => typeof item === 'string' && !isNaN(Date.parse(item)));
}

async function retryRequest<T>(request: () => Promise<T>, retries = MAX_RETRIES): Promise<T> {
  try {
    return await request();
  } catch (error) {
    if (retries > 0 && error instanceof Error && !error.message.includes('AbortError')) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      return retryRequest(request, retries - 1);
    }
    throw error;
  }
}

async function fetchWithTimeout(url: string, options: RequestInit, timeout = TIMEOUT): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
}

export async function query(
  query: string,
  symbol: string,
  signal?: AbortSignal
): Promise<QueryResponse> {
  const request = async () => {
    const response = await fetchWithTimeout(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, symbol }),
      signal
    });

    if (!response.ok) {
      const error = await response.json();
      throw new APIError(
        error.detail || 'Failed to process query',
        response.status,
        error
      );
    }

    const data = await response.json();
    console.log('Query response:', data); // Debug log

    return {
      status: data.status,
      response: data.response,
      market_context: data.market_context,
      knowledge_context: data.knowledge_context
    };
  };

  return retryRequest(request);
}

export async function initializeTicker(symbol: string, signal?: AbortSignal): Promise<InitializeTickerResponse> {
  const request = async () => {
    const response = await fetchWithTimeout(`${API_BASE_URL}/initialize_ticker`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ symbol }),
      signal
    });

    if (!response.ok) {
      const error = await response.json();
      throw new APIError(
        error.detail || 'Failed to initialize ticker',
        response.status,
        error
      );
    }

    const data = await response.json();
    console.log('Initialize ticker response:', data); // Debug log

    // Transform and validate daily data
    let daily_data = {
      dates: [] as string[],
      prices: [] as number[],
      volumes: [] as number[]
    };

    if (data.market_context?.daily_data) {
      const backend_daily = data.market_context.daily_data;

      // Ensure all required arrays exist and are arrays
      const dates = Array.isArray(backend_daily.dates) ? backend_daily.dates : [];
      const close = Array.isArray(backend_daily.close) ? backend_daily.close : [];
      const volume = Array.isArray(backend_daily.volume) ? backend_daily.volume : [];

      // Find the minimum length among all arrays
      const minLength = Math.min(dates.length, close.length, volume.length);

      // Trim all arrays to the minimum length and ensure they're valid
      daily_data = {
        dates: dates.slice(-minLength).filter((date: string) => isValidDateArray([date])),
        prices: close.slice(-minLength).filter((price: number) => isValidNumericArray([price])),
        volumes: volume.slice(-minLength).filter((vol: number) => isValidNumericArray([vol]))
      };

      // Ensure all arrays have the same length after filtering
      const finalLength = Math.min(
        daily_data.dates.length,
        daily_data.prices.length,
        daily_data.volumes.length
      );

      daily_data = {
        dates: daily_data.dates.slice(-finalLength),
        prices: daily_data.prices.slice(-finalLength),
        volumes: daily_data.volumes.slice(-finalLength)
      };
    }

    // Validate the transformed data
    if (daily_data.dates.length === 0 ||
      daily_data.prices.length === 0 ||
      daily_data.volumes.length === 0) {
      throw new APIError('No valid daily data available', 400);
    }

    return {
      status: data.status,
      message: data.message,
      market_context: {
        ...data.market_context,
        symbol: symbol.toUpperCase(),
        daily_data
      },
      options_context: data.options_context
    };
  };

  return retryRequest(request);
} 
