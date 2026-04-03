from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from ..services.document_service import DocumentService
from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import User

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        service = DocumentService(db)
        document = service.save_file(file, user_id=current_user.id)

        return {
            "status": "success",
            "document": {
                "id": document.id,
                "original_name": document.original_name,
                "filename": document.filename,
                "path": document.path,
                "uploaded_at": str(document.uploaded_at),
            }
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}")
def list_user_documents(user_id: str, db: Session = Depends(get_db)):
    try:
        service = DocumentService(db)
        documents = service.list_user_documents(user_id)
        return {
            "documents": [
                {
                    "id": doc.id,
                    "original_name": doc.original_name,
                    "filename": doc.filename,
                    "path": doc.path,
                    "uploaded_at": str(doc.uploaded_at),
                } for doc in documents
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
