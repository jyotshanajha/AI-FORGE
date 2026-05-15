import { useState } from 'react'
import { Alert, Box, Button, Chip, CircularProgress, Divider, MenuItem, TextField, Typography } from '@mui/material'
import TableChartIcon from '@mui/icons-material/TableChart'
import AttachFileIcon from '@mui/icons-material/AttachFile'

import { dataframeQuery, uploadAttachment } from '../../lib/api'
import type { ChatAttachment, DataframeQueryResponse } from '../../types/api'

type SourceMode = 'attachment' | 'google_sheet'

const ACCEPTED_EXTENSIONS = '.csv,.xls,.xlsx'

export function DataframeQueryPanel() {
  const [sourceMode, setSourceMode] = useState<SourceMode>('attachment')
  const [attachment, setAttachment] = useState<ChatAttachment | null>(null)
  const [question, setQuestion] = useState('')
  const [googleSheetId, setGoogleSheetId] = useState('')
  const [worksheetName, setWorksheetName] = useState('')
  const [result, setResult] = useState<DataframeQueryResponse | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.2, p: { xs: 1.2, md: 1.8 }, height: '100%', overflow: 'auto' }}>
      <Typography variant="h6" sx={{ lineHeight: 1.2 }}>
        CSV / Google Sheets Query Agent
      </Typography>
      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
        Upload a CSV or Excel file, or connect a Google Sheet, then ask questions in natural language.
      </Typography>

      <TextField
        select
        size="small"
        label="Data source"
        value={sourceMode}
        onChange={(event) => {
          setSourceMode(event.target.value as SourceMode)
          setError(null)
          setResult(null)
        }}
      >
        <MenuItem value="attachment">Uploaded CSV / Excel</MenuItem>
        <MenuItem value="google_sheet">Google Sheet</MenuItem>
      </TextField>

      {sourceMode === 'attachment' ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <input
            id="dataframe-upload-input"
            type="file"
            accept={ACCEPTED_EXTENSIONS}
            style={{ display: 'none' }}
            onChange={async (event) => {
              const file = event.target.files?.[0]
              if (!file) return
              setIsUploading(true)
              setError(null)
              try {
                const uploaded = await uploadAttachment(file)
                setAttachment(uploaded)
              } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to upload spreadsheet')
              } finally {
                setIsUploading(false)
                event.target.value = ''
              }
            }}
          />
          <Button
            component="label"
            htmlFor="dataframe-upload-input"
            variant="outlined"
            startIcon={isUploading ? <CircularProgress size={14} color="inherit" /> : <AttachFileIcon fontSize="small" />}
            disabled={isUploading}
            sx={{ borderRadius: 999, alignSelf: 'flex-start' }}
          >
            {attachment ? 'Replace file' : 'Upload CSV / Excel'}
          </Button>

          {attachment && (
            <Chip
              label={`${attachment.filename} (${attachment.attachment_type})`}
              onDelete={() => setAttachment(null)}
              sx={{ alignSelf: 'flex-start', maxWidth: 320 }}
            />
          )}
        </Box>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <TextField
            size="small"
            label="Google Sheet URL or ID"
            value={googleSheetId}
            onChange={(event) => setGoogleSheetId(event.target.value)}
            placeholder="https://docs.google.com/spreadsheets/d/... or sheet ID"
          />
          <TextField
            size="small"
            label="Worksheet name (optional)"
            value={worksheetName}
            onChange={(event) => setWorksheetName(event.target.value)}
            placeholder="Sheet1"
          />
        </Box>
      )}

      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
        <TextField
          fullWidth
          size="small"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Example: What are the columns and which category has the highest total?"
        />
        <Button
          variant="contained"
          startIcon={isLoading ? <CircularProgress size={14} color="inherit" /> : <TableChartIcon fontSize="small" />}
          disabled={
            isLoading
            || question.trim().length < 3
            || (sourceMode === 'attachment' ? !attachment : googleSheetId.trim().length < 10)
          }
          onClick={async () => {
            setError(null)
            setResult(null)
            setIsLoading(true)
            try {
              const response = await dataframeQuery({
                question: question.trim(),
                attachmentId: sourceMode === 'attachment' ? attachment?.id : undefined,
                googleSheetId: sourceMode === 'google_sheet' ? googleSheetId.trim() : undefined,
                worksheetName: sourceMode === 'google_sheet' && worksheetName.trim() ? worksheetName.trim() : undefined,
              })
              setResult(response)
            } catch (err) {
              setError(err instanceof Error ? err.message : 'Failed to query dataframe')
            } finally {
              setIsLoading(false)
            }
          }}
          sx={{ borderRadius: 999, minWidth: 140 }}
        >
          Query Data
        </Button>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}

      <Box
        sx={{
          flex: 1,
          minHeight: 260,
          borderRadius: 2,
          border: '1px solid rgba(159, 200, 255, 0.28)',
          background: 'rgba(14, 22, 44, 0.52)',
          p: 1.2,
          overflow: 'auto',
        }}
      >
        {!result ? (
          <Typography variant="body2" sx={{ color: 'text.secondary' }}>
            Query results will appear here, including answer, source details, row and column counts, and generated dataframe logic.
          </Typography>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.2 }}>
            <Typography variant="subtitle1">Answer</Typography>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
              {result.answer}
            </Typography>

            <Divider />

            <Typography variant="subtitle2">Source</Typography>
            <Typography variant="body2">{result.source_name}</Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              {result.row_count} rows · {result.column_count} columns
            </Typography>

            <Typography variant="subtitle2">Columns</Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75 }}>
              {result.columns.map((column) => (
                <Chip key={column} label={column} size="small" />
              ))}
            </Box>

            {result.generated_code && (
              <>
                <Typography variant="subtitle2">Generated Dataframe Expression</Typography>
                <Box component="pre" sx={{ m: 0, p: 1, borderRadius: 1.5, background: 'rgba(8, 13, 30, 0.9)', overflow: 'auto', fontSize: '0.82rem' }}>
                  {result.generated_code}
                </Box>
              </>
            )}

            {result.intermediate_steps.length > 0 && (
              <>
                <Typography variant="subtitle2">Intermediate Steps</Typography>
                <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
                  {result.intermediate_steps.map((step) => (
                    <Box component="li" key={step} sx={{ mb: 0.5, whiteSpace: 'pre-wrap', fontSize: '0.84rem' }}>
                      {step}
                    </Box>
                  ))}
                </Box>
              </>
            )}
          </Box>
        )}
      </Box>
    </Box>
  )
}
