import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'

export type AccountFieldType = 'text' | 'number'
export interface AccountField { id: number; key: string; label: string; type: AccountFieldType; is_system: boolean; sort_order: number; created_at: string; updated_at: string }
export interface AccountRecord { id: number; values: Record<string, string | number>; sort_order: number; created_at: string; updated_at: string }
export interface AccountSummary { account_count: number; total_followers: number; total_notes: number; field_count: number; updated_at: string }
export interface AccountDataPage { fields: AccountField[]; records: AccountRecord[]; summary: AccountSummary }
export interface RecordMutation { record: AccountRecord; summary: AccountSummary }

export const getAccountData = () => request.get<never, ApiResponse<AccountDataPage>>('/account-data')
export const createAccountRecord = (values: Record<string, string | number>) => request.post<never, ApiResponse<RecordMutation>>('/account-data/records', { values })
export const updateAccountRecord = (id: number, values: Record<string, string | number>) => request.patch<never, ApiResponse<RecordMutation>>(`/account-data/records/${id}`, { values })
export const deleteAccountRecord = (id: number) => request.delete<never, ApiResponse<{ deleted_id: number; summary: AccountSummary }>>(`/account-data/records/${id}`)
export const createAccountField = (data: { label: string; type: AccountFieldType }) => request.post<never, ApiResponse<{ field: AccountField; default_value: string | number }>>('/account-data/fields', data)
export const updateAccountField = (id: number, data: { label?: string; sort_order?: number }) => request.patch<never, ApiResponse<{ field: AccountField }>>(`/account-data/fields/${id}`, data)
export const deleteAccountField = (id: number) => request.delete<never, ApiResponse<{ deleted_id: number; deleted_key: string; summary: AccountSummary }>>(`/account-data/fields/${id}`)
