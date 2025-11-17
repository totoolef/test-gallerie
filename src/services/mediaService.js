// Service pour gérer les appels API vers le backend Python

// URL de base de l'API - utilise le proxy en développement, ou l'URL complète en production
// Par défaut, utilise le port 5001 (5000 est souvent utilisé par AirPlay sur macOS)
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const mediaService = {
  /**
   * Récupère les 9 premiers médias pour la page d'accueil
   */
  async getInitialMedia(limit = 9) {
    try {
      const response = await fetch(`${API_BASE_URL}/media/initial?limit=${limit}`)
      if (!response.ok) {
        throw new Error('Erreur lors du chargement des médias')
      }
      const data = await response.json()
      return this.formatMedia(data.media || [])
    } catch (error) {
      console.error('Erreur getInitialMedia:', error)
      // Fallback: retourner des médias vides
      return []
    }
  },

  /**
   * Recherche des médias par requête texte
   */
  async searchMedia(query, options = {}) {
    try {
      const response = await fetch(`${API_BASE_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          top_k: options.top_k || 12,
          use_query_expansion: options.use_query_expansion !== false,
          ...options
        }),
      })
      
      if (!response.ok) {
        throw new Error('Erreur lors de la recherche')
      }
      
      const data = await response.json()
      return this.formatMedia(data.results || [])
    } catch (error) {
      console.error('Erreur searchMedia:', error)
      return []
    }
  },

  /**
   * Formate les médias pour l'affichage
   */
  formatMedia(mediaArray) {
    return mediaArray.map((item) => {
      const isVideo = item.media_type === 'video' || item.type === 'video'
      
      return {
        path: item.file_path || item.path,
        type: isVideo ? 'video' : 'image',
        caption: item.caption || '',
        thumbnail: this.getThumbnailUrl(item.file_path || item.path, isVideo),
        score: item.score || 0,
        meta: item
      }
    })
  },

  /**
   * Génère l'URL de la miniature
   */
  getThumbnailUrl(filePath, isVideo) {
    const baseUrl = API_BASE_URL.replace('/api', '') || ''
    if (isVideo) {
      return `${baseUrl}/api/thumbnail?path=${encodeURIComponent(filePath)}&type=video`
    }
    return `${baseUrl}/api/thumbnail?path=${encodeURIComponent(filePath)}&type=image`
  },

  /**
   * Génère l'URL du fichier média (pour lecture vidéo)
   */
  getMediaFileUrl(filePath) {
    const baseUrl = API_BASE_URL.replace('/api', '') || ''
    return `${baseUrl}/api/media/file?path=${encodeURIComponent(filePath)}`
  },

  /**
   * Upload des fichiers depuis la galerie du téléphone
   */
  async uploadMedia(files) {
    try {
      const formData = new FormData()
      
      // Ajouter tous les fichiers au FormData
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i])
      }
      
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Erreur lors de l\'upload')
      }
      
      const data = await response.json()
      return data
    } catch (error) {
      console.error('Erreur uploadMedia:', error)
      throw error
    }
  }
}

