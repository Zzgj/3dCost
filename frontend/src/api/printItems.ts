import client from './client'
import type { ApiResponse, ApiListResponse } from '@/types/api'

export interface PrintFilament {
  material_id: number
  grams: string
}

export interface PrintCost {
  material_cost: string
  machine_cost: string
  total: string
}

export interface PrintItem {
  id: number
  name: string
  machine_id: number
  print_hours: string
  plates: number
  nozzle: string
  source_url: string | null
  filaments: PrintFilament[]
  is_active: boolean
  created_at: string
  updated_at: string
  cost: PrintCost | null
  cost_error?: string
}

export interface PrintItemCreate {
  name: string
  machine_id: number
  print_hours: string
  plates?: number
  nozzle?: string
  source_url?: string | null
  filaments: PrintFilament[]
}

export function listPrintItems(page = 1, pageSize = 20) {
  return client.get('/api/print-items', { params: { page, page_size: pageSize } }) as unknown as Promise<ApiListResponse<PrintItem>>
}

export function createPrintItem(payload: PrintItemCreate) {
  return client.post('/api/print-items', payload) as unknown as Promise<ApiResponse<PrintItem>>
}

export function updatePrintItem(id: number, payload: Partial<PrintItemCreate>) {
  return client.patch(`/api/print-items/${id}`, payload) as unknown as Promise<ApiResponse<PrintItem>>
}

export function deletePrintItem(id: number) {
  return client.delete(`/api/print-items/${id}`) as unknown as Promise<ApiResponse<{ deleted: number }>>
}
