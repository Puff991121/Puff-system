import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'
import type { WorkFormat } from '@/api/orders'

export type TemplateFormat = Extract<WorkFormat, 'Figma' | 'Psd' | 'Xd' | 'Jsd' | 'Html'> | '素材'
export type TemplateShareField = 'figma_share' | 'psd_share' | 'xd_share' | 'jsd_share' | 'html_share' | 'material_share'

export const TEMPLATE_FORMATS: readonly {
  value: TemplateFormat
  field: TemplateShareField
  description: string
}[] = [
  { value: 'Html', field: 'html_share', description: '源代码' },
  { value: 'Figma', field: 'figma_share', description: '设计文件' },
  { value: 'Psd', field: 'psd_share', description: '设计文件' },
  { value: 'Jsd', field: 'jsd_share', description: '即时设计' },
  { value: 'Xd', field: 'xd_share', description: '设计文件' },
  { value: '素材', field: 'material_share', description: '素材文件' },
]

export type TemplatePayload = {
  name: string
  notes: string | null
} & Record<TemplateShareField, string | null>

export interface TemplateRecord extends TemplatePayload {
  id: number
  created_at: string
  updated_at: string
  share_urls: Record<TemplateFormat, string | null>
}

export interface TemplatePage {
  items: TemplateRecord[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const getTemplates = (params: { page: number; page_size: number; keyword?: string }) =>
  request.get<never, ApiResponse<TemplatePage>>('/templates', { params })

export const createTemplate = (data: TemplatePayload) =>
  request.post<never, ApiResponse<TemplateRecord>>('/templates', data)

export const updateTemplate = (id: number, data: Partial<TemplatePayload>) =>
  request.patch<never, ApiResponse<TemplateRecord>>(`/templates/${id}`, data)

export const deleteTemplate = (id: number) =>
  request.delete<never, ApiResponse<{ deleted_id: number }>>(`/templates/${id}`)
