import os
import shutil
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.document import Document
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "documents")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024 

class DocumentService:
    allowed_extensions = {
        ".pdf", ".doc", ".docx", ".txt", ".md",
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"
    }

    def __init__(self, db: Session):
        self.db = db

    def save_file(self, file, user_id: str) -> Document:
        if not file or not file.filename:
            raise ValueError("No file provided")

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in self.allowed_extensions:
            raise ValueError("Unsupported file type")

        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds {MAX_FILE_SIZE_MB} MB limit")

        original_name = secure_filename(file.filename)
        unique_filename = f"{uuid4().hex}_{original_name}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        document = Document(
            user_id=user_id,
            filename=unique_filename,
            original_name=original_name,
            path=file_path,
            uploaded_at=datetime.utcnow()
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def list_user_documents(self, user_id: str):
        return self.db.query(Document).filter(Document.user_id == user_id).all()
