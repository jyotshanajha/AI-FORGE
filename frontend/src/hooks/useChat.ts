import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import {
  createThread,
  deleteThread,
  listMessages,
  listThreads,
  renameThread,
  streamChat,
} from '../lib/api'
import type { ChatAttachment, ChatResponseMode, Message } from '../types/api'

export function useChat(activeThreadId: string | null) {
  const queryClient = useQueryClient()
  const [isStreaming, setIsStreaming] = useState(false)

  const threadsQuery = useQuery({
    queryKey: ['threads'],
    queryFn: listThreads,
  })

  const messagesQuery = useQuery({
    queryKey: ['messages', activeThreadId],
    queryFn: () => listMessages(activeThreadId as string),
    enabled: Boolean(activeThreadId),
  })

  const createThreadMutation = useMutation({
    mutationFn: createThread,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['threads'] })
    },
  })

  const renameThreadMutation = useMutation({
    mutationFn: (values: { threadId: string; title: string }) => renameThread(values.threadId, values.title),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['threads'] })
    },
  })

  const deleteThreadMutation = useMutation({
    mutationFn: deleteThread,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['threads'] })
      await queryClient.invalidateQueries({ queryKey: ['messages'] })
    },
  })

  const sendMessage = async (
    threadId: string,
    message: string,
    attachments: ChatAttachment[] = [],
    responseMode: ChatResponseMode = 'rag',
  ): Promise<void> => {
    if (!threadId || (!message.trim() && attachments.length === 0)) {
      return
    }

    const optimisticMessage: Message = {
      id: `local-user-${Date.now()}`,
      thread_id: threadId,
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
      attachments,
    }

    const optimisticAssistant: Message = {
      id: `local-assistant-${Date.now()}`,
      thread_id: threadId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      attachments: [],
    }

    queryClient.setQueryData(['messages', threadId], (previous: Message[] | undefined) => {
      return [...(previous ?? []), optimisticMessage, optimisticAssistant]
    })

    setIsStreaming(true)
    try {
      await streamChat(
        threadId,
        message,
        ({ token }) => {
          queryClient.setQueryData(['messages', threadId], (previous: Message[] | undefined) => {
            if (!previous || previous.length === 0) {
              return previous
            }
            const updated = [...previous]
            const last = updated[updated.length - 1]
            updated[updated.length - 1] = { ...last, content: `${last.content}${token}` }
            return updated
          })
        },
        attachments.map((attachment) => attachment.id),
        responseMode,
      )
      await queryClient.invalidateQueries({ queryKey: ['messages', threadId] })
      await queryClient.invalidateQueries({ queryKey: ['threads'] })
    } finally {
      setIsStreaming(false)
    }
  }

  return {
    threads: threadsQuery.data ?? [],
    messages: messagesQuery.data ?? [],
    isThreadsLoading: threadsQuery.isLoading,
    isMessagesLoading: messagesQuery.isLoading,
    createThreadMutation,
    renameThreadMutation,
    deleteThreadMutation,
    sendMessage,
    isStreaming,
  }
}
