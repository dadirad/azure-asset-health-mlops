from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.predict import score


app = FastAPI(
    title="Azure Asset Health MLOps",
    description="Asset health anomaly scoring API (Milestone B).",
    version="0.1.0",
)


class TelemetryRecord(BaseModel):
    asset_id: str = Field(..., description="Asset identifier")
    timestamp: str = Field(..., description="ISO-8601 timestamp")
    temp_c: Optional[float] = None
    vibration: Optional[float] = None
    pressure_bar: Optional[float] = None
    rpm: Optional[float] = None


class ScoreRequest(BaseModel):
    records: List[TelemetryRecord] = Field(..., min_length=1, description="List of telemetry records")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/score")
def score_endpoint(req: ScoreRequest) -> Dict[str, Any]:
    try:
        records = [r.model_dump() for r in req.records]
        result = score(records)
        return result
    except FileNotFoundError as e:
        # Model artifacts missing
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        # Schema / feature errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
