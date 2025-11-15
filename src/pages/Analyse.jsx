import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Brain, Upload, CheckCircle, AlertCircle } from 'lucide-react'

const Analyse = ({ onAnalyse }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [status, setStatus] = useState(null)

  const handleAnalyse = async () => {
    setIsAnalyzing(true)
    setStatus(null)
    
    try {
      if (onAnalyse) {
        await onAnalyse()
        setStatus('success')
      }
    } catch (error) {
      console.error('Erreur lors de l\'analyse:', error)
      setStatus('error')
    } finally {
      setIsAnalyzing(false)
    }
  }

  return (
    <div className="px-4 py-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="max-w-sm mx-auto"
      >
        <div className="flex flex-col items-center mb-8">
          <div className="w-20 h-20 rounded-full bg-apple-blue/10 flex items-center justify-center mb-4">
            <Brain className="w-10 h-10 text-apple-blue" />
          </div>
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Analyse des médias
          </h2>
          <p className="text-gray-500 text-center text-sm">
            Indexez vos images et vidéos pour une recherche intelligente
          </p>
        </div>

        <div className="space-y-4 mb-6">
          <div className="bg-gray-50 rounded-2xl p-4">
            <h3 className="font-medium text-gray-900 mb-2">Fonctionnalités</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-apple-blue mr-2 mt-0.5 flex-shrink-0" />
                <span>Extraction automatique des embeddings CLIP</span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-apple-blue mr-2 mt-0.5 flex-shrink-0" />
                <span>Génération de captions avec BLIP</span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-apple-blue mr-2 mt-0.5 flex-shrink-0" />
                <span>Indexation FAISS pour recherche rapide</span>
              </li>
            </ul>
          </div>
        </div>

        {status === 'success' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-4 bg-green-50 border border-green-200 rounded-2xl p-4 flex items-start"
          >
            <CheckCircle className="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-green-800 font-medium text-sm">Analyse terminée</p>
              <p className="text-green-600 text-xs mt-1">Vos médias ont été indexés avec succès</p>
            </div>
          </motion.div>
        )}

        {status === 'error' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mb-4 bg-red-50 border border-red-200 rounded-2xl p-4 flex items-start"
          >
            <AlertCircle className="w-5 h-5 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-red-800 font-medium text-sm">Erreur</p>
              <p className="text-red-600 text-xs mt-1">Une erreur s'est produite lors de l'analyse</p>
            </div>
          </motion.div>
        )}

        <motion.button
          whileTap={{ scale: 0.98 }}
          whileHover={{ scale: 1.02 }}
          onClick={handleAnalyse}
          disabled={isAnalyzing}
          className="w-full bg-apple-blue text-white rounded-2xl py-4 px-6 font-medium text-base disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 shadow-lg shadow-apple-blue/20"
        >
          {isAnalyzing ? (
            <>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
              />
              <span>Analyse en cours...</span>
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" />
              <span>Lancer l'analyse</span>
            </>
          )}
        </motion.button>
      </motion.div>
    </div>
  )
}

export default Analyse


