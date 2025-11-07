import React from 'react'
import { motion } from 'framer-motion'

const Header = ({ title = "Mon IA Média" }) => {
  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
      className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md shadow-md safe-area-top w-full"
    >
      <div className="w-full md:max-w-[430px] md:mx-auto px-4 py-3">
        <h1 className="text-xl font-semibold text-gray-900 text-center tracking-tight">
          {title}
        </h1>
      </div>
    </motion.header>
  )
}

export default Header

