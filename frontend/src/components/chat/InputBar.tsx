import { useState } from 'react'
import { Box, TextField, Button, CircularProgress } from '@mui/material'
import SendIcon from '@mui/icons-material/Send'

interface InputBarProps {
  onSend: (message: string) => Promise<void>
  disabled?: boolean
}

export function InputBar({ onSend, disabled }: InputBarProps) {
  const [text, setText] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  return (
    <Box
      component="form"
      onSubmit={async (event: React.FormEvent) => {
        event.preventDefault()
        const value = text.trim()
        if (!value || isLoading) {
          return
        }
        setText('')
        setIsLoading(true)
        try {
          await onSend(value)
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
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
        <TextField
          fullWidth
          multiline
          maxRows={4}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Ask anything about your work..."
          disabled={disabled || isLoading}
          variant="outlined"
          size="small"
        />
        <Button
          type="submit"
          variant="contained"
          color="primary"
          disabled={disabled || isLoading || !text.trim()}
          endIcon={isLoading ? <CircularProgress size={20} /> : <SendIcon />}
          sx={{ height: '40px' }}
        >
          Send
        </Button>
      </Box>
    </Box>
  )
}
