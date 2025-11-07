import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import MediaGrid from '../components/MediaGrid'
import SearchBar from '../components/SearchBar'
import PhotoPicker from '../components/PhotoPicker'

const Home = ({ onSearch, onMediaClick, mediaService, onMediaListUpdate }) => {
  const [media, setMedia] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadInitialMedia()
  }, [])

  useEffect(() => {
    if (onMediaListUpdate && media.length > 0) {
      onMediaListUpdate(media)
    }
  }, [media, onMediaListUpdate])

  const loadInitialMedia = async () => {
    try {
      setLoading(true)
      const initialMedia = await mediaService.getInitialMedia(9)
      setMedia(initialMedia)
    } catch (error) {
      console.error('Erreur lors du chargement des médias:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (query) => {
    if (onSearch) {
      onSearch(query)
    }
  }

  const handleUploadComplete = async (result) => {
    // Recharger les médias après l'upload
    await loadInitialMedia()
  }

  return (
    <div className="pb-4">
      <div className="pt-2">
        <SearchBar onSearch={handleSearch} />
      </div>
      
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="w-8 h-8 border-2 border-apple-blue border-t-transparent rounded-full"
          />
        </div>
      ) : (
        <MediaGrid media={media} onMediaClick={onMediaClick} />
      )}

      <PhotoPicker onUploadComplete={handleUploadComplete} />
    </div>
  )
}

export default Home

