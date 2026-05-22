// User types
export enum UserRole {
  ADMIN = "admin",
  INSTRUCTOR = "instructor",
  LEARNER = "learner",
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  avatar_url?: string | null;
  bio?: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login_at?: string | null;
}

// Auth types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  role?: UserRole;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse extends TokenResponse {
  user: User;
}

// Course types
export enum CourseStatus {
  DRAFT = "draft",
  PUBLISHED = "published",
  ARCHIVED = "archived",
}

export enum CourseLevel {
  ELEMENTARY = "elementary",
  MIDDLE_SCHOOL = "middle_school",
  HIGH_SCHOOL = "high_school",
  HIGHER_EDUCATION = "higher_education",
}

export interface Course {
  id: string;
  slug: string;
  instructor_id: string;
  title: string;
  description?: string | null;
  short_description?: string | null;
  thumbnail_url?: string | null;
  status: CourseStatus;
  category?: string | null;
  level: CourseLevel;
  language: string;
  estimated_duration?: number | null;
  is_featured: boolean;
  created_at: string;
  updated_at: string;
  published_at?: string | null;
}

export interface CourseDetail extends Course {
  instructor: User;
  lesson_count: number;
}

// Lesson types
export interface Lesson {
  id: string;
  course_id: string;
  title: string;
  description?: string | null;
  content?: string | null;
  video_url?: string | null;
  video_duration?: number | null;
  thumbnail_url?: string | null;
  order_index: number;
  is_published: boolean;
  is_preview: boolean;
  created_at: string;
  updated_at: string;
}

// Material types
export interface Material {
  id: string;
  course_id?: string | null;
  lesson_id?: string | null;
  title: string;
  description?: string | null;
  type: string;
  file_url?: string | null;
  file_size?: number | null;
  mime_type?: string | null;
  order_index: number;
  created_at: string;
}

// Assignment types
export enum AssignmentType {
  PRACTICE = "practice",
  TEST = "test",
}

export enum AssignmentQuestionType {
  MULTIPLE_CHOICE = "multiple_choice",
  ESSAY = "essay",
}

export interface Assignment {
  id: string;
  course_id: string;
  lesson_id?: string | null;
  title: string;
  assignment_type: AssignmentType;
  scoped_lesson_ids: string[];
  is_published: boolean;
  order_index: number;
  questions: AssignmentQuestion[];
  created_at: string;
  updated_at: string;
}

export interface AssignmentQuestion {
  id: string;
  assignment_id: string;
  question_text: string;
  question_type: AssignmentQuestionType;
  correct_answer_text?: string | null;
  difficulty: QuestionDifficulty;
  purpose_type: QuestionPurposeType;
  order_index: number;
  options: AssignmentOption[];
  created_at: string;
  updated_at: string;
}

export interface AssignmentOption {
  id: string;
  question_id: string;
  option_text: string;
  is_correct: boolean;
  order_index: number;
  created_at: string;
  updated_at: string;
}

// Question bank types
export enum QuestionDifficulty {
  EASY = "easy",
  MEDIUM = "medium",
  HARD = "hard",
}

export enum QuestionPurposeType {
  PRACTICE = "practice",
  ASSESSMENT = "assessment",
  SHARED = "shared",
}

export interface QuestionBankCourse {
  id: string;
  title: string;
  slug: string;
  instructor_id: string;
}

export interface QuestionBankOption {
  id: string;
  question_id: string;
  option_text: string;
  is_correct: boolean;
  order_index: number;
  created_at: string;
  updated_at: string;
}

export interface QuestionBankQuestion {
  id: string;
  course_id: string;
  lesson_id?: string | null;
  question_text: string;
  difficulty: QuestionDifficulty;
  purpose_type: QuestionPurposeType;
  order_index: number;
  course_title: string;
  lesson_title?: string | null;
  options: QuestionBankOption[];
  created_at: string;
  updated_at: string;
}

// Submission types
export enum SubmissionStatus {
  SUBMITTED = "submitted",
  GRADED = "graded",
  RETURNED = "returned",
}

export interface Submission {
  id: string;
  assignment_id: string;
  user_id: string;
  content?: string | null;
  file_url?: string | null;
  file_name?: string | null;
  file_size?: number | null;
  status: SubmissionStatus;
  score?: number | null;
  feedback?: string | null;
  submitted_at: string;
  graded_at?: string | null;
  is_late: boolean;
  answers?: SubmissionAnswer[];
}

export interface SubmissionAnswer {
  id: string;
  submission_id: string;
  question_id: string;
  selected_option_id?: string | null;
  answer_text?: string | null;
  is_correct?: boolean | null;
  score?: number | null;
  explanation?: string | null;
  feedback?: string | null;
  correct_answer_text?: string | null;
}

// API Response types
export interface ApiError {
  detail: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
