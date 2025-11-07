"""
Module de gestion de base de données pour stocker les métadonnées des médias.
Utilise SQLite en local, PostgreSQL en production.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import sqlite3
from contextlib import contextmanager

# Support PostgreSQL en production
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


class MediaDatabase:
    """Gestionnaire de base de données pour les médias."""
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialise la base de données.
        
        Args:
            db_url: URL de connexion (DATABASE_URL en production, None pour SQLite local)
        """
        self.db_url = db_url or os.environ.get('DATABASE_URL')
        self.use_postgres = self.db_url and self.db_url.startswith('postgresql://')
        
        if not self.use_postgres:
            # SQLite local
            db_path = Path("media.db")
            self.conn_string = str(db_path)
        else:
            # PostgreSQL en production
            self.conn_string = self.db_url
        
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager pour obtenir une connexion."""
        if self.use_postgres:
            if not POSTGRES_AVAILABLE:
                raise ImportError("psycopg2 n'est pas installé. Installez-le avec: pip install psycopg2-binary")
            conn = psycopg2.connect(self.conn_string)
            conn.cursor_factory = RealDictCursor
        else:
            conn = sqlite3.connect(self.conn_string)
            conn.row_factory = sqlite3.Row
        
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialise les tables de la base de données."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.use_postgres:
                # PostgreSQL
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS media (
                        id SERIAL PRIMARY KEY,
                        file_path TEXT NOT NULL UNIQUE,
                        file_name TEXT NOT NULL,
                        media_type TEXT NOT NULL,
                        file_size BIGINT,
                        mime_type TEXT,
                        caption TEXT,
                        embedding_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS embeddings (
                        id SERIAL PRIMARY KEY,
                        media_id INTEGER REFERENCES media(id),
                        embedding VECTOR(768),
                        frame_index INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Index pour les recherches
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_type ON media(media_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_created ON media(created_at)")
                
            else:
                # SQLite
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS media (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL UNIQUE,
                        file_name TEXT NOT NULL,
                        media_type TEXT NOT NULL,
                        file_size INTEGER,
                        mime_type TEXT,
                        caption TEXT,
                        embedding_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS embeddings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        media_id INTEGER REFERENCES media(id),
                        embedding BLOB,
                        frame_index INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Index pour les recherches
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_type ON media(media_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_created ON media(created_at)")
            
            conn.commit()
    
    def add_media(self, file_path: str, file_name: str, media_type: str, 
                  file_size: Optional[int] = None, mime_type: Optional[str] = None,
                  caption: Optional[str] = None) -> int:
        """
        Ajoute un média à la base de données.
        
        Returns:
            ID du média créé
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.use_postgres:
                cursor.execute("""
                    INSERT INTO media (file_path, file_name, media_type, file_size, mime_type, caption)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (file_path) DO UPDATE SET
                        updated_at = CURRENT_TIMESTAMP,
                        caption = EXCLUDED.caption
                    RETURNING id
                """, (file_path, file_name, media_type, file_size, mime_type, caption))
            else:
                cursor.execute("""
                    INSERT OR REPLACE INTO media (file_path, file_name, media_type, file_size, mime_type, caption, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (file_path, file_name, media_type, file_size, mime_type, caption))
                
                cursor.execute("SELECT last_insert_rowid() as id")
            
            result = cursor.fetchone()
            media_id = result['id'] if isinstance(result, dict) else result[0]
            return media_id
    
    def get_media(self, media_id: Optional[int] = None, file_path: Optional[str] = None) -> Optional[Dict]:
        """Récupère un média par ID ou chemin."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if media_id:
                if self.use_postgres:
                    cursor.execute("SELECT * FROM media WHERE id = %s", (media_id,))
                else:
                    cursor.execute("SELECT * FROM media WHERE id = ?", (media_id,))
            elif file_path:
                if self.use_postgres:
                    cursor.execute("SELECT * FROM media WHERE file_path = %s", (file_path,))
                else:
                    cursor.execute("SELECT * FROM media WHERE file_path = ?", (file_path,))
            else:
                return None
            
            row = cursor.fetchone()
            if row:
                return dict(row) if isinstance(row, dict) else dict(zip([col[0] for col in cursor.description], row))
            return None
    
    def list_media(self, limit: int = 100, offset: int = 0, media_type: Optional[str] = None) -> List[Dict]:
        """Liste les médias."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM media"
            params = []
            
            if media_type:
                if self.use_postgres:
                    query += " WHERE media_type = %s"
                else:
                    query += " WHERE media_type = ?"
                params.append(media_type)
            
            if self.use_postgres:
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            else:
                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) if isinstance(row, dict) else dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def add_embedding(self, media_id: int, embedding: bytes, frame_index: Optional[int] = None) -> int:
        """Ajoute un embedding."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.use_postgres:
                cursor.execute("""
                    INSERT INTO embeddings (media_id, embedding, frame_index)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (media_id, embedding, frame_index))
            else:
                cursor.execute("""
                    INSERT INTO embeddings (media_id, embedding, frame_index)
                    VALUES (?, ?, ?)
                """, (media_id, embedding, frame_index))
                cursor.execute("SELECT last_insert_rowid() as id")
            
            result = cursor.fetchone()
            embedding_id = result['id'] if isinstance(result, dict) else result[0]
            return embedding_id
    
    def get_embeddings(self, media_id: int) -> List[Dict]:
        """Récupère les embeddings d'un média."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.use_postgres:
                cursor.execute("SELECT * FROM embeddings WHERE media_id = %s", (media_id,))
            else:
                cursor.execute("SELECT * FROM embeddings WHERE media_id = ?", (media_id,))
            rows = cursor.fetchall()
            
            return [dict(row) if isinstance(row, dict) else dict(zip([col[0] for col in cursor.description], row)) for row in rows]
    
    def delete_media(self, media_id: int) -> bool:
        """Supprime un média et ses embeddings."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.use_postgres:
                cursor.execute("DELETE FROM embeddings WHERE media_id = %s", (media_id,))
                cursor.execute("DELETE FROM media WHERE id = %s", (media_id,))
            else:
                cursor.execute("DELETE FROM embeddings WHERE media_id = ?", (media_id,))
                cursor.execute("DELETE FROM media WHERE id = ?", (media_id,))
            
            return cursor.rowcount > 0


# Instance globale
_db_instance = None

def get_db(db_url: Optional[str] = None) -> MediaDatabase:
    """Obtient l'instance de la base de données (singleton)."""
    global _db_instance
    if _db_instance is None:
        _db_instance = MediaDatabase(db_url)
    return _db_instance

