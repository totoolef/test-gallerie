#!/bin/bash

# Script pour déployer le frontend sur Vercel

echo "🚀 Déploiement du frontend sur Vercel"
echo ""

# Vérifier que Vercel CLI est installé
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI n'est pas installé"
    echo "Installez-le avec: npm i -g vercel"
    exit 1
fi

# Vérifier que l'utilisateur est connecté à Vercel
if ! vercel whoami &> /dev/null; then
    echo "⚠️  Vous n'êtes pas connecté à Vercel"
    echo "Connectez-vous avec: vercel login"
    exit 1
fi

# Demander l'URL de l'API Railway
echo "📡 Quelle est l'URL de votre API Railway ?"
echo "   (Exemple: https://votre-app.railway.app)"
read -p "URL de l'API: " API_URL

if [ -z "$API_URL" ]; then
    echo "❌ URL de l'API requise"
    exit 1
fi

# Ajouter /api si ce n'est pas déjà présent
if [[ ! "$API_URL" == */api ]]; then
    API_URL="$API_URL/api"
fi

echo ""
echo "✅ URL de l'API: $API_URL"
echo ""

# Déployer sur Vercel
echo "📦 Déploiement sur Vercel..."
vercel --prod

# Afficher les instructions pour configurer les variables d'environnement
echo ""
echo "📝 IMPORTANT: Configurez la variable d'environnement dans Vercel:"
echo "   1. Allez sur https://vercel.com"
echo "   2. Sélectionnez votre projet"
echo "   3. Allez dans Settings → Environment Variables"
echo "   4. Ajoutez:"
echo "      - Name: VITE_API_URL"
echo "      - Value: $API_URL"
echo "      - Environment: Production, Preview, Development"
echo "   5. Redéployez avec: vercel --prod"
echo ""


