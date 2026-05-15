import { useMemo, useState } from 'react'
import { Alert, Box, Button, Typography } from '@mui/material'
import SportsEsportsIcon from '@mui/icons-material/SportsEsports'

import { ticTacToeMove } from '../../lib/api'

const EMPTY_BOARD = ['', '', '', '', '', '', '', '', '']

export function TicTacToePanel() {
  const [board, setBoard] = useState<string[]>([...EMPTY_BOARD])
  const [status, setStatus] = useState('Your turn (X)')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isFinished = useMemo(() => {
    return status.toLowerCase().includes('wins') || status.toLowerCase().includes('draw')
  }, [status])

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.2, p: { xs: 1.2, md: 1.8 }, height: '100%', overflow: 'auto' }}>
      <Typography variant="h6" sx={{ lineHeight: 1.2 }}>
        Tic Tac Toe Agent
      </Typography>
      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
        Play against an unbeatable agent.
      </Typography>

      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 1, maxWidth: 320 }}>
        {board.map((cell, index) => (
          <Button
            key={index}
            variant="outlined"
            disabled={isLoading || !!cell || isFinished}
            onClick={async () => {
              setError(null)
              setIsLoading(true)
              try {
                const result = await ticTacToeMove(board, index)
                setBoard(result.board)
                if (result.status === 'finished' && result.winner) {
                  setStatus(`${result.winner} wins`)
                } else if (result.status === 'draw') {
                  setStatus('Draw')
                } else {
                  setStatus('Your turn (X)')
                }
              } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to apply move')
              } finally {
                setIsLoading(false)
              }
            }}
            sx={{
              aspectRatio: '1 / 1',
              borderRadius: 2,
              minHeight: 88,
              fontSize: '2rem',
              fontWeight: 700,
              color: cell === 'X' ? '#8dd8ff' : '#ffbf83',
              borderColor: 'rgba(141, 194, 255, 0.32)',
              background: 'rgba(12, 20, 42, 0.45)',
            }}
          >
            {cell || <SportsEsportsIcon fontSize="small" sx={{ opacity: 0.2 }} />}
          </Button>
        ))}
      </Box>

      <Typography variant="body2" sx={{ color: 'text.secondary' }}>
        {isLoading ? 'Agent is thinking...' : status}
      </Typography>

      {error && <Alert severity="error">{error}</Alert>}

      <Button
        variant="text"
        onClick={() => {
          setBoard([...EMPTY_BOARD])
          setStatus('Your turn (X)')
          setError(null)
        }}
        sx={{ alignSelf: 'flex-start', borderRadius: 999 }}
      >
        Restart
      </Button>
    </Box>
  )
}
