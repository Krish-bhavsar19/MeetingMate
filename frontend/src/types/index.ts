// User types
export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface UserRegistration {
  email: string;
  full_name: string;
  password: string;
}

export interface UserLogin {
  username: string; // email
  password: string;
}

// Meeting types
export interface Meeting {
  id: string;
  title: string;
  description?: string;
  audio_file_name?: string;
  duration?: number;
  transcript?: string;
  summary?: string;
  action_items_count: number;
  transcription_status: 'pending' | 'processing' | 'completed' | 'failed';
  summarization_status: 'pending' | 'processing' | 'completed' | 'failed';
  action_extraction_status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  processed_at?: string;
}

export interface MeetingCreate {
  title: string;
  description?: string;
}

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
}

export interface TranscriptionResult {
  transcript: string;
  language: string;
  segments: TranscriptSegment[];
}

// Summary types
export interface SummaryResult {
  summary: string;
  stats: {
    original_length: number;
    summary_length: number;
    compression_ratio: number;
  };
}

// Action Item types
export interface ActionItem {
  id: string;
  meeting_id: string;
  text: string;
  assignees: string[];
  due_date?: string;
  organizations: string[];
  confidence: number;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high';
  calendar_event_id?: string;
  calendar_provider?: string;
  created_at: string;
  completed_at?: string;
}

export interface ActionItemCreate {
  text: string;
  assignees?: string[];
  due_date?: string;
  priority?: 'low' | 'medium' | 'high';
}

export interface ActionItemUpdate {
  text?: string;
  assignees?: string[];
  due_date?: string;
  status?: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority?: 'low' | 'medium' | 'high';
}

// API Response types
export interface ApiResponse<T = any> {
  message?: string;
  data?: T;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Error types
export interface ApiError {
  detail: string;
  status_code?: number;
}