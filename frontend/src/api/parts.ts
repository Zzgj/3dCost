import client from './client'
import type { ApiResponse, ApiListResponse } from '@/types/api'

export interface Part {
  id: number
  name: string
  category: string
  spec: string
  purchase_unit: string
  use_unit: string
  conversion_ratio: string
  stock_qty: string
  low_stock_qty: string
  avg_unit_price: string
  default_supplier_id: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PartCreate {
  name: string
  category?: string
  spec?: string
  purchase_unit?: string
  use_unit?: string
  conversion_ratio?: string
  low_stock_qty?: string
  default_supplier_id?: number | null
}

export function listParts(page = 1, pageSize = 100) {
  return client.get('/api/parts', {
    params: { page, page_size: pageSize },
  }) as unknown as Promise<ApiListResponse<Part>>
}

export function createPart(payload: PartCreate) {
  return client.post('/api/parts', payload) as unknown as Promise<ApiResponse<Part>>
}

export function updatePart(id: number, payload: Partial<PartCreate> & { is_active?: boolean }) {
  return client.patch(`/api/parts/${id}`, payload) as unknown as Promise<ApiResponse<Part>>
}
