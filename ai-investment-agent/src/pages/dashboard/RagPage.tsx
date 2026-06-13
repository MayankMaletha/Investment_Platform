import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, FileText, Search, X, CheckCircle, AlertCircle, Loader2, ExternalLink } from 'lucide-react'
import { useRagDocuments, useRagUpload, useRagQuery } from '../../hooks'
import { TableSkeleton } from '../../components/ui/LoadingSkeleton'
import { formatDate } from '../../lib/utils'
import type { RagQueryResponse, RagDocument } from '../../types'

const ACCEPTED = '.pdf,.docx,.txt,.xlsx'

function DocumentRow({ doc }: { doc: RagDocument }) {
  const statusIcon =
    doc.status === 'ready' ? <CheckCircle className="w-4 h-4 text-accent-green" /> :
    doc.status === 'error' ? <AlertCircle className="w-4 h-4 text-accent-red" /> :
    <Loader2 className="w-4 h-4 text-accent-yellow animate-spin" />

  const ext = doc.filename.split('.').pop()?.toUpperCase() || 'FILE'

  return (
    <div className="flex items-center gap-3 p-3 bg-surface-700 rounded-lg hover:bg-surface-600 transition-colors">
      <div className="w-9 h-9 bg-surface-600 rounded-lg flex items-center justify-center flex-shrink-0">
        <span className="text-xs font-bold text-slate-400">{ext}</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-slate-200 truncate">{doc.filename}</div>
        <div className="text-xs text-slate-500">
          {doc.chunk_count ? `${doc.chunk_count} chunks` : ''} · {(doc.size / 1024).toFixed(1)} KB · {formatDate(doc.uploaded_at)}
        </div>
      </div>
      <div className="flex items-center gap-2">
        {statusIcon}
        <span className="text-xs text-slate-500 capitalize">{doc.status}</span>
      </div>
    </div>
  )
}

function CitationCard({ citation }: { citation: { filename: string; page?: number; chunk_text: string; score: number } }) {
  return (
    <div className="border border-surface-500 rounded-lg p-3 bg-surface-700/50">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <FileText className="w-3.5 h-3.5 text-brand-400" />
          <span className="text-xs font-medium text-brand-400">{citation.filename}</span>
          {citation.page && <span className="text-xs text-slate-500">· Page {citation.page}</span>}
        </div>
        <span className="text-xs text-slate-500 bg-surface-600 px-2 py-0.5 rounded">
          {(citation.score * 100).toFixed(0)}% match
        </span>
      </div>
      <p className="text-xs text-slate-400 leading-relaxed line-clamp-3">{citation.chunk_text}</p>
    </div>
  )
}

export function RagPage() {
  const [queryText, setQueryText] = useState('')
  const [queryResult, setQueryResult] = useState<RagQueryResponse | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: documents, isLoading: loadingDocs } = useRagDocuments()
  const upload = useRagUpload()
  const query = useRagQuery()

  const handleFiles = (files: FileList | null) => {
    if (!files) return
    Array.from(files).forEach((file) => upload.mutate(file))
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    handleFiles(e.dataTransfer.files)
  }

  const handleQuery = async () => {
    if (!queryText.trim()) return
    const result = await query.mutateAsync({ query: queryText, top_k: 5 })
    setQueryResult(result)
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Document Intelligence</h1>
        <p className="text-slate-500 text-sm mt-1">Upload financial documents and query them with AI-powered RAG</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Area */}
        <div className="space-y-4">
          <div
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
            onDragLeave={() => setIsDragging(false)}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
              isDragging
                ? 'border-brand-500 bg-brand-600/10'
                : 'border-surface-500 hover:border-brand-600/50 hover:bg-surface-700/50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED}
              multiple
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
            <Upload className={`w-10 h-10 mx-auto mb-3 ${isDragging ? 'text-brand-400' : 'text-slate-600'}`} />
            <p className="text-sm font-medium text-slate-300 mb-1">Drop files here or click to upload</p>
            <p className="text-xs text-slate-500">PDF, DOCX, TXT, XLSX supported</p>
            {upload.isPending && (
              <div className="mt-3 flex items-center justify-center gap-2 text-xs text-brand-400">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Uploading...
              </div>
            )}
          </div>

          {/* Document List */}
          <div>
            <h3 className="text-sm font-semibold text-slate-300 mb-3">
              Uploaded Documents {documents && `(${documents.length})`}
            </h3>
            {loadingDocs ? (
              <TableSkeleton rows={3} />
            ) : documents && documents.length > 0 ? (
              <div className="space-y-2">
                {documents.map((doc) => (
                  <DocumentRow key={doc.id} doc={doc} />
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500 text-sm">
                No documents uploaded yet
              </div>
            )}
          </div>
        </div>

        {/* Query Area */}
        <div className="space-y-4">
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-slate-200 mb-3">Query Documents</h3>
            <textarea
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="Ask a question about your documents..."
              rows={3}
              className="input w-full resize-none mb-3"
            />
            <button
              onClick={handleQuery}
              disabled={query.isPending || !queryText.trim()}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {query.isPending ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Searching...</>
              ) : (
                <><Search className="w-4 h-4" /> Search Documents</>
              )}
            </button>
          </div>

          {/* Query Result */}
          <AnimatePresence>
            {queryResult && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                {/* Answer */}
                <div className="card p-5 border border-brand-600/20">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-6 h-6 bg-brand-600/20 rounded-full flex items-center justify-center">
                      <Search className="w-3 h-3 text-brand-400" />
                    </div>
                    <span className="text-xs font-medium text-brand-400">Answer</span>
                    <span className="text-xs text-slate-500 ml-auto">
                      Confidence: {(queryResult.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-sm text-slate-200 leading-relaxed">{queryResult.answer}</p>
                </div>

                {/* Citations */}
                {queryResult.citations && queryResult.citations.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wide">
                      Sources ({queryResult.citations.length})
                    </h4>
                    <div className="space-y-2">
                      {queryResult.citations.map((citation, i) => (
                        <CitationCard key={i} citation={citation} />
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
