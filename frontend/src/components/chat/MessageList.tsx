import { useEffect, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Box, Chip, Paper, Typography, Stack } from '@mui/material'
import DescriptionIcon from '@mui/icons-material/Description'
import TableChartIcon from '@mui/icons-material/TableChart'
import CodeIcon from '@mui/icons-material/Code'
import FunctionsIcon from '@mui/icons-material/Functions'
import AttachFileIcon from '@mui/icons-material/AttachFile'
import VideoFileIcon from '@mui/icons-material/VideoFile'
import LayersIcon from '@mui/icons-material/Layers'

import type { Message } from '../../types/api'

interface MessageListProps {
  messages: Message[]
  isStreaming: boolean
}

export function MessageList({ messages, isStreaming }: MessageListProps) {
  const viewportRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const node = viewportRef.current
    if (!node) return
    node.scrollTo({ top: node.scrollHeight, behavior: 'smooth' })
  }, [messages, isStreaming])

  return (
    <Box
      component="section"
      ref={viewportRef}
      sx={{
        flex: 1,
        overflowY: 'auto',
        px: { xs: 1.5, md: 2.5 },
        py: { xs: 1.25, md: 2 },
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      <Stack spacing={2}>
        <AnimatePresence initial={false}>
          {messages.map((message) => {
            const isUser = message.role === 'user'
            return (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 18, scale: 0.985 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ type: 'spring', stiffness: 220, damping: 24, mass: 0.8 }}
                style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' }}
              >
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    maxWidth: { xs: '94%', md: '78%' },
                    bgcolor: isUser ? 'rgba(84,129,255,0.72)' : 'rgba(17,29,58,0.72)',
                    color: '#eaf3ff',
                    borderRadius: 3,
                    border: isUser
                      ? '1px solid rgba(175,205,255,0.46)'
                      : '1px solid rgba(164,192,240,0.28)',
                    boxShadow: isUser
                      ? '0 14px 30px rgba(31,74,190,0.36)'
                      : '0 12px 26px rgba(5,11,30,0.44)',
                  }}
                >
                  <Box
                    sx={{
                      fontSize: '0.95rem',
                      lineHeight: 1.68,
                      textAlign: 'justify',
                      '& p': { m: 0, mb: 1 },
                      '& p:last-child': { mb: 0 },
                      '& code': {
                        bgcolor: isUser ? 'rgba(255,255,255,0.17)' : 'rgba(15,23,42,0.54)',
                        px: 0.75,
                        py: 0.25,
                        borderRadius: '6px',
                        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
                      },
                      '& pre': {
                        bgcolor: isUser ? 'rgba(255,255,255,0.12)' : 'rgba(15,23,42,0.54)',
                        p: 1.2,
                        borderRadius: 2,
                        overflow: 'auto',
                      },
                      '& blockquote': {
                        borderLeft: '3px solid currentColor',
                        pl: 1.4,
                        ml: 0,
                        opacity: 0.82,
                      },
                    }}
                  >
                    {message.content && (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                    )}

                    {message.attachments.length > 0 && (
                      <Box sx={{ mt: message.content ? 1.5 : 0 }}>
                        <Typography variant="caption" sx={{ opacity: 0.72, display: 'block', mb: 0.75 }}>
                          Attachments
                        </Typography>
                        <Stack spacing={1}>
                          {message.attachments.map((attachment) => {
                            if (attachment.mime_type.startsWith('image/')) {
                              return (
                                <Box key={attachment.id} sx={{ display: 'grid', gap: 0.5 }}>
                                  <Box
                                    component="img"
                                    src={attachment.download_url}
                                    alt={attachment.filename}
                                    sx={{
                                      width: '100%',
                                      maxWidth: 360,
                                      borderRadius: 2,
                                      border: '1px solid rgba(173,209,255,0.32)',
                                      boxShadow: '0 10px 24px rgba(4,10,28,0.42)',
                                    }}
                                  />
                                  <a
                                    href={attachment.download_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{ color: 'inherit', textDecoration: 'underline', fontSize: '0.8rem' }}
                                  >
                                    {attachment.filename}
                                  </a>
                                </Box>
                              )
                            }

                            if (attachment.mime_type.startsWith('video/')) {
                              return (
                                <Box key={attachment.id} sx={{ display: 'grid', gap: 0.5 }}>
                                  <Box
                                    component="video"
                                    controls
                                    src={attachment.download_url}
                                    sx={{
                                      width: '100%',
                                      maxWidth: 480,
                                      borderRadius: 2,
                                      border: '1px solid rgba(173,209,255,0.32)',
                                      boxShadow: '0 10px 24px rgba(4,10,28,0.42)',
                                      bgcolor: '#000',
                                    }}
                                  />
                                  <a
                                    href={attachment.download_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style={{ color: 'inherit', textDecoration: 'underline', fontSize: '0.8rem' }}
                                  >
                                    {attachment.filename}
                                  </a>
                                </Box>
                              )
                            }

                            const iconMap: Record<string, React.ReactElement> = {
                              document: <DescriptionIcon fontSize="small" />,
                              table: <TableChartIcon fontSize="small" />,
                              code: <CodeIcon fontSize="small" />,
                              formula: <FunctionsIcon fontSize="small" />,
                              video: <VideoFileIcon fontSize="small" />,
                            }
                            const icon = iconMap[attachment.attachment_type] ?? <AttachFileIcon fontSize="small" />

                            return (
                              <Box key={attachment.id}>
                                <Chip
                                  component="a"
                                  href={attachment.download_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  icon={icon}
                                  label={attachment.filename}
                                  clickable
                                  size="small"
                                  sx={{
                                    borderRadius: 999,
                                    background: 'rgba(20,35,72,0.78)',
                                    border: '1px solid rgba(126,167,229,0.38)',
                                    color: '#d0e8ff',
                                    maxWidth: '100%',
                                    '& .MuiChip-label': { overflow: 'hidden', textOverflow: 'ellipsis' },
                                  }}
                                />
                                {attachment.rag_info && (
                                  <Box sx={{ mt: 0.75, display: 'flex', gap: 0.6, flexWrap: 'wrap' }}>
                                    <Chip
                                      size="small"
                                      icon={<LayersIcon sx={{ fontSize: '0.82rem !important' }} />}
                                      label={`${attachment.rag_info.chunks_count} chunks indexed`}
                                      sx={{ fontSize: '0.7rem', height: 22, background: 'rgba(64,200,160,0.16)', border: '1px solid rgba(64,200,160,0.34)', color: '#80e8c8' }}
                                    />
                                    <Chip
                                      size="small"
                                      icon={<DescriptionIcon sx={{ fontSize: '0.82rem !important' }} />}
                                      label={`${attachment.rag_info.page_count} pages`}
                                      sx={{ fontSize: '0.7rem', height: 22, background: 'rgba(90,150,255,0.16)', border: '1px solid rgba(90,150,255,0.34)', color: '#a0c8ff' }}
                                    />
                                    <Chip
                                      size="small"
                                      label={`${(attachment.rag_info.characters_processed / 1000).toFixed(1)}k chars`}
                                      sx={{ fontSize: '0.7rem', height: 22, background: 'rgba(160,100,255,0.16)', border: '1px solid rgba(160,100,255,0.34)', color: '#c8a0ff' }}
                                    />
                                  </Box>
                                )}
                              </Box>
                            )
                          })}
                        </Stack>
                      </Box>
                    )}
                  </Box>
                </Paper>
              </motion.div>
            )
          })}
        </AnimatePresence>

        {isStreaming && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 0.5 }}>
              <Box sx={{ position: 'relative', width: 20, height: 20 }}>
                <motion.span
                  style={{
                    position: 'absolute',
                    inset: 0,
                    borderRadius: '50%',
                    border: '1px solid rgba(173,210,255,0.65)',
                  }}
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1.8, repeat: Infinity, ease: 'linear' }}
                />
                <motion.span
                  style={{
                    position: 'absolute',
                    top: 7,
                    left: 7,
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    background: 'rgba(194,233,255,0.95)',
                    boxShadow: '0 0 8px rgba(194,233,255,0.85)',
                  }}
                  animate={{ opacity: [0.55, 1, 0.6] }}
                  transition={{ duration: 1.2, repeat: Infinity, ease: 'easeInOut' }}
                />
              </Box>
              <Typography variant="caption" color="textSecondary">
                Transmitting across orbit...
              </Typography>
            </Box>
          </motion.div>
        )}
      </Stack>
    </Box>
  )
}
