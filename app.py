import os
import shutil
import tempfile
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from redact import process_docx
from evaluate import run_evaluation

app = FastAPI(
    title="Enterprise PII Redaction Engine",
    description="Automated PII De-Identification & Anonymization for Docx Documents",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
TEMP_DIR = BASE_DIR / "temp_files"
TEMP_DIR.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serves the main Glassmorphism Web UI Dashboard."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/health")
async def health_check():
    """Health check endpoint for Render monitoring."""
    return {"status": "healthy", "service": "PII Redaction Engine", "version": "1.0.0"}

@app.get("/api/metrics")
async def get_metrics():
    """Returns the empirical benchmark evaluation metrics."""
    results = run_evaluation()
    return JSONResponse(content=results)

@app.post("/api/redact")
async def redact_file(file: UploadFile = File(...)):
    """
    Accepts a .docx file upload, executes the Presidio + Custom Recognizer 
    PII Redaction engine, and returns the sanitized document as a download.
    """
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only Microsoft Word (.docx) files are supported.")

    input_filename = f"upload_{file.filename}"
    output_filename = f"Redacted_{file.filename}"

    input_path = TEMP_DIR / input_filename
    output_path = TEMP_DIR / output_filename

    try:
        # Save uploaded file to disk
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run PII Redaction pipeline
        process_docx(str(input_path), str(output_path))

        if not output_path.exists():
            raise HTTPException(status_code=500, detail="Failed to generate redacted document.")

        return FileResponse(
            path=str(output_path),
            filename=output_filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redaction processing error: {str(e)}")
    finally:
        # Clean up input file to save space
        if input_path.exists():
            try:
                os.remove(input_path)
            except Exception:
                pass

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
