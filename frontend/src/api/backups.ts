import client from './client'
import type { ApiResponse } from '@/types/api'

export interface Backup {
  filename: string
  size_bytes: number
  created_at: string
}

export function listBackups() {
  return client.get('/api/backups') as unknown as Promise<ApiResponse<Backup[]>>
}

export function createBackup() {
  return client.post('/api/backups') as unknown as Promise<ApiResponse<Backup>>
}
