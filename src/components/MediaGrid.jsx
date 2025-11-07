import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Play } from 'lucide-react'

const MediaGrid = ({ media = [], onMediaClick }) => {
  const [loadedImages, setLoadedImages] = useState(new Set())

  const handleImageLoad = (index) => {
    setLoadedImages(prev => new Set([...prev, index]))
  }

  const handleClick = (item, index) => {
    if (onMediaClick) {
      // Passer l'item et la liste complète de médias
      onMediaClick(item, media)
    }
  }

  return (
    <div className="w-full pb-20">
      <div className="grid grid-cols-3 gap-[2px] bg-black w-full">
        {media.map((item, index) => {
          const isLoaded = loadedImages.has(index)
          const isVideo = item.type === 'video'
          
          return (
            <motion.div
              key={item.path || index}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ 
                duration: 0.3, 
                delay: index * 0.02,
                ease: [0.4, 0, 0.2, 1]
              }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="relative aspect-square bg-gray-200 rounded-none overflow-hidden cursor-pointer group"
              onClick={() => handleClick(item, index)}
            >
              {item.thumbnail ? (
                <>
                  {!isLoaded && (
                    <div className="absolute inset-0 bg-gray-300 animate-pulse" />
                  )}
                  <img
                    src={item.thumbnail}
                    alt={item.caption || ''}
                    className={`w-full h-full object-cover transition-opacity duration-300 ${
                      isLoaded ? 'opacity-100' : 'opacity-0'
                    }`}
                    onLoad={() => handleImageLoad(index)}
                    loading="lazy"
                  />
                </>
              ) : (
                <div className="w-full h-full bg-gray-300 flex items-center justify-center">
                  <span className="text-gray-500 text-xs">Chargement...</span>
                </div>
              )}
              
              {isVideo && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/20 group-hover:bg-black/30 transition-colors">
                  <div className="w-12 h-12 rounded-full bg-white/80 flex items-center justify-center backdrop-blur-sm">
                    <Play className="w-6 h-6 text-gray-900 ml-1" fill="currentColor" />
                  </div>
                </div>
              )}
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}

export default MediaGrid

