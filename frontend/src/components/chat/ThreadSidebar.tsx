import { Box, Button, List, ListItem, Stack, Typography, IconButton } from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'

import type { Thread } from '../../types/api'

interface ThreadSidebarProps {
  threads: Thread[]
  activeThreadId: string | null
  onSelectThread: (threadId: string) => void
  onCreateThread: () => void
  onRenameThread: (threadId: string) => void
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
  return (
    <Box
      component="aside"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        width: '100%',
        borderRight: '1px solid',
        borderColor: 'divider',
        bgcolor: 'background.paper',
      }}
    >
      <Box sx={{ p: 2 }}>
        <Button
          fullWidth
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={onCreateThread}
          size="small"
        >
          New Chat
        </Button>
      </Box>

      <List
        sx={{
          flex: 1,
          overflowY: 'auto',
          px: 1,
        }}
      >
        {threads.length === 0 && (
          <ListItem>
            <Typography variant="caption" color="textSecondary" sx={{ textAlign: 'center', width: '100%' }}>
              No conversations yet. Create one to get started!
            </Typography>
          </ListItem>
        )}
        {threads.map((thread) => {
          const active = activeThreadId === thread.id
          return (
            <ListItem
              key={thread.id}
              sx={{
                flexDirection: 'column',
                alignItems: 'flex-start',
                bgcolor: active ? 'action.selected' : 'transparent',
                borderRadius: 1,
                mb: 1,
                cursor: 'pointer',
                '&:hover': {
                  bgcolor: active ? 'action.selected' : 'action.hover',
                },
              }}
              onClick={() => onSelectThread(thread.id)}
            >
              <Typography
                variant="body2"
                sx={{
                  fontWeight: active ? 600 : 500,
                  width: '100%',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  mb: 0.5,
                }}
              >
                {thread.title}
              </Typography>
              <Typography variant="caption" color="textSecondary" sx={{ mb: 1 }}>
                {new Date(thread.created_at).toLocaleDateString()}
              </Typography>
              <Stack direction="row" spacing={0.5} sx={{ width: '100%' }}>
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation()
                    onRenameThread(thread.id)
                  }}
                >
                  <EditIcon fontSize="small" />
                </IconButton>
                <IconButton
                  size="small"
                  color="error"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDeleteThread(thread.id)
                  }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Stack>
            </ListItem>
          )
        })}
      </List>
    </Box>
  )
}
