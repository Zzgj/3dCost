import client from './client'
import type { ApiResponse, ApiListResponse } from '@/types/api'

export interface Machine {
  id: number
  name: string
  price: string
  life_hours: number
  power_w: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface MachineCreate {
  name: string
  price: string
  life_hours: number
  power_w: number
}

export function listMachines(page = 1, pageSize = 100) {
  return client.get('/api/machines', {
    params: { page, page_size: pageSize },
  }) as unknown as Promise<ApiListResponse<Machine>>
}

export function createMachine(payload: MachineCreate) {
  return client.post('/api/machines', payload) as unknown as Promise<ApiResponse<Machine>>
}

export function updateMachine(
  id: number,
  payload: Partial<MachineCreate> & { is_active?: boolean },
) {
  return client.patch(`/api/machines/${id}`, payload) as unknown as Promise<ApiResponse<Machine>>
}
