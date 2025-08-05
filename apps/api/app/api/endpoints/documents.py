from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import aiofiles
import os
from app.config import get_settings

router = APIRouter()
settings = get_settings()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document for processing"""
    
    # Validate file extension
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in settings.allowed_extensions_list:  # Use the list property
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {settings.allowed_extensions_list}"
        )
    
    # Validate file size
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)
    if file_size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )
    
    # Process based on file type
    if file_ext == "txt":
        content = contents.decode("utf-8")
    elif file_ext == "pdf":
        # Use pypdf to extract text
        try:
            import pypdf
            import io
            pdf_reader = pypdf.PdfReader(io.BytesIO(contents))
            content = ""
            for page in pdf_reader.pages:
                content += page.extract_text()
        except:
            content = "Error reading PDF file"
    elif file_ext == "docx":
        # Use python-docx to extract text
        try:
            import docx
            import io
            doc = docx.Document(io.BytesIO(contents))
            content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except:
            content = "Error reading DOCX file"
    else:
        content = contents.decode("utf-8", errors="ignore")
    
    return {
        "filename": file.filename,
        "size": len(contents),
        "content": content[:1000] + "..." if len(content) > 1000 else content,
        "full_content": content,
        "message": "Document uploaded successfully"
    }

@router.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported document formats"""
    return {
        "formats": settings.allowed_extensions_list,  # Use the list property
        "max_size_mb": settings.max_file_size_mb
    }
