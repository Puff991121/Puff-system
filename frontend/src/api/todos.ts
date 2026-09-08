import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'

export type TodoPeriod = 'daily' | 'weekly' | 'monthly'
export type TodoPriority = 'low' | 'medium' | 'high'
export type TodoStatus = 'pending' | 'completed'

export interface Todo {
  id: number
  title: string
  description: string | null
  period_type: TodoPeriod
  scheduled_date: string
  priority: TodoPriority
  status: TodoStatus
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface TodoPayload {
  title: string
  description?: string | null
  period_type: TodoPeriod
  scheduled_date: string
  priority: TodoPriority
  status?: TodoStatus
}

export interface TodoQuery {
  page?: number
  page_size?: number
  period_type?: TodoPeriod
  status?: TodoStatus
  keyword?: string
  start_date?: string
  end_date?: string
}

export interface TodoPage { items: Todo[]; total: number; page: number; page_size: number; total_pages: number }
export interface TodoSummary { total: number; pending: number; completed: number; overdue: number; daily: number; weekly: number; monthly: number; completion_rate: number }

export const getTodos = (params: TodoQuery) => request.get<never, ApiResponse<TodoPage>>('/todos', { params })
export const getTodoSummary = () => request.get<never, ApiResponse<TodoSummary>>('/todos/summary')
export const createTodo = (data: TodoPayload) => request.post<never, ApiResponse<Todo>>('/todos', data)
export const updateTodo = (id: number, data: Partial<TodoPayload>) => request.patch<never, ApiResponse<Todo>>(`/todos/${id}`, data)
export const deleteTodo = (id: number) => request.delete<never, ApiResponse<{ deleted_id: number }>>(`/todos/${id}`)
