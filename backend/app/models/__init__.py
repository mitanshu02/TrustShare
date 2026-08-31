"""
Importing this package registers all ORM models on Base.metadata,
which Alembic's autogenerate relies on.
"""

from app.models.user import User 
from app.models.folder import Folder  
from app.models.file import File  
from app.models.file_version import FileVersion  
from app.models.file_permission import FilePermission  
from app.models.share_link import ShareLink  
from app.models.download import Download  