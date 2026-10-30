import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'

export interface XianyuLinkPayload {
  title: string
  link: string
}

export interface XianyuLink extends XianyuLinkPayload {
  id: number
  created_at: string
  updated_at: string
}

export interface XianyuLinkPage {
  items: XianyuLink[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const getXianyuLinks = (params: { page: number; page_size: number; keyword?: string }) =>
  request.get<never, ApiResponse<XianyuLinkPage>>('/xianyu-links', { params })

export const createXianyuLink = (data: XianyuLinkPayload) =>
  request.post<never, ApiResponse<XianyuLink>>('/xianyu-links', data)

export const updateXianyuLink = (id: number, data: Partial<XianyuLinkPayload>) =>
  request.patch<never, ApiResponse<XianyuLink>>(`/xianyu-links/${id}`, data)

export const deleteXianyuLink = (id: number) =>
  request.delete<never, ApiResponse<{ deleted_id: number }>>(`/xianyu-links/${id}`)
