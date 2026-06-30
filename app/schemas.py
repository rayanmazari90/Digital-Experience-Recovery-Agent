from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class ScenarioCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class Scenario(BaseModel):
    id: str
    name: str
    description: str
    data: dict[str, Any]
    created_at: str


class SessionCreate(BaseModel):
    scenario_id: str
    title: str = Field(min_length=1)


class Session(BaseModel):
    id: str
    scenario_id: str
    title: str
    status: Literal["created", "running", "stopped", "completed"]
    created_at: str


class RunStart(BaseModel):
    session_id: str
    prompt: str = "Start synthetic digital experience recovery run."


class Run(BaseModel):
    id: str
    session_id: str
    status: Literal["running", "stopped", "completed", "failed"]
    hermes_thread_id: str | None = None
    started_at: str
    stopped_at: str | None = None
    prompt: str


class EventCreate(BaseModel):
    event_type: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class Event(BaseModel):
    id: int
    run_id: str
    event_type: str
    payload: dict[str, Any]
    created_at: str


class Artifact(BaseModel):
    id: str
    session_id: str
    filename: str
    content_type: str
    storage_path: str
    size_bytes: int
    sha256: str
    created_at: str


class EvidenceCreate(BaseModel):
    source_type: str = Field(min_length=1)
    title: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    id: str
    session_id: str
    source_type: str
    title: str
    payload: dict[str, Any]
    created_at: str


class OutcomeCreate(BaseModel):
    status: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class Outcome(BaseModel):
    id: str
    session_id: str
    status: str
    summary: str
    payload: dict[str, Any]
    created_at: str


class HistoryResponse(BaseModel):
    session: Session
    runs: list[Run]
    events: list[Event]
    artifacts: list[Artifact]
    evidence: list[Evidence]
    outcomes: list[Outcome]


class HealthResponse(BaseModel):
    status: str
    hermes_enabled: bool
    hermes_base_url: str
