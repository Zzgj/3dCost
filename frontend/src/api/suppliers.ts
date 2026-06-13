import client from './client'
import type { ApiResponse, ApiListResponse } from '@/types/api'

export interface Supplier {
  id: number
  name: string
  note: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SupplierCreate {
  name: string
  note?: string | null
}

export function listSuppliers(page = 1, pageSize = 100) {
  return client.get('/api/suppliers', {
    params: { page, page_size: pageSize },
  }) as unknown as Promise<ApiListResponse<Supplier>>
}

export function createSupplier(payload: SupplierCreate) {
  return client.post('/api/suppliers', payload) as unknown as Promise<ApiResponse<Supplier>>
}

export function updateSupplier(
  id: number,
  payload: Partial<SupplierCreate> & { is_active?: boolean },
) {
  return client.patch(`/api/suppliers/${id}`, payload) as unknown as Promise<ApiResponse<Supplier>>
}
