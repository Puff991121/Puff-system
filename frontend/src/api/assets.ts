import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'

export type AssetAccountType = 'asset' | 'liability'

export interface AssetAccount {
  id: number
  type: AssetAccountType
  account: string
  amount: string
  sort_order: number
  created_at: string
  updated_at: string
}

export interface AssetSummary {
  total_assets: string
  total_liabilities: string
  net_assets: string
  liability_ratio: string
  asset_account_count: number
  liability_account_count: number
  updated_at: string
}

export interface AssetPageData {
  summary: AssetSummary
  assets: AssetAccount[]
  liabilities: AssetAccount[]
}

export interface AssetMutationResult {
  account: AssetAccount
  summary: AssetSummary
}

export const getAssetPage = () =>
  request.get<never, ApiResponse<AssetPageData>>('/assets')

export const createAssetAccount = (data: {
  type: AssetAccountType
  account: string
  amount: string
}) => request.post<never, ApiResponse<AssetMutationResult>>('/assets/accounts', data)

export const updateAssetAccount = (
  id: number,
  data: { account?: string; amount?: string; sort_order?: number },
) => request.patch<never, ApiResponse<AssetMutationResult>>(`/assets/accounts/${id}`, data)

export const deleteAssetAccount = (id: number) =>
  request.delete<never, ApiResponse<{ deleted_id: number; summary: AssetSummary }>>(
    `/assets/accounts/${id}`,
  )
