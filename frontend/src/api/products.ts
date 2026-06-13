import client from './client'
import type { ApiResponse, ApiListResponse } from '@/types/api'

export type BOMKind = 'printitem' | 'part' | 'postprocess' | 'subproduct'

export interface BOMItemIn {
  kind: BOMKind
  ref_id?: number | null
  qty?: string | null
  hours?: string | null
}

export interface BOMItemOut {
  id: number
  kind: BOMKind
  ref_id: number | null
  ref_name: string | null
  qty: string | null
  hours: string | null
  unit_price: string
  subtotal: string
}

export interface CostDetail {
  printitems_cost: string
  parts_cost: string
  postprocess_cost: string
  subproduct_cost: string
  subtotal: string
  scrap_cost: string
  total_cost: string
  customer_price: string
}

export interface Product {
  id: number
  name: string
  note: string | null
  mode: string
  status: string
  markup_rate: string
  total_cost: string
  customer_price: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ProductDetail extends Product {
  bom_items: BOMItemOut[]
  cost_detail: CostDetail
}

export interface ProductCreate {
  name: string
  note?: string | null
  mode?: string
  markup_rate?: string
  bom_items?: BOMItemIn[]
}

export interface ProductUpdate {
  name?: string
  note?: string | null
  mode?: string
  markup_rate?: string
  bom_items?: BOMItemIn[]
}

export interface ConsumeResult {
  consumed: {
    materials: { name: string; deducted_g: string; remaining_g: string }[]
    parts: { name: string; deducted_qty: string; remaining_qty: string }[]
  }
  warnings: string[]
}

export function listProducts(page = 1, pageSize = 20, status?: string, mode?: string) {
  return client.get('/api/products', {
    params: { page, page_size: pageSize, status, mode },
  }) as unknown as Promise<ApiListResponse<ProductDetail>>
}

export function getProduct(id: number) {
  return client.get(`/api/products/${id}`) as unknown as Promise<ApiResponse<ProductDetail>>
}

export function createProduct(payload: ProductCreate) {
  return client.post('/api/products', payload) as unknown as Promise<ApiResponse<ProductDetail>>
}

export function updateProduct(id: number, payload: ProductUpdate) {
  return client.patch(`/api/products/${id}`, payload) as unknown as Promise<ApiResponse<ProductDetail>>
}

export function consumeStock(id: number) {
  return client.post(`/api/products/${id}/consume-stock`) as unknown as Promise<ApiResponse<ConsumeResult>>
}

export function completeProduct(id: number) {
  return client.post(`/api/products/${id}/complete`) as unknown as Promise<ApiResponse<ProductDetail>>
}
