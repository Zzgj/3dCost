import client, { API_BASE_URL } from './client'
import type { ApiResponse, ApiListResponse } from '@/types/api'

export interface Quote {
  id: number
  product_id: number
  mode: string
  internal_cost: string
  customer_price: string
  created_at: string
}

export interface QuoteDetail extends Quote {
  snapshot: {
    product: {
      id: number
      name: string
      mode: string
      status: string
      markup_rate: string
      note: string | null
    }
    cost_detail: Record<string, string>
    bom_items: Array<Record<string, string | number | null>>
  }
}

export function createQuote(productId: number, mode?: string) {
  return client.post('/api/quotes', {
    product_id: productId,
    mode,
  }) as unknown as Promise<ApiResponse<QuoteDetail>>
}

export function listQuotes(page = 1, pageSize = 100, productId?: number | null) {
  return client.get('/api/quotes', {
    params: { page, page_size: pageSize, product_id: productId || undefined },
  }) as unknown as Promise<ApiListResponse<Quote>>
}

export function getQuote(id: number) {
  return client.get(`/api/quotes/${id}`) as unknown as Promise<ApiResponse<QuoteDetail>>
}

export function quoteExportUrl(id: number, type: 'internal' | 'customer') {
  return `${API_BASE_URL}/api/quotes/${id}/export?type=${type}&format=html`
}
