import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Box, Paper, Typography, CircularProgress, Stack } from '@mui/material'

import type { Message } from '../../types/api'

interface MessageListProps {
  messages: Message[]
  isStreaming: boolean
}

export function MessageList({ messages, isStreaming }: MessageListProps) {
  return (
    <Box
      component="section"
      sx={{
        flex: 1,
        overflowY: 'auto',
        p: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      <Stack spacing={2}>
        {messages.map((message) => {
          const isUser = message.role === 'user'
          return (
            <Paper
              key={message.id}
              sx={{
                p: 2,
                maxWidth: '80%',
                alignSelf: isUser ? 'flex-end' : 'flex-start',
                bgcolor: isUser ? 'primary.main' : 'background.paper',
                color: isUser ? 'primary.contrastText' : 'text.primary',
                borderRadius: 2,
              }}
              elevation={1}
            >
              <Box
                sx={{
                  fontSize: '0.95rem',
                  lineHeight: 1.6,
                  textAlign: 'justify',
                  '& p': { m: 0, mb: 1 },
                  '& p:last-child': { mb: 0 },
                  '& code': {
                    bgcolor: isUser ? 'rgba(255,255,255,0.2)' : 'action.hover',
                    px: 0.75,
                    py: 0.25,
                    borderRadius: '4px',
                    fontFamily: 'monospace',
                  },
                  '& pre': {
                    bgcolor: isUser ? 'rgba(255,255,255,0.1)' : 'action.hover',
                    p: 1,
                    borderRadius: 1,
                    overflow: 'auto',
                  },
                  '& blockquote': {
                    borderLeft: '3px solid currentColor',
                    pl: 2,
                    ml: 0,
                    opacity: 0.8,
                  },
                }}
              >
                {message.content && <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>}

                {message.attachments.length > 0 && (
                  <Box sx={{ mt: message.content ? 1.5 : 0 }}>
                    <Typography variant="caption" sx={{ opacity: 0.8, display: 'block', mb: 0.5 }}>
                      Attachments
                    </Typography>
                    <Stack spacing={0.5}>
                      {message.attachments.map((attachment) => (
                        <a
                          key={attachment.id}
                          href={attachment.download_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ color: 'inherit', textDecoration: 'underline', fontSize: '0.85rem' }}
                        >
                          {attachment.filename} ({attachment.attachment_type})
                        </a>
                      ))}
                    </Stack>
                  </Box>
                )}
              </Box>
            </Paper>
          )
        })}
        {isStreaming && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CircularProgress size={20} />
            <Typography variant="caption" color="textSecondary">
              Streaming response...
            </Typography>
          </Box>
        )}
      </Stack>
    </Box>
  )
}
