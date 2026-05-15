import { useState } from 'react'
import { motion } from 'framer-motion'
import { Alert, Box, Button, CircularProgress, TextField, Typography } from '@mui/material'
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh'
import { useQueryClient } from '@tanstack/react-query'

import { generateImage } from '../../lib/api'

interface ImageGenPanelProps {
  threadId?: string
  onGenerated?: () => void
}

export function ImageGenPanel({ threadId, onGenerated }: ImageGenPanelProps) {
  const queryClient = useQueryClient()
  const [prompt, setPrompt] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastPrompt, setLastPrompt] = useState<string | null>(null)

  const handleGenerate = async () => {
    if (!prompt.trim()) return
    setIsGenerating(true)
    setError(null)
    try {
      const result = await generateImage(prompt, threadId)
      if (result.messageId && threadId) {
        await queryClient.invalidateQueries({ queryKey: ['messages', threadId] })
        await queryClient.invalidateQueries({ queryKey: ['threads'] })
      }
      setLastPrompt(prompt.trim())
      setPrompt('')
      onGenerated?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Image generation failed')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <Box
      sx={{
        borderTop: '1px solid rgba(157, 197, 255, 0.22)',
        background: 'linear-gradient(180deg, rgba(18,30,66,0.74), rgba(12,21,48,0.56))',
        backdropFilter: 'blur(14px)',
        px: { xs: 1.5, md: 2.5 },
        py: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 1.5,
      }}
    >
      <Typography
        variant="caption"
        sx={{ color: 'text.secondary', letterSpacing: '0.07em', fontWeight: 600 }}
      >
        ✦ DESCRIBE YOUR IMAGE — the more detail, the better
      </Typography>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ py: 0.5 }}>
          {error}
        </Alert>
      )}

      {lastPrompt && !error && (
        <Typography variant="caption" sx={{ color: '#7ab8ff', fontStyle: 'italic' }}>
          ✓ Generated: "{lastPrompt}"
        </Typography>
      )}

      <TextField
        fullWidth
        multiline
        minRows={3}
        maxRows={7}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Sunrise over mountain ridges, warm volumetric light, filmic realism..."
        disabled={isGenerating}
        variant="outlined"
        size="small"
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && !isGenerating) {
            handleGenerate()
          }
        }}
        slotProps={{
          input: { sx: { borderRadius: 3, background: 'rgba(16, 27, 56, 0.82)' } },
        }}
      />

      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <motion.div whileTap={{ scale: 0.975 }}>
          <Button
            variant="contained"
            disabled={!prompt.trim() || isGenerating}
            onClick={handleGenerate}
            startIcon={isGenerating ? <CircularProgress size={16} /> : <AutoFixHighIcon />}
            sx={{
              borderRadius: 999,
              px: 2.5,
              background: 'linear-gradient(135deg, #8d72ff 0%, #5a97ff 100%)',
              boxShadow: '0 12px 24px rgba(100, 80, 200, 0.42)',
            }}
          >
            {isGenerating ? 'Generating…' : 'Generate  ⌘↵'}
          </Button>
        </motion.div>
      </Box>
    </Box>
  )
}
