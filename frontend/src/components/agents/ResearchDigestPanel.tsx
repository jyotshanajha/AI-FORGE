import { useEffect, useRef, useState } from 'react'
import { Box, Button, CircularProgress, TextField, Typography } from '@mui/material'
import ScienceIcon from '@mui/icons-material/Science'
import StopIcon from '@mui/icons-material/Stop'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { streamResearchDigest } from '../../lib/api'

type SourcePaper = { title: string; id: string; published: string; authors: string[] }

interface Props {
  onBack: () => void
}

function PanelBox({ title, children, sx = {} }: { title: string; children: React.ReactNode; sx?: object }) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        borderRadius: 2.5,
        border: '1px solid rgba(159, 200, 255, 0.16)',
        background: 'rgba(8, 14, 32, 0.62)',
        overflow: 'hidden',
        ...sx,
      }}
    >
      <Typography
        variant="subtitle2"
        sx={{
          px: 1.8, py: 1.1, fontWeight: 700,
          borderBottom: '1px solid rgba(159, 200, 255, 0.1)',
          color: '#c8deff', letterSpacing: '0.01em', flexShrink: 0,
        }}
      >
        {title}
      </Typography>
      <Box sx={{ flex: 1, overflow: 'auto', p: 1.5, minHeight: 0 }}>{children}</Box>
    </Box>
  )
}

function NumInput({ label, value, min, max, disabled, onChange }: {
  label: string; value: number; min: number; max: number; disabled: boolean; onChange: (v: number) => void
}) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.4, flex: 1 }}>
      <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 600, fontSize: '0.7rem', whiteSpace: 'nowrap' }}>
        {label}
      </Typography>
      <TextField
        size="small" type="number" value={value} disabled={disabled}
        onChange={(e) => { const v = Number(e.target.value); if (Number.isFinite(v)) onChange(Math.max(min, Math.min(max, Math.round(v)))) }}
        slotProps={{ htmlInput: { min, max, step: 1 } }}
        sx={{ '& .MuiInputBase-input': { textAlign: 'center', py: 0.7, fontSize: '0.9rem', fontWeight: 600 } }}
      />
    </Box>
  )
}

