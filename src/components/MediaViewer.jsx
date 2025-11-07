import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, ChevronLeft, ChevronRight, Share2, Printer, Sparkles, Download, Trash2 } from 'lucide-react'
import MediaActions from './MediaActions'
import { mediaService } from '../services/mediaService'

const MediaViewer = ({ media, currentIndex, onClose, onNext, onPrevious }) => {
  const [isActionsVisible, setIsActionsVisible] = useState(true)
  const [touchStart, setTouchStart] = useState(null)
  const [touchEnd, setTouchEnd] = useState(null)

  if (!media || media.length === 0) return null
  
  const currentMedia = media[currentIndex]
  
  if (!currentMedia) return null

  // Masquer/afficher les actions après 3 secondes d'inactivité
  useEffect(() => {
    if (!isActionsVisible) return

    const timer = setTimeout(() => {
      setIsActionsVisible(false)
    }, 3000)

    return () => clearTimeout(timer)
  }, [isActionsVisible, currentIndex])

  // Gérer le swipe pour changer de photo
  const minSwipeDistance = 50

  const onTouchStart = (e) => {
    setTouchEnd(null)
    setTouchStart(e.targetTouches[0].clientX)
    setIsActionsVisible(true)
  }

  const onTouchMove = (e) => {
    setTouchEnd(e.targetTouches[0].clientX)
  }

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return

    const distance = touchStart - touchEnd
    const isLeftSwipe = distance > minSwipeDistance
    const isRightSwipe = distance < -minSwipeDistance

    if (isLeftSwipe && onNext) {
      onNext()
      setIsActionsVisible(true)
    }
    if (isRightSwipe && onPrevious) {
      onPrevious()
      setIsActionsVisible(true)
    }
  }

  const handleImageClick = () => {
    setIsActionsVisible(!isActionsVisible)
  }

  const handleShare = async () => {
    if (navigator.share && currentMedia?.path) {
      try {
        await navigator.share({
          title: currentMedia.caption || 'Photo',
          text: currentMedia.caption || '',
          url: currentMedia.thumbnail || currentMedia.path
        })
      } catch (error) {
        console.log('Erreur lors du partage:', error)
      }
    } else {
      // Fallback: copier le lien dans le presse-papiers
      if (currentMedia?.path) {
        navigator.clipboard.writeText(currentMedia.path)
        alert('Lien copié dans le presse-papiers')
      }
    }
  }

  const handlePrint = () => {
    if (currentMedia?.thumbnail || currentMedia?.path) {
      const printWindow = window.open('', '_blank')
      if (printWindow) {
        printWindow.document.write(`
          <html>
            <head><title>Impression</title></head>
            <body style="margin:0;padding:0;display:flex;justify-content:center;align-items:center;min-height:100vh;">
              <img src="${currentMedia.thumbnail || currentMedia.path}" style="max-width:100%;max-height:100vh;object-fit:contain;" />
            </body>
          </html>
        `)
        printWindow.document.close()
        printWindow.print()
      }
    }
  }

  const handleEnhance = () => {
    // Placeholder pour amélioration de qualité
    alert('Fonctionnalité d\'amélioration de qualité à venir')
  }

  const handleDownload = () => {
    if (currentMedia?.thumbnail || currentMedia?.path) {
      const link = document.createElement('a')
      link.href = currentMedia.thumbnail || currentMedia.path
      link.download = currentMedia.caption || 'photo.jpg'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  const actions = [
    { id: 'share', icon: Share2, label: 'Partager', action: handleShare },
    { id: 'print', icon: Printer, label: 'Imprimer', action: handlePrint },
    { id: 'enhance', icon: Sparkles, label: 'Améliorer', action: handleEnhance },
    { id: 'download', icon: Download, label: 'Télécharger', action: handleDownload },
  ]

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        className="fixed inset-0 z-50 bg-black"
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
      >
        {/* Média principal (image ou vidéo) */}
        <div 
          className="absolute inset-0 flex items-center justify-center"
          onClick={handleImageClick}
        >
          {currentMedia.type === 'video' ? (
            <motion.video
              key={currentIndex}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
              src={mediaService.getMediaFileUrl(currentMedia.path)}
              poster={currentMedia.thumbnail}
              controls
              className="max-w-full max-h-full object-contain"
              playsInline
              onPlay={() => setIsActionsVisible(false)}
              onPause={() => setIsActionsVisible(true)}
            >
              Votre navigateur ne supporte pas la lecture de vidéos.
            </motion.video>
          ) : (
            <motion.img
              key={currentIndex}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
              src={currentMedia.thumbnail || currentMedia.path}
              alt={currentMedia.caption || ''}
              className="max-w-full max-h-full object-contain"
              draggable={false}
            />
          )}
        </div>

        {/* Bouton fermer (en haut à droite) */}
        <AnimatePresence>
          {isActionsVisible && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.2 }}
              onClick={(e) => {
                e.stopPropagation()
                onClose()
              }}
              className="absolute top-4 right-4 z-10 w-10 h-10 rounded-full bg-black/50 backdrop-blur-md flex items-center justify-center text-white hover:bg-black/70 transition-colors safe-area-top"
            >
              <X className="w-6 h-6" />
            </motion.button>
          )}
        </AnimatePresence>

        {/* Indicateur de position (en haut) */}
        <AnimatePresence>
          {isActionsVisible && media.length > 1 && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
              className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10 px-4 py-2 rounded-full bg-black/50 backdrop-blur-md text-white text-sm font-medium safe-area-top"
            >
              {currentIndex + 1} / {media.length}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Boutons navigation (gauche/droite) */}
        {media.length > 1 && (
          <>
            {currentIndex > 0 && (
              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: isActionsVisible ? 1 : 0 }}
                exit={{ opacity: 0 }}
                onClick={(e) => {
                  e.stopPropagation()
                  onPrevious()
                }}
                className="absolute left-4 top-1/2 transform -translate-y-1/2 z-10 w-12 h-12 rounded-full bg-black/50 backdrop-blur-md flex items-center justify-center text-white hover:bg-black/70 transition-colors"
              >
                <ChevronLeft className="w-6 h-6" />
              </motion.button>
            )}
            {currentIndex < media.length - 1 && (
              <motion.button
                initial={{ opacity: 0 }}
                animate={{ opacity: isActionsVisible ? 1 : 0 }}
                exit={{ opacity: 0 }}
                onClick={(e) => {
                  e.stopPropagation()
                  onNext()
                }}
                className="absolute right-4 top-1/2 transform -translate-y-1/2 z-10 w-12 h-12 rounded-full bg-black/50 backdrop-blur-md flex items-center justify-center text-white hover:bg-black/70 transition-colors"
              >
                <ChevronRight className="w-6 h-6" />
              </motion.button>
            )}
          </>
        )}

        {/* Menu d'actions en bas */}
        <MediaActions
          actions={actions}
          isVisible={isActionsVisible}
          onActionClick={(action) => {
            action.action()
            setIsActionsVisible(true)
          }}
        />
      </motion.div>
    </AnimatePresence>
  )
}

export default MediaViewer

