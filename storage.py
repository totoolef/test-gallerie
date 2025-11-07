"""
Module de gestion du stockage des médias.
Support pour stockage local, S3, et Cloudinary.
"""

import os
import io
from pathlib import Path
from typing import Optional, BinaryIO, Tuple
from datetime import datetime
import uuid

# Support S3
try:
    import boto3
    from botocore.exceptions import ClientError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

# Support Cloudinary
try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False


class MediaStorage:
    """Gestionnaire de stockage pour les médias."""
    
    def __init__(self, storage_type: str = "local"):
        """
        Initialise le stockage.
        
        Args:
            storage_type: "local", "s3", ou "cloudinary"
        """
        self.storage_type = storage_type or os.environ.get('STORAGE_TYPE', 'local')
        
        if self.storage_type == 's3':
            if not S3_AVAILABLE:
                raise ImportError("boto3 n'est pas installé. Installez-le avec: pip install boto3")
            self._init_s3()
        elif self.storage_type == 'cloudinary':
            if not CLOUDINARY_AVAILABLE:
                raise ImportError("cloudinary n'est pas installé. Installez-le avec: pip install cloudinary")
            self._init_cloudinary()
        else:
            # Stockage local
            self.storage_dir = Path(os.environ.get('STORAGE_DIR', 'media_storage'))
            self.storage_dir.mkdir(exist_ok=True)
    
    def _init_s3(self):
        """Initialise S3."""
        self.s3_bucket = os.environ.get('S3_BUCKET')
        self.s3_region = os.environ.get('S3_REGION', 'us-east-1')
        
        if not self.s3_bucket:
            raise ValueError("S3_BUCKET doit être défini dans les variables d'environnement")
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=self.s3_region
        )
    
    def _init_cloudinary(self):
        """Initialise Cloudinary."""
        cloudinary.config(
            cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
            api_key=os.environ.get('CLOUDINARY_API_KEY'),
            api_secret=os.environ.get('CLOUDINARY_API_SECRET')
        )
    
    def save_file(self, file_data: BinaryIO, filename: str, content_type: Optional[str] = None) -> str:
        """
        Sauvegarde un fichier.
        
        Args:
            file_data: Données du fichier (file-like object)
            filename: Nom du fichier
            content_type: Type MIME
            
        Returns:
            Chemin/URL du fichier sauvegardé
        """
        # Générer un nom unique
        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4()}{ext}"
        
        if self.storage_type == 's3':
            return self._save_s3(file_data, unique_name, content_type)
        elif self.storage_type == 'cloudinary':
            return self._save_cloudinary(file_data, unique_name, content_type)
        else:
            return self._save_local(file_data, unique_name)
    
    def _save_local(self, file_data: BinaryIO, filename: str) -> str:
        """Sauvegarde localement."""
        file_path = self.storage_dir / filename
        # Lire le contenu
        content = file_data.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        return str(file_path)
    
    def _save_s3(self, file_data: BinaryIO, filename: str, content_type: Optional[str]) -> str:
        """Sauvegarde sur S3."""
        key = f"media/{filename}"
        self.s3_client.upload_fileobj(
            file_data,
            self.s3_bucket,
            key,
            ExtraArgs={'ContentType': content_type} if content_type else {}
        )
        return f"s3://{self.s3_bucket}/{key}"
    
    def _save_cloudinary(self, file_data: BinaryIO, filename: str, content_type: Optional[str]) -> str:
        """Sauvegarde sur Cloudinary."""
        result = cloudinary.uploader.upload(
            file_data,
            public_id=Path(filename).stem,
            resource_type="auto"
        )
        return result['secure_url']
    
    def get_file_url(self, file_path: str) -> str:
        """
        Obtient l'URL d'accès à un fichier.
        
        Args:
            file_path: Chemin/URL du fichier
            
        Returns:
            URL d'accès
        """
        if self.storage_type == 's3':
            # Générer une URL signée valide 1h
            key = file_path.replace(f"s3://{self.s3_bucket}/", "")
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.s3_bucket, 'Key': key},
                ExpiresIn=3600
            )
            return url
        elif self.storage_type == 'cloudinary':
            # Cloudinary retourne déjà une URL
            return file_path
        else:
            # Local: retourner le chemin relatif pour l'API
            return f"/api/media/file?path={file_path}"
    
    def delete_file(self, file_path: str) -> bool:
        """Supprime un fichier."""
        if self.storage_type == 's3':
            key = file_path.replace(f"s3://{self.s3_bucket}/", "")
            try:
                self.s3_client.delete_object(Bucket=self.s3_bucket, Key=key)
                return True
            except ClientError:
                return False
        elif self.storage_type == 'cloudinary':
            public_id = Path(file_path).stem
            try:
                cloudinary.uploader.destroy(public_id)
                return True
            except:
                return False
        else:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                file_path_obj.unlink()
                return True
            return False


# Instance globale
_storage_instance = None

def get_storage() -> MediaStorage:
    """Obtient l'instance du stockage (singleton)."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = MediaStorage()
    return _storage_instance

