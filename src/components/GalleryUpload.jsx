import React, { useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, X, CheckCircle, AlertCircle, Loader } from 'lucide-react'
import { mediaService } from '../services/mediaService'

const GalleryUpload = ({ onUploadComplete }) => {
  const fileInputRef = useRef(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState(null) // { type: 'success' | 'error', message: string }

  const handleFileSelect = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (event) => {
    const files = Array.from(event.target.files || [])
    
    if (files.length === 0) {
      return
    }

    setIsUploading(true)
    setUploadStatus(null)

    try {
      const result = await mediaService.uploadMedia(files)
      
      setUploadStatus({
        type: 'success',
        message: `${result.uploaded} fichier(s) uploadé(s) avec succès${result.errors ? ` (${result.errors.length} erreur(s))` : ''}`
      })

      // Réinitialiser l'input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      // Appeler le callback si fourni
      if (onUploadComplete) {
        onUploadComplete(result)
      }

      // Masquer le message après 3 secondes
      setTimeout(() => {
        setUploadStatus(null)
      }, 3000)

    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: error.message || 'Erreur lors de l\'upload'
      })

      // Masquer le message après 5 secondes
      setTimeout(() => {
        setUploadStatus(null)
      }, 5000)
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*,video/*"
        multiple
        onChange={handleFileChange}
        className="hidden"
        // Pas d'attribut capture pour permettre l'accès à la galerie Photos sur iOS
      />

      <motion.button
        whileTap={{ scale: 0.95 }}
        onClick={handleFileSelect}
        disabled={isUploading}
        className="fixed bottom-20 right-4 z-50 w-14 h-14 bg-apple-blue rounded-full shadow-lg flex items-center justify-center text-white disabled:opacity-50 disabled:cursor-not-allowed"
        style={{
          boxShadow: '0 4px 14px 0 rgba(0, 122, 255, 0.39)'
        }}
        title="Importer depuis la galerie Photos"
        aria-label="Importer des photos et vidéos depuis la galerie"
      >
        {isUploading ? (
          <Loader className="w-6 h-6 animate-spin" />
        ) : (
          <Upload className="w-6 h-6" />
        )}
      </motion.button>

      {/* Message de statut */}
      <AnimatePresence>
        {uploadStatus && (
          <motion.div
            initial={{ y: 100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 100, opacity: 0 }}
            className="fixed bottom-24 left-4 right-4 z-50"
          >
            <div
              className={`rounded-2xl p-4 shadow-lg flex items-center space-x-3 ${
                uploadStatus.type === 'success'
                  ? 'bg-green-500 text-white'
                  : 'bg-red-500 text-white'
              }`}
            >
              {uploadStatus.type === 'success' ? (
                <CheckCircle className="w-5 h-5 flex-shrink-0" />
              ) : (
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
              )}
              <p className="text-sm font-medium flex-1">{uploadStatus.message}</p>
              <button
                onClick={() => setUploadStatus(null)}
                className="flex-shrink-0"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

export default GalleryUpload

