import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    name: '管理员',
    role: '超级管理员',
    token: localStorage.getItem('access_token') || '',
  }),
  actions: {
    setToken(token: string) {
      this.token = token
      localStorage.setItem('access_token', token)
    },
    logout() {
      this.token = ''
      localStorage.removeItem('access_token')
    },
  },
})
