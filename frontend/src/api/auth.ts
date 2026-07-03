import request from '@/utils/request'

export interface LoginPayload { username: string; password: string }
export interface LoginResult { access_token: string; token_type: string }

export const login = (data: LoginPayload) =>
  request.post<never, LoginResult>('/auth/login', data)
