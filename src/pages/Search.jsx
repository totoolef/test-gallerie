import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Search as SearchIcon } from 'lucide-react'
import MediaGrid from '../components/MediaGrid'
import SearchBar from '../components/SearchBar'

const Search = ({ onSearch, onMediaClick, mediaService, searchQuery, onMediaListUpdate }) => {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  useEffect(() => {
    if (searchQuery) {
      performSearch(searchQuery)
    }
  }, [searchQuery])

  useEffect(() => {
    if (onMediaListUpdate && results.length > 0) {
      onMediaListUpdate(results)
    }
  }, [results, onMediaListUpdate])

  const performSearch = async (query) => {
    if (!query || !query.trim()) {
      setResults([])
      setHasSearched(false)
      return
    }

    try {
      setLoading(true)
      setHasSearched(true)
      const searchResults = await mediaService.searchMedia(query)
      setResults(searchResults)
    } catch (error) {
      console.error('Erreur lors de la recherche:', error)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (query) => {
    performSearch(query)
    if (onSearch) {
      onSearch(query)
    }
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
      ) : hasSearched && results.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 px-4">
          <SearchIcon className="w-16 h-16 text-gray-300 mb-4" />
          <p className="text-gray-500 text-center text-base">
            Aucun résultat trouvé
          </p>
          <p className="text-gray-400 text-center text-sm mt-2">
            Essayez avec d'autres mots-clés
          </p>
        </div>
      ) : results.length > 0 ? (
        <div className="mt-2">
          <p className="text-gray-600 text-sm px-3 mb-2">
            {results.length} résultat{results.length > 1 ? 's' : ''} trouvé{results.length > 1 ? 's' : ''}
          </p>
          <MediaGrid media={results} onMediaClick={onMediaClick} />
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-20 px-4">
          <SearchIcon className="w-16 h-16 text-gray-300 mb-4" />
          <p className="text-gray-500 text-center text-base">
            Recherchez des images ou vidéos
          </p>
          <p className="text-gray-400 text-center text-sm mt-2">
            Utilisez la barre de recherche ci-dessus
          </p>
        </div>
      )}
    </div>
  )
}

export default Search

