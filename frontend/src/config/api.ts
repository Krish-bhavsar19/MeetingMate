// API Configuration
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// API endpoints
export const API_ENDPOINTS = {
  // Auth
  LOGIN: '/api/auth/login',
  REGISTER: '/api/auth/register',
  ME: '/api/auth/me',
  
  // Meetings
  MEETINGS: '/api/meetings',
  MEETING_DETAIL: (id: string) => `/api/meetings/${id}`,
  
  // Transcription
  TRANSCRIBE_MEETING: (id: string) => `/api/transcription/transcribe/${id}`,
  TRANSCRIBE_FILE: '/api/transcription/transcribe-file',
  TRANSCRIPT: (id: string) => `/api/transcription/${id}/transcript`,
  
  // Summarization
  SUMMARIZE_MEETING: (id: string) => `/api/summarization/summarize/${id}`,
  SUMMARIZE_TEXT: '/api/summarization/summarize-text',
  SUMMARY: (id: string) => `/api/summarization/${id}/summary`,
  
  // Tasks/Action Items
  EXTRACT_TASKS: (id: string) => `/api/tasks/extract/${id}`,
  EXTRACT_TASKS_TEXT: '/api/tasks/extract-text',
  MEETING_TASKS: (id: string) => `/api/tasks/meeting/${id}`,
  USER_TASKS: '/api/tasks',
  TASK_DETAIL: (id: string) => `/api/tasks/${id}`,
  
  // Calendar
  GOOGLE_AUTH: '/api/calendar/google/auth-url',
  GOOGLE_CALLBACK: '/api/calendar/google/callback',
  OUTLOOK_AUTH: '/api/calendar/outlook/auth-url',
  OUTLOOK_CALLBACK: '/api/calendar/outlook/callback',
  CREATE_EVENT: (id: string) => `/api/calendar/create-event/${id}`,
  CALENDAR_EVENTS: '/api/calendar/events',
};