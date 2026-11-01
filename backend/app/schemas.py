"""Response models for the API contract (PRD section 10)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ConvertResponse(BaseModel):
    text: str = Field(description="ASCII/emoji art, lines separated by newline")
    width: int = Field(description="Columns in the result grid")
    height: int = Field(description="Rows in the result grid")
    mode: str = Field(description="ascii or emoji")


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str
