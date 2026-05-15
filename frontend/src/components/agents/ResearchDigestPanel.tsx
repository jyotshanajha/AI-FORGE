import { useState } from 'react'
import { Alert, Box, Button, CircularProgress, TextField, Typography } from '@mui/material'
import ScienceIcon from '@mui/icons-material/Science'

import { streamResearchDigest } from '../../lib/api'

export function ResearchDigestPanel() {
  const [query, setQuery] = useState('')
  const [digest, setDigest] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.2, p: { xs: 1.2, md: 1.8 }, height: '100%', overflow: 'auto' }}>
      <Typography variant="h6" sx={{ lineHeight: 1.2 }}>
        Research Digest Agent
      </Typography>
      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
        Searches arXiv and streams a structured digest in real time.
      </Typography>

      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
        <TextField
          fullWidth
          size="small"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Example: retrieval augmented generation for enterprise search"
        />
        <Button
          variant="contained"
          startIcon={isLoading ? <CircularProgress size={14} color="inherit" /> : <ScienceIcon fontSize="small" />}
          disabled={isLoading || query.trim().length < 3}
          onClick={async () => {
            setError(null)
            setDigest('')
            setIsLoading(true)
            try {
              await streamResearchDigest(query.trim(), (event) => {
                setDigest((current) => current + event.token)
              })
            } catch (err) {
              setError(err instanceof Error ? err.message : 'Failed to stream research digest')
            } finally {
              setIsLoading(false)
            }
          }}
          sx={{ borderRadius: 999, minWidth: 130 }}
        >
          Digest
        </Button>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}

      <Box
        sx={{
          flex: 1,
          minHeight: 220,
          borderRadius: 2,
          border: '1px solid rgba(159, 200, 255, 0.28)',
          background: 'rgba(14, 22, 44, 0.52)',
          p: 1.2,
          overflow: 'auto',
          whiteSpace: 'pre-wrap',
          fontSize: '0.92rem',
          lineHeight: 1.56,
        }}
      >
        {digest || 'Your streamed digest will appear here...'}
      </Box>
    </Box>
  )
}
