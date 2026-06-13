import client from './client'
import type { ApiResponse } from '@/types/api'

export interface LowStock {
  materials: {
    id: number
    name: string
    stock_g: string
    low_stock_g: string
    avg_price_per_g: string
  }[]
  parts: {
    id: number
    name: string
    stock_qty: string
    low_stock_qty: string
    avg_unit_price: string
    use_unit: string
  }[]
}

export interface MonthlyStats {
  year: number
  month: number
  products_count: number
  completed_count: number
  total_cost: string
  customer_price: string
  estimated_profit: string
}

export interface MaterialUsage {
  material_id: number
  material_name: string
  grams: string
}

export function getLowStock() {
  return client.get('/api/stats/low-stock') as unknown as Promise<ApiResponse<LowStock>>
}

export function getMonthlyStats(year: number, month: number) {
  return client.get('/api/stats/monthly', {
    params: { year, month },
  }) as unknown as Promise<ApiResponse<MonthlyStats>>
}

export function getMaterialUsage(start?: string, end?: string) {
  return client.get('/api/stats/material-usage', {
    params: { start, end },
  }) as unknown as Promise<ApiResponse<MaterialUsage[]>>
}
