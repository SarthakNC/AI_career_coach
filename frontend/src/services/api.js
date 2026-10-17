/**
 * API Service for Parivartan AI
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
      app_name: 'Parivartan AI API',
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
 * Upload and extract job description text from a digital or scanned PDF.
 * @param {File} file PDF file object
 * @param {string} token Supabase access token
 * @returns {Promise<{success: boolean, extracted_text: string, page_count: number, extraction_method: string, ocr_pages: number[], warnings: string[], detected_job_title?: string, detected_company_name?: string}>}
 */
export async function extractPdfJobDescription(file, token) {
  if (!token) {
    throw new Error('Authentication required. Please log in.')
  }

  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/extract-pdf`, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  })

  if (!response.ok) {
    let errorDetail = `PDF extraction failed with HTTP ${response.status}`
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
 * Submit user-confirmed extracted job description text for requirement analysis.
 * @param {Object} payload { extracted_text, job_title, company_name }
 * @param {string} token Supabase access token
 * @returns {Promise<Object>} Saved job analysis record
 */
export async function analyzeExtractedText(payload, token) {
  if (!token) {
    throw new Error('Authentication required. Please log in.')
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/jobs/analyze-extracted-text`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    let errorDetail = `Requirement analysis failed with HTTP ${response.status}`
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

/**
 * ─────────────────────────────────────────────────────────────
 * GitHub Portfolio API Client
 * ─────────────────────────────────────────────────────────────
 */

export async function resolveGitHub(query, token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/github/repositories/resolve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ query }),
  })

  if (!response.ok) {
    let err = `Failed to resolve GitHub identifier (HTTP ${response.status})`
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
  return await response.json()
}

export async function listUserRepositories(token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/github/repositories`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let err = 'Failed to load portfolio repositories'
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
  return await response.json()
}

export async function addRepositoryToPortfolio(repoData, token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/github/repositories`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(repoData),
  })

  if (!response.ok) {
    let err = 'Failed to add repository'
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
  return await response.json()
}

export async function analyzeRepository(repoId, token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/github/repositories/${repoId}/analyze`, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let err = 'Analysis failed'
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
  return await response.json()
}

export async function getRepositoryAnalysis(repoId, token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/github/repositories/${repoId}/analysis`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    if (response.status === 404) return null
    let err = 'Failed to fetch analysis'
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
  return await response.json()
}

export async function deleteUserRepository(repoId, token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/github/repositories/${repoId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok && response.status !== 204) {
    let err = 'Failed to delete repository'
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
}

export async function getPortfolioSummary(token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/github/portfolio-summary`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    return {
      total_repositories: 0,
      analyzed_repositories: 0,
      total_skills_detected: 0,
      latest_analyzed_at: null,
    }
  }
  return await response.json()
}

/**
 * ─────────────────────────────────────────────────────────────
 * AI-Powered Skill-Gap Assessment API
 * ─────────────────────────────────────────────────────────────
 */

export async function getAssessmentOptions(token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/assessments/options`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let err = 'Failed to fetch assessment options'
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
  return await response.json()
}

export async function createAssessment({ jobId, repositoryIds }, token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/assessments`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      job_id: jobId,
      repository_ids: repositoryIds,
    }),
  })

  if (!response.ok) {
    let err = 'Assessment generation failed'
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
  return await response.json()
}

export async function listAssessments(token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/assessments`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let err = 'Failed to fetch assessments'
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
  return await response.json()
}

export async function getAssessmentById(assessmentId, token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/assessments/${assessmentId}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let err = 'Failed to retrieve assessment details'
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
  return await response.json()
}

export async function deleteAssessment(assessmentId, token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/assessments/${assessmentId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok && response.status !== 204) {
    let err = 'Failed to delete assessment'
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
}

/**
 * Fetch GitHub repository monitoring status and overview.
 * @param {string} token
 * @returns {Promise<Object>}
 */
export async function getMonitoringStatus(token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/github/monitoring/status`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let err = 'Failed to fetch monitoring status'
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
  return await response.json()
}

/**
 * Phase 8: Trigger an immediate commit sync check for a single repository.
 * @param {string} repositoryId
 * @param {string} token
 * @returns {Promise<Object>}
 */
export async function syncRepository(repositoryId, token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/github/repositories/${repositoryId}/sync`, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let err = 'Repository sync failed'
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
  return await response.json()
}

/**
 * Phase 8: List persisted repository change events.
 * @param {string} token
 * @param {number} limit
 * @returns {Promise<{events: Array, total: number}>}
 */
export async function listChangeEvents(token, limit = 20) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/github/changes?limit=${limit}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let err = 'Failed to load change events'
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
  return await response.json()
}

/**
 * Phase 8: Get details of a specific change event.
 * @param {string} changeId
 * @param {string} token
 * @returns {Promise<Object>}
 */
export async function getChangeEventById(changeId, token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/github/changes/${changeId}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let err = 'Failed to load change event details'
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
  return await response.json()
}

/**
 * Phase 8: Retry a failed change event.
 * @param {string} changeId
 * @param {string} token
 * @returns {Promise<Object>}
 */
export async function retryChangeEvent(changeId, token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/github/changes/${changeId}/retry`, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let err = 'Retry failed'
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
  return await response.json()
}

/**
 * Phase 8: Get version history/lineage of an assessment.
 * @param {string} assessmentId
 * @param {string} token
 * @returns {Promise<{assessment_id: string, job_title: string, company_name: string, current_version: number, versions: Array}>}
 */
export async function getAssessmentHistory(assessmentId, token) {
  if (!token) throw new Error('Authentication required.')

  const response = await fetch(`${API_BASE_URL}/api/v1/assessments/${assessmentId}/history`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    let err = 'Failed to load assessment version history'
    try {
      const data = await response.json()
      if (data.detail) err = data.detail
    } catch {}
    throw new Error(err)
  }
  return await response.json()
}

export { API_BASE_URL }

