import { useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { Alert, Box, Button, Chip, CircularProgress, TextField, Typography } from '@mui/material'
import SendIcon from '@mui/icons-material/Send'
import AttachFileIcon from '@mui/icons-material/AttachFile'
import DescriptionIcon from '@mui/icons-material/Description'
import SmartToyIcon from '@mui/icons-material/SmartToy'

import { uploadAttachment } from '../../lib/api'
import type { ChatAttachment, ChatResponseMode } from '../../types/api'

interface InputBarProps {
  onSend: (payload: { message: string; attachments: ChatAttachment[]; responseMode: ChatResponseMode }) => Promise<void>
  responseMode: ChatResponseMode
  onResponseModeChange: (mode: ChatResponseMode) => void
  disabled?: boolean
}

const ACCEPTED_EXTENSIONS = [
  '.jpg,.jpeg,.png,.gif,.webp',
  '.mp4,.webm,.mov',
  '.pdf',
  '.csv,.xls,.xlsx',
  '.tex,.txt,.md,.json,.py,.js,.ts,.tsx',
].join(',')

export function InputBar({ onSend, responseMode, onResponseModeChange, disabled }: InputBarProps) {
  const [text, setText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [attachments, setAttachments] = useState<ChatAttachment[]>([])
  const [uploadError, setUploadError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  return (
    <Box
      component="form"
      onSubmit={async (event: React.FormEvent) => {
        event.preventDefault()
        const value = text.trim()
        if ((!value && attachments.length === 0) || isLoading || isUploading) return

        const pendingAttachments = [...attachments]
        setText('')
        setIsLoading(true)
        setUploadError(null)
        try {
          await onSend({ message: value, attachments: pendingAttachments, responseMode })
          setAttachments([])
        } finally {
          setIsLoading(false)
        }
      }}
      sx={{
        borderTop: '1px solid rgba(157,197,255,0.22)',
        background: 'linear-gradient(180deg, rgba(18,30,66,0.74), rgba(12,21,48,0.56))',
        backdropFilter: 'blur(14px)',
        px: { xs: 1.2, md: 2 },
        py: { xs: 1.2, md: 1.4 },
      }}
    >
      {attachments.length > 0 && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1.2 }}>
          {attachments.map((attachment) => (
            <Box key={attachment.id} sx={{ display: 'flex', flexDirection: 'column', gap: 0.4 }}>
              <Chip
                label={`${attachment.filename} (${attachment.attachment_type})`}
                onDelete={() => setAttachments((prev) => prev.filter((a) => a.id !== attachment.id))}
                size="small"
                sx={{
                  borderRadius: 999,
                  background: 'rgba(20, 33, 68, 0.72)',
                  border: '1px solid rgba(126,167,229,0.35)',
                  maxWidth: 260,
                }}
              />
              {attachment.rag_info && (
                <Typography variant="caption" sx={{ color: '#7ab8ff', pl: 0.75, fontSize: '0.72rem' }}>
                  📄 {attachment.rag_info.page_count} pages · {attachment.rag_info.chunks_count} chunks indexed
                </Typography>
              )}
            </Box>
          ))}
        </Box>
      )}

      {uploadError && (
        <Alert severity="error" onClose={() => setUploadError(null)} sx={{ mb: 1, py: 0.5 }}>
          {uploadError}
        </Alert>
      )}

      <Box sx={{ display: 'flex', gap: 0.8, mb: 1, flexWrap: 'wrap' }}>
        <Button
          type="button"
          size="small"
          variant={responseMode === 'rag' ? 'contained' : 'outlined'}
          startIcon={<DescriptionIcon fontSize="small" />}
          onClick={() => onResponseModeChange('rag')}
          sx={{
            borderRadius: 999,
            minHeight: 28,
            px: 1.25,
            fontSize: '0.72rem',
            ...(responseMode === 'rag'
              ? {
                  background: 'linear-gradient(135deg, #2eb89a 0%, #33c6a2 100%)',
                  color: '#07231f',
                }
              : {
                  borderColor: 'rgba(117, 224, 194, 0.35)',
                  color: '#8de8cc',
                }),
          }}
        >
          RAG
        </Button>
        <Button
          type="button"
          size="small"
          variant={responseMode === 'llm' ? 'contained' : 'outlined'}
          startIcon={<SmartToyIcon fontSize="small" />}
          onClick={() => onResponseModeChange('llm')}
          sx={{
            borderRadius: 999,
            minHeight: 28,
            px: 1.25,
            fontSize: '0.72rem',
            ...(responseMode === 'llm'
              ? {
                  background: 'linear-gradient(135deg, #6aa1ff 0%, #7c84ff 100%)',
                  color: '#f3f7ff',
                }
              : {
                  borderColor: 'rgba(132, 178, 255, 0.34)',
                  color: '#b7d3ff',
                }),
          }}
        >
          LLM
        </Button>
        <Button
          type="button"
          size="small"
          variant={responseMode === 'sql' ? 'contained' : 'outlined'}
          startIcon={<DescriptionIcon fontSize="small" />}
          onClick={() => onResponseModeChange('sql')}
          sx={{
            borderRadius: 999,
            minHeight: 28,
            px: 1.25,
            fontSize: '0.72rem',
            ...(responseMode === 'sql'
              ? {
                  background: 'linear-gradient(135deg, #ffb347 0%, #ffcc80 100%)',
                  color: '#4a2c00',
                }
              : {
                  borderColor: 'rgba(255, 183, 77, 0.35)',
                  color: '#ffb347',
                }),
          }}
        >
          SQL
        </Button>
      </Box>

      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ACCEPTED_EXTENSIONS}
          style={{ display: 'none' }}
          onChange={async (event) => {
            const files = Array.from(event.target.files ?? [])
            if (files.length === 0) return
            setIsUploading(true)
            setUploadError(null)
            try {
              const uploaded = await Promise.all(files.map((file) => uploadAttachment(file)))
              setAttachments((prev) => [...prev, ...uploaded])
            } catch (error) {
              setUploadError(error instanceof Error ? error.message : 'Attachment upload failed')
            } finally {
              setIsUploading(false)
              event.target.value = ''
            }
          }}
        />

        <motion.div whileHover={{ y: -1 }} whileTap={{ scale: 0.97 }}>
          <Button
            type="button"
            variant="outlined"
            color="secondary"
            disabled={disabled || isLoading || isUploading}
            onClick={() => fileInputRef.current?.click()}
            sx={{
              minWidth: 42,
              height: 42,
              px: 1,
              borderRadius: 999,
              borderColor: 'rgba(132,178,255,0.34)',
              backgroundColor: 'rgba(17,29,60,0.62)',
              flexShrink: 0,
            }}
          >
            {isUploading ? <CircularProgress size={18} /> : <AttachFileIcon fontSize="small" />}
          </Button>
        </motion.div>

        <TextField
          fullWidth
          multiline
          maxRows={4}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey && !disabled && !isLoading && !isUploading) {
              e.preventDefault()
              ;(e.currentTarget.closest('form') as HTMLFormElement | null)?.requestSubmit()
            }
          }}
          placeholder="Ask anything... (Enter to send, Shift+Enter for newline)"
          disabled={disabled || isLoading || isUploading}
          variant="outlined"
          size="small"
          slotProps={{
            input: { sx: { borderRadius: 3, background: 'rgba(16,27,56,0.82)' } },
          }}
        />

        <motion.div whileTap={{ scale: 0.975 }} style={{ flexShrink: 0 }}>
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={disabled || isLoading || isUploading || (!text.trim() && attachments.length === 0)}
            endIcon={isLoading ? <CircularProgress size={18} /> : <SendIcon />}
            sx={{
              height: 42,
              borderRadius: 999,
              px: { xs: 1.5, md: 2 },
              background: 'linear-gradient(135deg, #5a97ff 0%, #8d72ff 100%)',
              boxShadow: '0 12px 24px rgba(56, 85, 186, 0.42)',
              whiteSpace: 'nowrap',
            }}
          >
            Launch
          </Button>
        </motion.div>
      </Box>
    </Box>
  )
}
