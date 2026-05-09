import { useMemo, useState } from 'react'
import { AppBar, Box, Button, Drawer, Toolbar, Typography, Alert } from '@mui/material'
import LogoutIcon from '@mui/icons-material/Logout'
import MenuIcon from '@mui/icons-material/Menu'

import { InputBar } from '../components/chat/InputBar'
import { MessageList } from '../components/chat/MessageList'
import { ThreadSidebar } from '../components/chat/ThreadSidebar'
import { useAuth } from '../hooks/useAuth'
import { useChat } from '../hooks/useChat'

export default function ChatPage() {
  const { user, logoutMutation } = useAuth()
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const {
    threads,
    messages,
    createThreadMutation,
    renameThreadMutation,
    deleteThreadMutation,
    sendMessage,
    isStreaming,
  } = useChat(activeThreadId)

  const resolvedActiveThreadId = useMemo(() => {
    if (activeThreadId) {
      return activeThreadId
    }
    return threads[0]?.id ?? null
  }, [activeThreadId, threads])

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <AppBar position="static" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Button
            color="inherit"
            size="small"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </Button>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
              Amzur AI Chat
            </Typography>
            <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
              {user?.email}
            </Typography>
          </Box>
          <Button
            color="inherit"
            size="small"
            startIcon={<LogoutIcon />}
            disabled={logoutMutation.isPending}
            onClick={() => logoutMutation.mutate()}
          >
            Logout
          </Button>
        </Toolbar>
      </AppBar>

      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Drawer
          variant="persistent"
          anchor="left"
          open={sidebarOpen}
          sx={{
            width: 280,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: 280,
              boxSizing: 'border-box',
              position: 'relative',
              height: '100%',
            },
          }}
        >
          <ThreadSidebar
            threads={threads}
            activeThreadId={resolvedActiveThreadId}
            onSelectThread={setActiveThreadId}
            onCreateThread={async () => {
              try {
                setError(null)
                const created = await createThreadMutation.mutateAsync()
                setActiveThreadId(created.id)
              } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to create thread')
              }
            }}
            onRenameThread={async (threadId) => {
              try {
                setError(null)
                const current = threads.find((thread) => thread.id === threadId)
                const nextTitle = window.prompt('Rename thread', current?.title ?? 'New Chat')
                if (!nextTitle?.trim()) {
                  return
                }
                await renameThreadMutation.mutateAsync({ threadId, title: nextTitle.trim() })
              } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to rename thread')
              }
            }}
            onDeleteThread={async (threadId) => {
              try {
                setError(null)
                await deleteThreadMutation.mutateAsync(threadId)
                if (resolvedActiveThreadId === threadId) {
                  setActiveThreadId(null)
                }
              } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to delete thread')
              }
            }}
          />
        </Drawer>

        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {error && (
            <Alert severity="error" onClose={() => setError(null)} sx={{ m: 2 }}>
              {error}
            </Alert>
          )}

          <MessageList messages={messages} isStreaming={isStreaming} />

          <InputBar
            onSend={async ({ message, attachments }) => {
              try {
                setError(null)
                if (!resolvedActiveThreadId) {
                  const created = await createThreadMutation.mutateAsync()
                  setActiveThreadId(created.id)
                  await sendMessage(created.id, message, attachments)
                  return
                }
                await sendMessage(resolvedActiveThreadId, message, attachments)
              } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to send message')
              }
            }}
            disabled={isStreaming}
            threadId={resolvedActiveThreadId ?? undefined}
          />
        </Box>
      </Box>
    </Box>
  )
}
