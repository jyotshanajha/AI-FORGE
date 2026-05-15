import { useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { getGoogleLoginUrl, login, logout, me, register } from '../lib/api'

export function useAuth() {
  const queryClient = useQueryClient()

  const meQuery = useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      try {
        return await me()
      } catch (error) {
        // 401 Unauthorized is expected when not logged in - treat as success with no user
        if (error instanceof Error && error.message.includes('401')) {
          return undefined
        }
        throw error
      }
    },
    retry: false,
  })

  // Refetch user on mount (important for OAuth callback redirect)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const error = params.get('error')
    if (error) {
      console.error('OAuth error:', error, params.get('message'))
    } else if (params.has('code') || params.has('state')) {
      // Only refetch if we detect OAuth params
      void meQuery.refetch()
    }
  }, []) // Empty dependency array - only run on mount

  const loginMutation = useMutation({
    mutationFn: (values: { email: string; password: string }) => login(values.email, values.password),
    onSuccess: (data) => {
      queryClient.setQueryData(['me'], data)
    },
  })

  const registerMutation = useMutation({
    mutationFn: (values: { email: string; password: string }) => register(values.email, values.password),
    onSuccess: (data) => {
      queryClient.setQueryData(['me'], data)
    },
  })

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: async () => {
      queryClient.setQueryData(['me'], undefined)
      queryClient.removeQueries({ queryKey: ['threads'] })
      queryClient.removeQueries({ queryKey: ['messages'] })
      await queryClient.invalidateQueries({ queryKey: ['me'] })
      window.location.assign('/')
    },
  })

  const googleLoginMutation = useMutation({
    mutationFn: getGoogleLoginUrl,
    onSuccess: (url) => {
      window.location.assign(url)
    },
  })

  return {
    user: meQuery.data?.user,
    isLoading: meQuery.isLoading,
    isAuthenticated: Boolean(meQuery.data?.user),
    loginMutation,
    registerMutation,
    logoutMutation,
    googleLoginMutation,
  }
}
