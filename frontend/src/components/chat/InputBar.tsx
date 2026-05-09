import { useRef, useState } from 'react'
import { Box, TextField, Button, CircularProgress, Chip, Typography, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material'
import SendIcon from '@mui/icons-material/Send'
import AttachFileIcon from '@mui/icons-material/AttachFile'
import ImageIcon from '@mui/icons-material/Image'

import { uploadAttachment, generateImage } from '../../lib/api'
import type { ChatAttachment } from '../../types/api'

interface InputBarProps {
  onSend: (payload: { message: string; attachments: ChatAttachment[] }) => Promise<void>
  disabled?: boolean
  threadId?: string
}

const ACCEPTED_EXTENSIONS = [
  '.jpg,.jpeg,.png,.gif,.webp',
  '.mp4,.webm,.mov',
  '.csv,.xls,.xlsx',
  '.tex,.txt,.md,.json,.py,.js,.ts,.tsx',
].join(',')

export function InputBar({ onSend, disabled, threadId }: InputBarProps) {
  const [text, setText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [isGeneratingImage, setIsGeneratingImage] = useState(false)
  const [attachments, setAttachments] = useState<ChatAttachment[]>([])
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [imageDialogOpen, setImageDialogOpen] = useState(false)
  const [imagePrompt, setImagePrompt] = useState('')
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  return (
    <Box
      component="form"
      onSubmit={async (event: React.FormEvent) => {
        event.preventDefault()
        const value = text.trim()
        if ((!value && attachments.length === 0) || isLoading || isUploading || isGeneratingImage) {
          return
        }

        const pendingAttachments = [...attachments]
        setText('')
        setIsLoading(true)
        setUploadError(null)
        try {
          await onSend({ message: value, attachments: pendingAttachments })
          setAttachments([])
        } finally {
          setIsLoading(false)
        }
      }}
      sx={{
        borderTop: '1px solid',
        borderColor: 'divider',
        bgcolor: 'background.paper',
        p: 2,
      }}
    >
      {attachments.length > 0 && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1 }}>
          {attachments.map((attachment) => (
            <Chip
              key={attachment.id}
              label={`${attachment.filename} (${attachment.attachment_type})`}
              onDelete={() => setAttachments((prev) => prev.filter((item) => item.id !== attachment.id))}
              size="small"
            />
          ))}
        </Box>
      )}

      {uploadError && (
        <Typography variant="caption" color="error" sx={{ display: 'block', mb: 1 }}>
          {uploadError}
        </Typography>
      )}

      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ACCEPTED_EXTENSIONS}
          style={{ display: 'none' }}
          onChange={async (event) => {
            const files = Array.from(event.target.files ?? [])
            if (files.length === 0) {
              return
            }

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

        <Button
          type="button"
          variant="outlined"
          color="secondary"
          disabled={disabled || isLoading || isUploading || isGeneratingImage}
          onClick={() => fileInputRef.current?.click()}
          sx={{ minWidth: '44px', height: '40px', px: 1 }}
        >
          {isUploading ? <CircularProgress size={20} /> : <AttachFileIcon />}
        </Button>

        <Button
          type="button"
          variant="outlined"
          color="secondary"
          disabled={disabled || isLoading || isUploading || isGeneratingImage}
          onClick={() => setImageDialogOpen(true)}
          sx={{ minWidth: '44px', height: '40px', px: 1 }}
        >
          {isGeneratingImage ? <CircularProgress size={20} /> : <ImageIcon />}
        </Button>

        <TextField
          fullWidth
          multiline
          maxRows={4}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Ask anything about your work..."
          disabled={disabled || isLoading || isUploading || isGeneratingImage}
          variant="outlined"
          size="small"
        />

        <Button
          type="submit"
          variant="contained"
          color="primary"
          disabled={disabled || isLoading || isUploading || isGeneratingImage || (!text.trim() && attachments.length === 0)}
          endIcon={isLoading ? <CircularProgress size={20} /> : <SendIcon />}
          sx={{ height: '40px' }}
        >
          Send
        </Button>
      </Box>

      <Dialog open={imageDialogOpen} onClose={() => setImageDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Generate Image</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            multiline
            maxRows={4}
            value={imagePrompt}
            onChange={(e) => setImagePrompt(e.target.value)}
            placeholder="Describe the image you want to generate..."
            variant="outlined"
            size="small"
            sx={{ mt: 2 }}
            disabled={isGeneratingImage}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImageDialogOpen(false)} disabled={isGeneratingImage}>
            Cancel
          </Button>
          <Button
            onClick={async () => {
              if (!imagePrompt.trim()) {
                return
              }
              setIsGeneratingImage(true)
              setUploadError(null)
              try {
                const image = await generateImage(imagePrompt, threadId)
                setAttachments((prev) => [...prev, image])
                setImagePrompt('')
                setImageDialogOpen(false)
              } catch (error) {
                setUploadError(error instanceof Error ? error.message : 'Image generation failed')
              } finally {
                setIsGeneratingImage(false)
              }
            }}
            variant="contained"
            color="primary"
            disabled={!imagePrompt.trim() || isGeneratingImage}
          >
            {isGeneratingImage ? <CircularProgress size={20} /> : 'Generate'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
