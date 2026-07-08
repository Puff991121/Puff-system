import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'

export interface Expense { id: number; transaction_time: string; transaction_type: string; counterparty: string; description: string; amount: string; payment_method: string; created_at: string; updated_at: string }
export interface ExpensePayload { transaction_time: string; transaction_type: string; counterparty: string; description: string; amount: string; payment_method: string }
export interface ExpenseQuery { page?: number; page_size?: number; start_time?: string; end_time?: string; transaction_type?: string; description?: string; payment_method?: string; sort_by?: 'transaction_time' | 'amount' | 'created_at'; sort_order?: 'asc' | 'desc' }
export interface ExpensePage { items: Expense[]; total: number; page: number; page_size: number; total_pages: number }
export interface ExpenseSummary { today_amount: string; today_count: number; month_amount: string; month_count: number; month_change_rate: string | null; year_amount: string; year_count: number; year_change_rate: string | null; total_amount: string; total_count: number }
export interface ExpenseImportResult { total_rows: number; success_count: number; failed_count: number; errors: Array<{ row: number; message: string }> }

export const getExpenses = (params: ExpenseQuery) => request.get<never, ApiResponse<ExpensePage>>('/expenses', { params })
export const getExpenseSummary = (referenceDate?: string) => request.get<never, ApiResponse<ExpenseSummary>>('/expenses/summary', { params: { reference_date: referenceDate } })
export const createExpense = (data: ExpensePayload) => request.post<never, ApiResponse<Expense>>('/expenses', data)
export const updateExpense = (id: number, data: Partial<ExpensePayload>) => request.patch<never, ApiResponse<Expense>>(`/expenses/${id}`, data)
export const deleteExpense = (id: number) => request.delete<never, ApiResponse<{ deleted_id: number }>>(`/expenses/${id}`)
export const importExpenseFile = (file: File) => { const data = new FormData(); data.append('file', file); return request.post<never, ApiResponse<ExpenseImportResult>>('/expenses/import', data) }
export const exportExpenseFile = (params: ExpenseQuery) => request.get<never, Blob>('/expenses/export', { params, responseType: 'blob' })
