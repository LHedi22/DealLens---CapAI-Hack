import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { uploadFiles } from '../../lib/api'

const IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.heic', '.heif']
const ACCEPTED = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'image/heic': ['.heic'],
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function isImageFile(name) {
  return IMAGE_EXTS.some(ext => name.toLowerCase().endsWith(ext))
}

export default function FileUploader({ startupId, onUploadComplete, onImageDetected }) {
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [uploadDone, setUploadDone] = useState(false)
  const [error, setError] = useState(null)

  const onDrop = useCallback((accepted) => {
    setFiles(prev => {
      const existing = new Set(prev.map(f => f.name))
      const newFiles = accepted.filter(f => !existing.has(f.name))
      return [...prev, ...newFiles]
    })
    setUploadDone(false)
    setError(null)

    const imageFile = accepted.find(f => isImageFile(f.name))
    if (imageFile && onImageDetected) onImageDetected(imageFile.name)
  }, [onImageDetected])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    multiple: true,
  })

  const removeFile = (name) => {
    setFiles(prev => prev.filter(f => f.name !== name))
  }

  const handleUpload = async () => {
    if (!files.length || !startupId) return
    setUploading(true)
    setError(null)
    try {
      const result = await uploadFiles(startupId, files)
      setUploadDone(true)
      if (onUploadComplete) onUploadComplete(result)
    } catch (e) {
      setError('Upload failed. Check that the backend is running.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-indigo-400 bg-indigo-900/20'
            : 'border-slate-600 hover:border-slate-500 hover:bg-slate-800/30'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center text-2xl">
            📄
          </div>
          <div>
            <p className="text-slate-200 font-medium">
              {isDragActive ? 'Drop files here...' : 'Drag & drop startup documents'}
            </p>
            <p className="text-slate-500 text-sm mt-1">
              PDF, DOCX, XLSX, JPG, PNG, HEIC — multiple files supported
            </p>
          </div>
          <button
            type="button"
            className="px-4 py-1.5 rounded-lg border border-slate-600 text-slate-300 text-sm hover:bg-slate-700 transition-colors"
          >
            Browse files
          </button>
        </div>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map(file => (
            <div
              key={file.name}
              className="flex items-center justify-between bg-slate-800 rounded-lg px-4 py-2.5 border border-slate-700"
            >
              <div className="flex items-center gap-3 min-w-0">
                <span className="text-lg">{isImageFile(file.name) ? '🖼️' : '📋'}</span>
                <div className="min-w-0">
                  <p className="text-slate-200 text-sm font-medium truncate">{file.name}</p>
                  <p className="text-slate-500 text-xs">{formatBytes(file.size)}</p>
                </div>
              </div>
              <button
                onClick={() => removeFile(file.name)}
                className="text-slate-500 hover:text-red-400 transition-colors ml-4 flex-shrink-0"
                title="Remove"
              >
                ✕
              </button>
            </div>
          ))}

          {error && (
            <p className="text-red-400 text-sm px-1">{error}</p>
          )}

          {uploadDone ? (
            <div className="flex items-center gap-2 text-green-400 text-sm px-1">
              <span>✓</span>
              <span>{files.length} file(s) uploaded successfully</span>
            </div>
          ) : (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="w-full py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-sm transition-colors"
            >
              {uploading ? 'Uploading...' : `Upload ${files.length} file(s)`}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
