import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'

export type PaymentMethod = '微信' | '咸鱼' | '小红书' | '支付宝'
export type WorkFormat = 'Figma' | 'Psd' | 'Xd' | 'Jsd' | 'Html' | '定做' | '无'

export interface Order {
    id: number
    order_no: string
    order_date: string
    requirement: string
    template: string
    format: WorkFormat
    school: string
    price: string
    payment_method: PaymentMethod
    created_at: string
    updated_at: string
}

export interface OrderPayload {
    order_date?: string
    requirement: string
    template: string
    format: WorkFormat
    school: string
    price: string
    payment_method: PaymentMethod
}

export interface OrderQuery {
    page: number
    page_size: number
    keyword?: string
    payment_method?: PaymentMethod
    start_date?: string
    end_date?: string
    sort_by?: 'order_date' | 'price' | 'created_at'
    sort_order?: 'asc' | 'desc'
}

export interface OrderPage {
    items: Order[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

export interface ImportResult {
    total_rows: number
    success_count: number
    failed_count: number
    imported_orders: Order[]
    errors: Array<{
        row: number
        field: string
        value: unknown
        message: string
    }>
}

export const getOrders = (params: OrderQuery) =>
    request.get<never, ApiResponse<OrderPage>>('/orders', { params })

export const getOrder = (id: number) =>
    request.get<never, ApiResponse<Order>>(`/orders/${id}`)

export const createOrder = (data: OrderPayload) =>
    request.post<never, ApiResponse<Order>>('/orders', data)

export const updateOrder = (id: number, data: Partial<OrderPayload>) =>
    request.patch<never, ApiResponse<Order>>(`/orders/${id}`, data)

export const deleteOrder = (id: number) =>
    request.delete<never, ApiResponse<{ deleted_id: number }>>(`/orders/${id}`)

export const importOrderFile = (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    return request.post<never, ApiResponse<ImportResult>>(
        '/orders/import',
        formData,
    )
}

export const exportOrderFile = (params: Omit<OrderQuery, 'page' | 'page_size'>) =>
    request.get<never, Blob>('/orders/export', {
        params,
        responseType: 'blob',
    })