export function ResearchDigestPanel({ onBack }: Props) {
  const [query, setQuery] = useState('')
  const [maxRounds, setMaxRounds] = useState(3)
  const [papersPerRound, setPapersPerRound] = useState(5)
  const [minPapers, setMinPapers] = useState(6)

  const [statusLines, setStatusLines] = useState<string[]>([])
  const [sources, setSources] = useState<SourcePaper[]>([])
  const [digest, setDigest] = useState('')

  const [statusCount, setStatusCount] = useState(0)
  const [papersFound, setPapersFound] = useState(0)
  const [decisionCount, setDecisionCount] = useState(0)

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const abortRef = useRef<AbortController | null>(null)
  const statusBoxRef = useRef<HTMLDivElement | null>(null)
  const digestBoxRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const el = statusBoxRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [statusLines])

  useEffect(() => {
    const el = digestBoxRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [digest])

  const handleRun = async () => {
    if (!query.trim() || query.trim().length < 3) return
    setError(null); setDigest(''); setStatusLines([]); setSources([])
    setStatusCount(0); setPapersFound(0); setDecisionCount(0)
    setIsLoading(true)
    const ctrl = new AbortController()
    abortRef.current = ctrl
    try {
      await streamResearchDigest(
        query.trim(),
        (event) => {
          if (event.type === 'token') { setDigest((p) => p + event.token); return }
          if (event.type === 'status') { setStatusLines((p) => [...p, event.message]); setStatusCount((n) => n + 1); return }
          if (event.type === 'evidence_decision') {
            const pct = `${Math.round(event.confidence * 100)}%`
            const icon = event.enough_evidence ? '[+]' : '[~]'
            setStatusLines((p) => [...p, `  ${icon} Evidence (${pct}): ${event.reason}`])
            setDecisionCount((n) => n + 1); return
          }
          if (event.type === 'meta') {
            setPapersFound(event.papers_found)
            setStatusLines((p) => [...p, `[+] Collected ${event.papers_found} papers in ${event.rounds_executed ?? '?'} rounds`]); return
          }
          if (event.type === 'sources') { setSources(event.papers); return }
          if (event.type === 'error') { setError(event.message) }
        },
        { maxPapers: minPapers, maxRounds, papersPerRound, signal: ctrl.signal },
      )
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        setStatusLines((p) => [...p, '-- Stopped by user.'])
      } else {
        setError(err instanceof Error ? err.message : 'Failed to stream research digest')
      }
    } finally {
      abortRef.current = null; setIsLoading(false)
    }
  }

  const monoFont = 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace'
  const dim = 'rgba(130, 165, 220, 0.38)'

  return (
    <Box sx={{ display: 'flex', flexDirection: 'row', height: '100%', gap: 1.5, overflow: 'hidden' }}>
      {/* â”€â”€ Left sidebar â”€â”€ */}
      <Box sx={{
        width: 340, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 1.4,
        borderRadius: 2.5, border: '1px solid rgba(159, 200, 255, 0.14)',
        background: 'rgba(8, 14, 32, 0.55)', p: 2, overflow: 'hidden',
      }}>
        <Box>
          <Typography variant="caption" sx={{ color: 'text.secondary', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', fontSize: '0.66rem' }}>
            Project 10
          </Typography>
          <Typography variant="h6" sx={{ fontWeight: 700, lineHeight: 1.25, mt: 0.3 }}>
            Research Digest Agent
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary', lineHeight: 1.4, display: 'block', mt: 0.3 }}>
            Autonomous arXiv exploration with real-time digest streaming.
          </Typography>
        </Box>

        <Box>
          <Typography variant="caption" sx={{ fontWeight: 600, color: 'text.secondary', mb: 0.5, display: 'block' }}>
            Topic
          </Typography>
          <TextField
            fullWidth multiline minRows={4} maxRows={7}
            disabled={isLoading} value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Describe the research area to investigate"
            sx={{ '& .MuiInputBase-input': { fontSize: '0.88rem', lineHeight: 1.55 } }}
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <NumInput label="Max Rounds" value={maxRounds} min={1} max={10} disabled={isLoading} onChange={setMaxRounds} />
          <NumInput label="Papers / Round" value={papersPerRound} min={2} max={15} disabled={isLoading} onChange={setPapersPerRound} />
          <NumInput label="Minimum Papers" value={minPapers} min={3} max={20} disabled={isLoading} onChange={setMinPapers} />
        </Box>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button variant="contained"
            startIcon={isLoading ? <CircularProgress size={14} color="inherit" /> : <ScienceIcon fontSize="small" />}
            disabled={isLoading || query.trim().length < 3} onClick={handleRun}
            sx={{ flex: 1, borderRadius: 999, minWidth: 100 }}>
            {isLoading ? 'Running...' : 'Run Agent'}
          </Button>
          <Button variant="outlined" startIcon={<StopIcon fontSize="small" />}
            disabled={!isLoading} onClick={() => abortRef.current?.abort()}
            sx={{ borderRadius: 999, minWidth: 78 }}>
            Stop
          </Button>
          <Button variant="outlined" color="inherit" startIcon={<ArrowBackIcon fontSize="small" />}
            onClick={onBack}
            sx={{ borderRadius: 999, minWidth: 118, color: 'text.secondary', borderColor: 'rgba(159,200,255,0.22)' }}>
            Back To Chat
          </Button>
        </Box>

        {error && (
          <Typography variant="caption" sx={{ color: '#ff7070', background: 'rgba(255,80,80,0.08)', borderRadius: 1.5, p: 1, display: 'block' }}>
            {error}
          </Typography>
        )}

        <Typography variant="caption" sx={{ color: 'text.secondary', mt: 'auto', pt: 1, fontSize: '0.76rem' }}>
          Statuses:&nbsp;{statusCount}&nbsp;&nbsp;Papers:&nbsp;{papersFound}&nbsp;&nbsp;Decisions:&nbsp;{decisionCount}
        </Typography>
      </Box>

      {/* â”€â”€ Right area â”€â”€ */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 1.5, minWidth: 0, minHeight: 0, overflow: 'hidden' }}>
        {/* Top row: Status + Papers */}
        <Box sx={{ display: 'flex', gap: 1.5, flex: 1, minHeight: 0 }}>
          <PanelBox title="Status" sx={{ flex: 3 }}>
            <Box ref={statusBoxRef} sx={{ fontFamily: monoFont, fontSize: '0.75rem', lineHeight: 1.6, color: 'rgba(180, 210, 255, 0.88)', whiteSpace: 'pre-wrap', wordBreak: 'break-word', height: '100%' }}>
              {statusLines.length === 0
                ? <Box component="span" sx={{ color: dim }}>No status yet.</Box>
                : statusLines.join('\n')}
            </Box>
          </PanelBox>

          <PanelBox title="Papers" sx={{ flex: 2 }}>
            {sources.length === 0
              ? <Typography variant="caption" sx={{ color: dim }}>No papers yet.</Typography>
              : <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.8 }}>
                  {sources.map((paper, i) => (
                    <Box key={`${paper.id}-${i}`}>
                      <a href={paper.id} target="_blank" rel="noreferrer noopener"
                        style={{ color: '#7ec8f0', textDecoration: 'none', fontSize: '0.75rem', fontWeight: 600, lineHeight: 1.35, display: 'block' }}>
                        {i + 1}. {paper.title}
                      </a>
                      <Typography variant="caption" sx={{ color: 'rgba(160,190,240,0.5)', ml: 1.5, fontSize: '0.68rem', display: 'block' }}>
                        {paper.authors.slice(0, 2).join(', ')}{paper.authors.length > 2 ? ' et al.' : ''} - {paper.published}
                      </Typography>
                    </Box>
                  ))}
                </Box>
            }
          </PanelBox>
        </Box>

        {/* Bottom row: Structured Digest */}
        <PanelBox title="Structured Digest" sx={{ flex: 2, minHeight: 0 }}>
          <Box ref={digestBoxRef} sx={{
            height: '100%', overflow: 'auto', fontSize: '0.9rem', lineHeight: 1.6, color: '#ddeeff',
            '& h1,& h2,& h3': { color: '#aad4ff', marginTop: 1.2, marginBottom: 0.5 },
            '& h2': { borderBottom: '1px solid rgba(100,160,255,0.18)', paddingBottom: 0.3 },
            '& p': { marginTop: 0, marginBottom: 0.8 },
            '& ul, & ol': { marginTop: 0.2, marginBottom: 0.7, paddingLeft: 2.2 },
            '& li': { marginBottom: 0.25 },
            '& strong': { color: '#c8e6ff' },
            '& code': { fontFamily: monoFont, fontSize: '0.8rem', background: 'rgba(255,255,255,0.07)', padding: '0.06rem 0.3rem', borderRadius: '0.3rem' },
            '& pre': { background: 'rgba(0,0,0,0.28)', border: '1px solid rgba(100,160,255,0.2)', borderRadius: 1, p: 1, overflow: 'auto' },
            '& blockquote': { m: 0, pl: 1.2, borderLeft: '3px solid rgba(100,160,255,0.4)', color: 'rgba(200,225,255,0.75)' },
            '& a': { color: '#7ec8f0' },
            '& hr': { borderColor: 'rgba(100,160,255,0.18)', my: 0.8 },
            textAlign: 'justify',
          }}>
            {digest
              ? <ReactMarkdown remarkPlugins={[remarkGfm]}
                  components={{ a: ({ href, children, ...p }) => <a href={href} target="_blank" rel="noreferrer noopener" {...p}>{children}</a> }}>
                  {digest}
                </ReactMarkdown>
              : <Typography variant="body2" sx={{ color: dim }}>
                  {isLoading ? 'Waiting for LLM synthesis...' : 'Digest content will stream here.'}
                </Typography>
            }
          </Box>
        </PanelBox>
      </Box>
    </Box>
  )
}
