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

/**
 * Analyze a job posting URL or pasted description.
 * @param {Object} payload { job_url, pasted_description, job_title, company_name }
 * @param {string} token Supabase access token
 * @returns {Promise<Object>} Saved job analysis record
 */
export async function analyzeJob(payload, token) {
  if (!token) {
    throw new Error('Authentication required. Please log in.')
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    let errorDetail = `Analysis failed with HTTP ${response.status}`
    try {
      const errJson = await response.json()
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail)
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail)
  }

  return await response.json()
}

/**
 * List all saved job analyses for current authenticated user.
 * @param {string} token Supabase access token
 * @returns {Promise<Array>} List of job summaries
 */
export async function listSavedJobs(token) {
  if (!token) {
    throw new Error('Authentication required. Please log in.')
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/jobs`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let errorDetail = `Failed to fetch jobs (HTTP ${response.status})`
    try {
      const errJson = await response.json()
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail)
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail)
  }

  return await response.json()
}

/**
 * Get details for a single job analysis including requirements.
 * @param {string} jobId UUID
 * @param {string} token Supabase access token
 * @returns {Promise<Object>} Job details with requirements
 */
export async function getJobDetails(jobId, token) {
  if (!token) {
    throw new Error('Authentication required. Please log in.')
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let errorDetail = `Failed to load job details (HTTP ${response.status})`
    try {
      const errJson = await response.json()
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail)
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail)
  }

  return await response.json()
}

/**
 * Delete a saved job analysis.
 * @param {string} jobId UUID
 * @param {string} token Supabase access token
 * @returns {Promise<void>}
 */
export async function deleteSavedJob(jobId, token) {
  if (!token) {
    throw new Error('Authentication required. Please log in.')
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/${jobId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok && response.status !== 204) {
    let errorDetail = `Failed to delete job (HTTP ${response.status})`
    try {
      const errJson = await response.json()
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail)
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail)
  }
}

export { API_BASE_URL }