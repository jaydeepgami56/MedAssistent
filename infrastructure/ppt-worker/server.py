"""
PPT Worker — sandboxed Linux container service for executing pptxgenjs pipelines.

The FastAPI backend (running on the host) calls this service to:
  1. Execute AI-generated pptxgenjs JavaScript → output.pptx
  2. Run LibreOffice + pdftoppm QA pipeline → slide-N.jpg thumbnails
  3. Store all outputs in /ppt_outputs/{job_id}/ (bind-mounted shared volume)

Endpoints:
  POST /run                          — execute pipeline for one job
  GET  /download/{job_id}           — serve .pptx file
  GET  /thumbnail/{job_id}/{n}      — serve slide thumbnail .jpg
  GET  /health                      — liveness check
"""

import subprocess
import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

OUTPUT_BASE = Path("/ppt_outputs")
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

SUBPROCESS_TIMEOUT_NPM = 60
SUBPROCESS_TIMEOUT_NODE = 120
SUBPROCESS_TIMEOUT_SOFFICE = 90
SUBPROCESS_TIMEOUT_PDFTOPPM = 60

app = FastAPI(title="MedAssist PPT Worker", version="1.0")


class RunRequest(BaseModel):
    job_id: str
    js_code: str


def _run(cmd: list, cwd: str, timeout: int) -> tuple:
    """Run a subprocess. Returns (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Timed out after {timeout}s: {' '.join(cmd)}"
    except FileNotFoundError as e:
        return -1, "", f"Command not found: {e}"
    except Exception as e:
        return -1, "", str(e)


@app.get("/health")
def health():
    """Liveness check — also verifies node, soffice, pdftoppm are on PATH."""
    tools = {}
    for tool in ["node", "npm", "soffice", "pdftoppm"]:
        rc, _, _ = _run(["which", tool], cwd="/tmp", timeout=5)
        tools[tool] = rc == 0
    return {"status": "ok", "tools": tools}


@app.post("/run")
def run_ppt(req: RunRequest):
    """
    Execute the PPT generation pipeline for one job.

    Steps:
      1. Write generate.js to a temp work dir
      2. npm install pptxgenjs (uses global install if available)
      3. node generate.js → output.pptx
      4. soffice --headless --convert-to pdf → output.pdf
      5. pdftoppm → slide-N.jpg thumbnails
      6. Copy .pptx + thumbnails to /ppt_outputs/{job_id}/

    Returns:
      { success: bool, thumbnail_count: int, error: str | null }
    """
    job_id = req.job_id
    work_dir = Path(f"/tmp/ppt_work_{job_id}")
    out_dir = OUTPUT_BASE / job_id

    work_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        # ── Step 1: write generate.js ─────────────────────────────────────────
        gen_js = work_dir / "generate.js"
        gen_js.write_text(req.js_code, encoding="utf-8")

        # ── Step 2: npm install pptxgenjs ─────────────────────────────────────
        # Try local install; if global pptxgenjs is pre-installed in the image
        # node will find it via NODE_PATH and npm install is still fast (no-op).
        rc, _, stderr = _run(
            ["npm", "install", "pptxgenjs"],
            cwd=str(work_dir),
            timeout=SUBPROCESS_TIMEOUT_NPM
        )
        if rc != 0:
            return {"success": False, "thumbnail_count": 0, "error": f"npm install failed: {stderr[:400]}"}

        # ── Step 3: node generate.js → output.pptx ───────────────────────────
        rc, stdout, stderr = _run(
            ["node", str(gen_js)],
            cwd=str(work_dir),
            timeout=SUBPROCESS_TIMEOUT_NODE
        )
        pptx = work_dir / "output.pptx"
        if rc != 0 or not pptx.exists() or pptx.stat().st_size == 0:
            error = stderr[:400] or stdout[:400] or "Unknown node error (empty output)"
            return {"success": False, "thumbnail_count": 0, "error": f"node generate.js failed: {error}"}

        # Copy .pptx to output dir
        shutil.copy2(str(pptx), str(out_dir / "presentation.pptx"))

        # ── Step 4: soffice → output.pdf ─────────────────────────────────────
        thumbnail_count = 0
        rc, _, stderr = _run(
            ["soffice", "--headless", "--convert-to", "pdf", str(pptx)],
            cwd=str(work_dir),
            timeout=SUBPROCESS_TIMEOUT_SOFFICE
        )
        pdf = pptx.with_suffix(".pdf")
        if rc != 0 or not pdf.exists():
            # QA unavailable — .pptx still delivered successfully
            return {"success": True, "thumbnail_count": 0, "error": None}

        # ── Step 5: pdftoppm → slide-N.jpg ───────────────────────────────────
        rc, _, stderr = _run(
            ["pdftoppm", "-jpeg", "-r", "150", str(pdf), str(work_dir / "slide")],
            cwd=str(work_dir),
            timeout=SUBPROCESS_TIMEOUT_PDFTOPPM
        )
        if rc == 0:
            thumbs = sorted(work_dir.glob("slide-*.jpg")) or sorted(work_dir.glob("slide*.jpg"))
            for i, t in enumerate(thumbs, start=1):
                shutil.copy2(str(t), str(out_dir / f"slide-{i}.jpg"))
            thumbnail_count = len(thumbs)

        return {"success": True, "thumbnail_count": thumbnail_count, "error": None}

    except Exception as e:
        return {"success": False, "thumbnail_count": 0, "error": str(e)}
    finally:
        # Always clean up the temp work dir
        shutil.rmtree(str(work_dir), ignore_errors=True)


@app.get("/download/{job_id}")
def download(job_id: str):
    """Serve the generated .pptx file for download."""
    p = OUTPUT_BASE / job_id / "presentation.pptx"
    if not p.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No presentation for job '{job_id}'. It may have expired or failed."
        )
    return FileResponse(
        path=str(p),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename="presentation.pptx",
        headers={"Content-Disposition": "attachment; filename=presentation.pptx"}
    )


@app.get("/thumbnail/{job_id}/{n}")
def thumbnail(job_id: str, n: int):
    """Serve a slide thumbnail image."""
    p = OUTPUT_BASE / job_id / f"slide-{n}.jpg"
    if not p.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Thumbnail {n} not found for job '{job_id}'."
        )
    return FileResponse(path=str(p), media_type="image/jpeg")
