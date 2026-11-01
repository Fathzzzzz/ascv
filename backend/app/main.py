"""FastAPI entry point. Run from `backend/`:

    uvicorn app.main:app --port 8000

The API is a thin wrapper: validation here, pixels in `core` (no rembg import
before shutdown/startup, no FastAPI import inside core).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from core import segmentation
from core import convert_image
from core.errors import (
    CoreError,
    EmptySubjectError,
    InvalidImageError,
    InvalidOptionError,
    SegmentationError,
)

from .constants import APP_VERSION, REMBG_MODEL
from .errors import ImageDimensionsError, PayloadTooLargeError, UnsupportedImageError
from .schemas import ConvertResponse, HealthResponse
from .service import decode_upload, parse_options, read_upload

logger = logging.getLogger("ascv")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load the segmentation model once per process (PRD 11.1)."""
    try:
        await run_in_threadpool(segmentation.preload_model, REMBG_MODEL)
        logger.info("Model segmentasi %s dimuat.", REMBG_MODEL)
    except Exception:  # model download/onnx failure must not kill the server
        logger.exception("Model segmentasi %s gagal dimuat.", REMBG_MODEL)
    yield


app = FastAPI(title="Image to ASCII/Emoji Converter", version=APP_VERSION, lifespan=lifespan)


def error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


@app.exception_handler(PayloadTooLargeError)
async def _payload_too_large(_request, exc: PayloadTooLargeError) -> JSONResponse:
    return error(413, str(exc))


@app.exception_handler(EmptySubjectError)
async def _blank_image(_request, exc: EmptySubjectError) -> JSONResponse:
    return error(400, str(exc))


@app.exception_handler(InvalidOptionError)
async def _invalid_option(_request, exc: InvalidOptionError) -> JSONResponse:
    return error(400, str(exc))


@app.exception_handler(InvalidImageError)
async def _invalid_image(_request, exc: InvalidImageError) -> JSONResponse:
    return error(400, str(exc))


@app.exception_handler(UnsupportedImageError)
async def _unsupported(_request, exc: UnsupportedImageError) -> JSONResponse:
    return error(400, str(exc))


@app.exception_handler(ImageDimensionsError)
async def _dimensions(_request, exc: ImageDimensionsError) -> JSONResponse:
    return error(400, str(exc))


@app.exception_handler(RequestValidationError)
async def _validation(_request, exc: RequestValidationError) -> JSONResponse:
    # The PRD contract uses 400 (not FastAPI's default 422) for bad parameters.
    missing = ", ".join(str(item["loc"][-1]) for item in exc.errors())
    return error(400, f"Parameter tidak valid: {missing}.")


@app.exception_handler(SegmentationError)
async def _segmentation(_request, exc: SegmentationError) -> JSONResponse:
    logger.warning("Segmentasi gagal: %s", exc)
    return error(500, "Segmentasi subjek gagal diproses.")


@app.exception_handler(CoreError)
async def _core(_request, exc: CoreError) -> JSONResponse:
    logger.warning("Pipeline gagal: %s", exc)
    return error(400, str(exc))


@app.exception_handler(Exception)
async def _unexpected(_request, exc: Exception) -> JSONResponse:
    logger.exception("Kegagalan tak terduga", exc_info=exc)
    return error(500, "Pipeline gagal saat memproses gambar.")


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Report server status, whether the model is loaded, and the app version."""
    return HealthResponse(
        status="ok",
        model_loaded=segmentation.is_model_loaded(REMBG_MODEL),
        version=APP_VERSION,
    )


@app.post("/api/convert", response_model=ConvertResponse)
async def convert(
    image: UploadFile = File(...),
    width: str | None = Form(None),
    mode: str | None = Form(None),
    charset: str | None = Form(None),
    invert: str | None = Form(None),
    remove_bg: str | None = Form(None),
) -> ConvertResponse:
    """Convert an uploaded image into ASCII or emoji art."""
    options = parse_options(
        mode=mode, width=width, charset=charset, invert=invert, remove_bg=remove_bg
    )
    data = await read_upload(image.read)

    def run() -> ConvertResponse:
        try:
            decoded = decode_upload(data)
            result = convert_image(decoded, options)
        except (CoreError, UnsupportedImageError, ImageDimensionsError):
            raise  # mapped to 400/500 by the handlers below
        except Exception:
            logger.exception("Pipeline gagal saat memproses gambar")
            raise HTTPException(status_code=500, detail="Pipeline gagal saat memproses gambar.")
        return ConvertResponse(
            text=result.text, width=result.width, height=result.height, mode=result.mode
        )

    return await run_in_threadpool(run)
