import client from './client'
import type { ApiResponse } from '@/types/api'

export interface Purchase {
  id: number
  target_kind: string
  target_id: number
  qty_rolls: number | null
  grams_per_roll: number | null
  qty: string | null
  goods_amount: string
  shipping_fee: string
  supplier_id: number | null
  purchase_url: string | null
  purchased_at: string
  created_at: string
}

export interface PurchaseResult {
  purchase: Purchase
  updated_avg_price: string
  total_stock: string
}

export interface PurchaseCreate {
  target_kind: 'material' | 'part'
  target_id: number
  qty_rolls?: number
  grams_per_roll?: number
  qty?: string
  goods_amount: string
  shipping_fee?: string
  supplier_id?: number | null
  purchase_url?: string | null
  purchased_at?: string | null
}

export function createPurchase(payload: PurchaseCreate) {
  return client.post('/api/purchases', payload) as unknown as Promise<ApiResponse<PurchaseResult>>
}

export function listPurchases(targetKind: 'material' | 'part', targetId: number) {
  return client.get('/api/purchases', {
    params: { target_kind: targetKind, target_id: targetId },
  }) as unknown as Promise<ApiResponse<Purchase[]>>
}
