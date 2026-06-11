export interface Meta {
  request_id: string
  warnings: string[]
}

export interface ApiResponse<T> {
  data: T
  meta: Meta
}

export interface Pagination {
  page: number
  page_size: number
  total: number
}

export interface ApiListResponse<T> {
  data: T[]
  pagination: Pagination
  meta: Meta
}

export interface ApiError {
  error: { code: string; message: string; details: Record<string, unknown> }
  meta: { request_id: string }
}
