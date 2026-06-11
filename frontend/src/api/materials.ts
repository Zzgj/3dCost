import client from './client'
import type { ApiResponse, ApiListResponse } from '@/types/api'

export interface Material {
  id: number
  name: string
  type: string
  color: string
  brand: string
  stock_g: string
  low_stock_g: string
  avg_price_per_g: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface MaterialCreate {
  name: string
  type: string
  color?: string
  brand?: string
  low_stock_g?: string
}

export function listMaterials(page = 1, pageSize = 20) {
  return client.get('/api/materials', { params: { page, page_size: pageSize } }) as unknown as Promise<ApiListResponse<Material>>
}

export function createMaterial(payload: MaterialCreate) {
  return client.post('/api/materials', payload) as unknown as Promise<ApiResponse<Material>>
}
