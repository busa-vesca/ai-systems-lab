import logging
from dataclasses import dataclass
from enum import StrEnum
from time import perf_counter
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker


logger = logging.getLogger(__name__)


class ToolExecutionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ToolResult:
    tool_name: str
    status: ToolExecutionStatus
    output: dict[str, Any]
    error: str | None
    latency_ms: float


class ToolNotAllowedError(Exception):
    """The requested tool is outside the executor allowlist."""


class Tool(Protocol):
    name: str

    def run(self, arguments: dict[str, Any]) -> dict[str, Any]: ...


class DatabaseHealthArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DatabaseHealthTool:
    name = "check_database_health"

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        DatabaseHealthArguments.model_validate(arguments)
        with self._session_factory() as session:
            database_available = session.scalar(text("SELECT 1")) == 1
        return {"database_available": database_available}


class SafeToolExecutor:
    def __init__(self, tools: tuple[Tool, ...]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def execute(self, call: ToolCall) -> ToolResult:
        tool = self._tools.get(call.name)
        if tool is None:
            raise ToolNotAllowedError(f"tool is not allowed: {call.name}")

        started_at = perf_counter()
        try:
            output = tool.run(call.arguments)
            status = ToolExecutionStatus.SUCCEEDED
            error_message = None
        except ValidationError:
            output = {}
            status = ToolExecutionStatus.FAILED
            error_message = "invalid tool arguments"
        except SQLAlchemyError:
            logger.exception("database health tool failed")
            output = {}
            status = ToolExecutionStatus.FAILED
            error_message = "tool execution failed"

        return ToolResult(
            tool_name=call.name,
            status=status,
            output=output,
            error=error_message,
            latency_ms=(perf_counter() - started_at) * 1_000,
        )
