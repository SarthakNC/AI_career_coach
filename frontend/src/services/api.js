/**
 * API Service for CareerProof AI
 * Centralized HTTP request handling using Fetch API.
 */

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '')

/**
 * Perform a real health check request to GET /health
 * @returns {Promise<{status: string, message: string, latencyMs: number, timestamp: string}>}
 */
export async function checkBackendHealth() {
  const startTime = performance.now()
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    })

    const latencyMs = Math.round(performance.now() - startTime)

    if (!response.ok) {
      throw new Error(`Backend returned HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()
    return {
      ...data,
      latencyMs,
      timestamp: new Date().toLocaleTimeString(),
    }
  } catch (error) {
    const latencyMs = Math.round(performance.now() - startTime)
    throw {
      message: error.message || 'Unable to connect to backend service',
      latencyMs,
      timestamp: new Date().toLocaleTimeString(),
    }
  }
}

/**
 * Fetch detailed system status from GET /api/v1/status
 * @returns {Promise<{app_name: string, version: string, environment: string, database: {status: string, configured: boolean, message: string}}>}
 */
export async function getSystemStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/status`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Status endpoint returned HTTP ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    return {
      app_name: 'CareerProof AI API',
      version: 'Unknown',
      environment: 'Unknown',
      database: {
        status: 'error',
        configured: false,
        message: error.message || 'Failed to reach status endpoint',
      },
    }
  }
}

export { API_BASE_URL }