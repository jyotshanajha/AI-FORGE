import { useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Box, Button, List, Stack, Typography, IconButton, TextField } from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import DoneIcon from '@mui/icons-material/Done'
import CloseIcon from '@mui/icons-material/Close'

import type { Thread } from '../../types/api'

interface ThreadSidebarProps {
  threads: Thread[]
  activeThreadId: string | null
  onSelectThread: (threadId: string) => void
  onCreateThread: () => void
  onRenameThread: (threadId: string, title: string) => void
  onDeleteThread: (threadId: string) => void
}

export function ThreadSidebar({
  threads,
  activeThreadId,
  onSelectThread,
  onCreateThread,
  onRenameThread,
  onDeleteThread,
}: ThreadSidebarProps) {
  const [editingThreadId, setEditingThreadId] = useState<string | null>(null)
  const [pendingTitle, setPendingTitle] = useState('')

  const sortedThreads = useMemo(
    () => [...threads].sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at)),
    [threads],
  )

  return (
    <Box
      component="aside"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        width: '100%',
        px: 1.5,
        py: 1,
        background: 'linear-gradient(180deg, rgba(18,30,64,0.74), rgba(12,20,44,0.52))',
        backdropFilter: 'blur(18px)',
        borderRight: '1px solid rgba(159, 198, 255, 0.22)',
      }}
    >
      <Box sx={{ px: 1, py: 1.25 }}>
        <Typography variant="caption" sx={{ color: 'text.secondary', letterSpacing: '0.08em' }}>
          CONVERSATIONS
        </Typography>
      </Box>

      <Box sx={{ p: 1 }}>
        <motion.div whileTap={{ scale: 0.985 }}>
          <Button
            fullWidth
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={onCreateThread}
            size="small"
            sx={{
              minHeight: 42,
              borderRadius: 999,
              boxShadow: '0 12px 24px rgba(70, 132, 255, 0.34)',
              background: 'linear-gradient(135deg, #4e8dff 0%, #7d6dff 100%)',
            }}
          >
            New Chat
          </Button>
        </motion.div>
      </Box>

      <List
        sx={{
          flex: 1,
          overflowY: 'auto',
          px: 0.5,
        }}
      >
        {sortedThreads.length === 0 && (
          <Box sx={{ px: 1.25, py: 3 }}>
            <Typography variant="caption" color="textSecondary" sx={{ textAlign: 'center', width: '100%' }}>
              No conversations yet. Create one to get started!
            </Typography>
          </Box>
        )}
        {sortedThreads.map((thread) => {
          const active = activeThreadId === thread.id
          const editing = editingThreadId === thread.id

          return (
            <motion.li
              key={thread.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.24, ease: 'easeOut' }}
              style={{ listStyle: 'none', marginBottom: 10 }}
            >
              <Box
                sx={{
                  borderRadius: 2.5,
                  px: 1.1,
                  py: 1,
                  cursor: 'pointer',
                  border: active ? '1px solid rgba(118, 176, 255, 0.45)' : '1px solid rgba(165, 203, 255, 0.22)',
                  background: active
                    ? 'linear-gradient(180deg, rgba(65,122,245,0.28), rgba(86,86,182,0.16))'
                    : 'linear-gradient(180deg, rgba(30,46,88,0.64), rgba(20,31,62,0.52))',
                  boxShadow: active
                    ? '0 14px 30px rgba(36, 84, 186, 0.34)'
                    : '0 8px 20px rgba(3, 7, 24, 0.4)',
                  transition: 'background 200ms ease, box-shadow 220ms ease, border-color 200ms ease',
                  '&:hover': {
                    boxShadow: '0 12px 24px rgba(21, 52, 123, 0.42)',
                    borderColor: 'rgba(116, 174, 255, 0.42)',
                  },
                }}
                onClick={() => onSelectThread(thread.id)}
              >
                <Stack direction="row" spacing={0.75} sx={{ alignItems: 'flex-start' }}>
                  <motion.div
                    animate={{ scale: [1, 1.25, 1], opacity: [0.45, 1, 0.55] }}
                    transition={{ duration: 3.4, repeat: Infinity, ease: 'easeInOut' }}
                    style={{
                      marginTop: 6,
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      background: active ? 'rgba(162, 220, 255, 0.96)' : 'rgba(155, 172, 211, 0.62)',
                      boxShadow: active ? '0 0 12px rgba(118, 210, 255, 0.88)' : 'none',
                    }}
                  />

                  <Box sx={{ minWidth: 0, flex: 1 }}>
                    {!editing && (
                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight: active ? 620 : 550,
                          width: '100%',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          mb: 0.25,
                        }}
                      >
                        {thread.title}
                      </Typography>
                    )}

                    <AnimatePresence>
                      {editing && (
                        <motion.div
                          initial={{ opacity: 0, y: -4 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -4 }}
                        >
                          <TextField
                            autoFocus
                            value={pendingTitle}
                            onClick={(event) => event.stopPropagation()}
                            onChange={(event) => setPendingTitle(event.target.value)}
                            size="small"
                            fullWidth
                            placeholder="Conversation title"
                            slotProps={{
                              input: {
                                sx: {
                                  fontSize: '0.85rem',
                                  borderRadius: 2,
                                  backgroundColor: 'rgba(14,24,52,0.72)',
                                },
                              },
                            }}
                          />
                        </motion.div>
                      )}
                    </AnimatePresence>

                    <Typography variant="caption" color="textSecondary">
                      {new Date(thread.created_at).toLocaleDateString()}
                    </Typography>
                  </Box>

                  <Stack direction="row" spacing={0.25}>
                    {!editing && (
                      <IconButton
                        size="small"
                        onClick={(event) => {
                          event.stopPropagation()
                          setEditingThreadId(thread.id)
                          setPendingTitle(thread.title)
                        }}
                        sx={{ color: 'text.secondary' }}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    )}

                    {editing && (
                      <>
                        <IconButton
                          size="small"
                          onClick={(event) => {
                            event.stopPropagation()
                            const next = pendingTitle.trim()
                            if (next) {
                              onRenameThread(thread.id, next)
                            }
                            setEditingThreadId(null)
                            setPendingTitle('')
                          }}
                          sx={{ color: 'primary.main' }}
                        >
                          <DoneIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={(event) => {
                            event.stopPropagation()
                            setEditingThreadId(null)
                            setPendingTitle('')
                          }}
                          sx={{ color: 'text.secondary' }}
                        >
                          <CloseIcon fontSize="small" />
                        </IconButton>
                      </>
                    )}

                    <IconButton
                      size="small"
                      onClick={(event) => {
                        event.stopPropagation()
                        onDeleteThread(thread.id)
                      }}
                      sx={{ color: '#b02b3d' }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Stack>
                </Stack>
              </Box>
            </motion.li>
          )
        })}
      </List>
    </Box>
  )
}
