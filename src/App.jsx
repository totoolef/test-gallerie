import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import AppLayout from './components/AppLayout'
import Home from './pages/Home'
import Search from './pages/Search'
import Analyse from './pages/Analyse'
import Settings from './pages/Settings'
import MediaViewer from './components/MediaViewer'
import { mediaService } from './services/mediaService'

function App() {
  const [activeTab, setActiveTab] = useState('home')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedMedia, setSelectedMedia] = useState(null)
  const [viewerOpen, setViewerOpen] = useState(false)
  const [viewerMedia, setViewerMedia] = useState([])
  const [viewerIndex, setViewerIndex] = useState(0)
  const [allMedia, setAllMedia] = useState({ home: [], search: [] })

  const handleTabChange = (tabId) => {
    setActiveTab(tabId)
    if (tabId === 'search') {
      setSearchQuery('')
    }
  }

  const handleSearch = (query) => {
    setSearchQuery(query)
    setActiveTab('search')
  }

  const handleMediaClick = (media, mediaList = null) => {
    // Déterminer la liste de médias à utiliser
    const mediaArray = mediaList || allMedia[activeTab] || []
    
    // Trouver l'index du média cliqué
    const index = mediaArray.findIndex(m => 
      (m.path && m.path === media.path) || 
      (m.thumbnail && m.thumbnail === media.thumbnail) ||
      (m.path === media.path && m.type === media.type)
    )
    
    if (mediaArray.length > 0) {
      setViewerMedia(mediaArray)
      setViewerIndex(index !== -1 ? index : 0)
      setViewerOpen(true)
    } else {
      setViewerMedia([media])
      setViewerIndex(0)
      setViewerOpen(true)
    }
  }

  const handleCloseViewer = () => {
    setViewerOpen(false)
  }

  const handleNextMedia = () => {
    if (viewerIndex < viewerMedia.length - 1) {
      setViewerIndex(viewerIndex + 1)
    }
  }

  const handlePreviousMedia = () => {
    if (viewerIndex > 0) {
      setViewerIndex(viewerIndex - 1)
    }
  }

  const updateMediaList = (tab, mediaList) => {
    setAllMedia(prev => ({
      ...prev,
      [tab]: mediaList
    }))
  }

  const handleAnalyse = async () => {
    // Appel à l'API Python pour lancer l'analyse
    try {
      const apiUrl = import.meta.env.VITE_API_URL || '/api'
      const response = await fetch(`${apiUrl}/analyse`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (!response.ok) {
        throw new Error('Erreur lors de l\'analyse')
      }
      return await response.json()
    } catch (error) {
      console.error('Erreur:', error)
      throw error
    }
  }

  const handleThemeChange = (theme) => {
    // Gérer le changement de thème
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  const renderPage = () => {
    switch (activeTab) {
      case 'home':
        return (
          <Home
            onSearch={handleSearch}
            onMediaClick={handleMediaClick}
            mediaService={mediaService}
            onMediaListUpdate={(mediaList) => updateMediaList('home', mediaList)}
          />
        )
      case 'search':
        return (
          <Search
            onSearch={handleSearch}
            onMediaClick={handleMediaClick}
            mediaService={mediaService}
            searchQuery={searchQuery}
            onMediaListUpdate={(mediaList) => updateMediaList('search', mediaList)}
          />
        )
      case 'analyse':
        return <Analyse onAnalyse={handleAnalyse} />
      case 'settings':
        return <Settings onThemeChange={handleThemeChange} />
      default:
        return null
    }
  }

  return (
    <>
      <AppLayout
        activeTab={activeTab}
        onTabChange={handleTabChange}
        headerTitle="Mon IA Média"
      >
        {renderPage()}
      </AppLayout>
      
      {/* Media Viewer plein écran */}
      {viewerOpen && (
        <MediaViewer
          media={viewerMedia}
          currentIndex={viewerIndex}
          onClose={handleCloseViewer}
          onNext={handleNextMedia}
          onPrevious={handlePreviousMedia}
        />
      )}
    </>
  )
}

export default App

