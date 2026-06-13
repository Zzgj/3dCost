import client from './client'
import type { ApiResponse } from '@/types/api'

export interface CostSetting {
  id: number
  electricity_price: string
  default_machine_id: number | null
  scrap_rate: string
  labor_rate: string
  default_markup: string
  updated_at: string
}

export interface CostSettingUpdate {
  electricity_price?: string
  default_machine_id?: number | null
  scrap_rate?: string
  labor_rate?: string
  default_markup?: string
}

export function getCostSetting() {
  return client.get('/api/settings/cost') as unknown as Promise<ApiResponse<CostSetting>>
}

export function updateCostSetting(payload: CostSettingUpdate) {
  return client.patch('/api/settings/cost', payload) as unknown as Promise<ApiResponse<CostSetting>>
}
