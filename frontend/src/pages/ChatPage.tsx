import { useEffect, useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Box, Button, Typography, Alert, useMediaQuery, useTheme } from '@mui/material'
import LogoutIcon from '@mui/icons-material/Logout'
import MenuIcon from '@mui/icons-material/Menu'
import ChatIcon from '@mui/icons-material/Chat'
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh'
import ScienceIcon from '@mui/icons-material/Science'
import SportsEsportsIcon from '@mui/icons-material/SportsEsports'
import TableChartIcon from '@mui/icons-material/TableChart'

import { InputBar } from '../components/chat/InputBar'
import { MessageList } from '../components/chat/MessageList'
import { ThreadSidebar } from '../components/chat/ThreadSidebar'
import { CosmicBackdrop } from '../components/chat/CosmicBackdrop'
import { ImageGenPanel } from '../components/chat/ImageGenPanel'
import { DataframeQueryPanel } from '../components/agents/DataframeQueryPanel'
import { ResearchDigestPanel } from '../components/agents/ResearchDigestPanel'
import { TicTacToePanel } from '../components/agents/TicTacToePanel'
import { useAuth } from '../hooks/useAuth'
import { useChat } from '../hooks/useChat'
import type { ChatResponseMode } from '../types/api'

export default function ChatPage() {
  const { user, logoutMutation } = useAuth()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile)
  const [error, setError] = useState<string | null>(null)
  const [mode, setMode] = useState<'chat' | 'image' | 'dataframe' | 'research' | 'tictactoe'>('chat')
  const [responseMode, setResponseMode] = useState<ChatResponseMode>('rag')
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

  useEffect(() => {
    if (!activeThreadId && threads.length > 0) {
      setActiveThreadId(threads[0].id)
    }
  }, [activeThreadId, threads])

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', px: { xs: 1, md: 1.6 }, py: { xs: 1, md: 1.3 }, position: 'relative' }}>
      <CosmicBackdrop />

      <Box
        sx={{
          position: 'relative',
          zIndex: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          px: 1.2,
          py: 0.9,
          mb: 1.2,
          borderRadius: 99,
          border: '1px solid rgba(164, 203, 255, 0.32)',
          background: 'linear-gradient(180deg, rgba(24,36,76,0.78), rgba(16,24,53,0.58))',
          backdropFilter: 'blur(16px)',
          boxShadow: '0 16px 36px rgba(6, 10, 28, 0.42)',
        }}
      >
        <motion.div whileTap={{ scale: 0.95 }}>
          <Button
            color="inherit"
            size="small"
            onClick={() => setSidebarOpen((value) => !value)}
            sx={{ minWidth: 38, color: 'text.secondary', borderRadius: 999, border: '1px solid rgba(151, 191, 255, 0.24)' }}
          >
            <MenuIcon fontSize="small" />
          </Button>
        </motion.div>

        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
          <Typography variant="h6" component="div" sx={{ lineHeight: 1.15, textShadow: '0 0 14px rgba(140, 199, 255, 0.4)' }}>
            Amzur AI Chat
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            {user?.email}
          </Typography>
        </Box>

        <motion.div whileTap={{ scale: 0.97 }}>
          <Button
            color="inherit"
            size="small"
            startIcon={<LogoutIcon />}
            disabled={logoutMutation.isPending}
            onClick={() => logoutMutation.mutate()}
            sx={{
              borderRadius: 999,
              color: 'text.secondary',
              border: '1px solid rgba(151,191,255,0.24)',
              backgroundColor: 'rgba(23,35,72,0.62)',
            }}
          >
            Logout
          </Button>
        </motion.div>
      </Box>

      <Box sx={{ display: 'flex', flex: 1, minHeight: 0, overflow: 'hidden', gap: 1, position: 'relative', zIndex: 2 }}>
        {/* Mobile sidebar backdrop */}
        <AnimatePresence>
          {sidebarOpen && isMobile && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              style={{
                position: 'fixed',
                inset: 0,
                background: 'rgba(4, 8, 22, 0.55)',
                backdropFilter: 'blur(4px)',
                zIndex: 10,
              }}
              onClick={() => setSidebarOpen(false)}
            />
          )}
        </AnimatePresence>

        <AnimatePresence initial={false}>
          {sidebarOpen && (
            <motion.aside
              initial={{ width: 0, opacity: 0, x: -18 }}
              animate={{ width: isMobile ? 280 : 320, opacity: 1, x: 0 }}
              exit={{ width: 0, opacity: 0, x: -18 }}
              transition={{ type: 'spring', stiffness: 210, damping: 28 }}
              style={{
                overflow: 'hidden',
                minWidth: 0,
                ...(isMobile
                  ? { position: 'fixed', top: 0, left: 0, bottom: 0, zIndex: 11, width: 280 }
                  : {}),
              }}
            >
              <ThreadSidebar
                threads={threads}
                activeThreadId={resolvedActiveThreadId}
                onSelectThread={(threadId) => {
                  setActiveThreadId(threadId)
                  if (isMobile) {
                    setSidebarOpen(false)
                  }
                }}
                onCreateThread={async () => {
                  try {
                    setError(null)
                    const created = await createThreadMutation.mutateAsync()
                    setActiveThreadId(created.id)
                    if (isMobile) {
                      setSidebarOpen(false)
                    }
                  } catch (err) {
                    setError(err instanceof Error ? err.message : 'Failed to create thread')
                  }
                }}
                onRenameThread={async (threadId, title) => {
                  try {
                    setError(null)
                    await renameThreadMutation.mutateAsync({ threadId, title })
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
            </motion.aside>
          )}
        </AnimatePresence>

        <Box
          sx={{
            flex: 1,
            minWidth: 0,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            borderRadius: 4,
            border: '1px solid rgba(164, 203, 255, 0.28)',
            background: 'linear-gradient(180deg, rgba(20, 32, 66, 0.76), rgba(14, 22, 49, 0.58))',
            backdropFilter: 'blur(18px)',
            boxShadow: '0 20px 40px rgba(4, 8, 24, 0.46)',
          }}
        >
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.22, ease: 'easeOut' }}
              >
                <Alert severity="error" onClose={() => setError(null)} sx={{ m: 1.25, borderRadius: 2 }}>
                  {error}
                </Alert>
              </motion.div>
            )}
          </AnimatePresence>

          {mode === 'chat' && <MessageList messages={messages} isStreaming={isStreaming} />}

          {/* Mode toggle */}
          <Box
            sx={{
              display: 'flex',
              gap: 0.75,
              px: 1.5,
              pt: 1,
              pb: 0,
              borderTop: '1px solid rgba(160, 200, 255, 0.14)',
            }}
          >
            {(['chat', 'image', 'dataframe', 'research', 'tictactoe'] as const).map((m) => (
              <Button
                key={m}
                size="small"
                onClick={() => setMode(m)}
                variant={mode === m ? 'contained' : 'text'}
                startIcon={
                  m === 'chat'
                    ? <ChatIcon fontSize="small" />
                    : m === 'image'
                      ? <AutoFixHighIcon fontSize="small" />
                      : m === 'dataframe'
                        ? <TableChartIcon fontSize="small" />
                        : m === 'research'
                          ? <ScienceIcon fontSize="small" />
                          : <SportsEsportsIcon fontSize="small" />
                }
                sx={{
                  borderRadius: 999,
                  px: 1.75,
                  py: 0.4,
                  minHeight: 30,
                  fontSize: '0.78rem',
                  fontWeight: 580,
                  ...(mode === m
                    ? {
                        background: 'linear-gradient(135deg, #4e8dff 0%, #7d6dff 100%)',
                        boxShadow: '0 6px 18px rgba(70, 100, 220, 0.35)',
                      }
                    : { color: 'text.secondary' }),
                }}
              >
                {m === 'chat' ? 'Chat' : m === 'image' ? 'Generate Image' : m === 'dataframe' ? 'Sheets & CSV' : m === 'research' ? 'Research Digest' : 'Tic Tac Toe'}
              </Button>
            ))}
          </Box>

          {mode === 'chat' ? (
            <InputBar
              responseMode={responseMode}
              onResponseModeChange={setResponseMode}
              onSend={async ({ message, attachments, responseMode: selectedResponseMode }) => {
                try {
                  setError(null)
                  if (!resolvedActiveThreadId) {
                    const created = await createThreadMutation.mutateAsync()
                    setActiveThreadId(created.id)
                    await sendMessage(created.id, message, attachments, selectedResponseMode)
                    return
                  }
                  await sendMessage(resolvedActiveThreadId, message, attachments, selectedResponseMode)
                } catch (err) {
                  setError(err instanceof Error ? err.message : 'Failed to send message')
                }
              }}
              disabled={isStreaming}
            />
          ) : mode === 'image' ? (
            <ImageGenPanel
              threadId={resolvedActiveThreadId ?? undefined}
              onGenerated={() => setMode('chat')}
            />
          ) : mode === 'dataframe' ? (
            <DataframeQueryPanel />
          ) : mode === 'research' ? (
            <ResearchDigestPanel />
          ) : (
            <TicTacToePanel />
          )}
        </Box>
      </Box>
    </Box>
  )
}
