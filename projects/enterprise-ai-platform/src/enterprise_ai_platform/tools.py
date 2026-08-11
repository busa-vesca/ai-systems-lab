import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
from enum import StrEnum
from time import sleep
from time import perf_counter
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError
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
    idempotency_key: str = Field(min_length=1, max_length=200)


@dataclass(frozen=True, slots=True)
class ToolResult:
    tool_name: str
    status: ToolExecutionStatus
    output: dict[str, Any]
    error: str | None
    latency_ms: float
    attempts: int
    idempotency_key: str


class ToolNotAllowedError(Exception):
    """The requested tool is outside the executor allowlist."""


class Tool(Protocol):
    name: str
    retry_safe: bool
    requires_approval: bool

    def run(
        self,
        arguments: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> dict[str, Any]: ...


class DatabaseHealthArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DatabaseHealthTool:
    name = "check_database_health"
    retry_safe = True
    requires_approval = False

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def run(
        self,
        arguments: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        del idempotency_key
        DatabaseHealthArguments.model_validate(arguments)
        with self._session_factory() as session:
            database_available = session.scalar(text("SELECT 1")) == 1
        return {"database_available": database_available}


class SafeToolExecutor:
    def __init__(
        self,
        tools: tuple[Tool, ...],
        *,
        max_attempts: int = 2,
        timeout_seconds: float = 2.0,
        retry_delay_seconds: float = 0.1,
        max_workers: int = 4,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must not be negative")
        self._tools = {tool.name: tool for tool in tools}
        self._max_attempts = max_attempts
        self._timeout_seconds = timeout_seconds
        self._retry_delay_seconds = retry_delay_seconds
        self._worker_pool = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="safe-tool",
        )

    def requires_approval(self, tool_name: str) -> bool:
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ToolNotAllowedError(f"tool is not allowed: {tool_name}")
        return getattr(tool, "requires_approval", True)

    def is_retry_safe(self, tool_name: str) -> bool:
        tool = self._tools.get(tool_name)
        if tool is None:
            raise ToolNotAllowedError(f"tool is not allowed: {tool_name}")
        return tool.retry_safe

    def execute(self, call: ToolCall) -> ToolResult:
        tool = self._tools.get(call.name)
        if tool is None:
            raise ToolNotAllowedError(f"tool is not allowed: {call.name}")

        started_at = perf_counter()
        attempt_limit = self._max_attempts if tool.retry_safe else 1
        error_message = "tool execution failed"

        for attempt in range(1, attempt_limit + 1):
            future = self._worker_pool.submit(
                tool.run,
                call.arguments,
                idempotency_key=call.idempotency_key,
            )
            try:
                output = future.result(timeout=self._timeout_seconds)
                return ToolResult(
                    tool_name=call.name,
                    status=ToolExecutionStatus.SUCCEEDED,
                    output=output,
                    error=None,
                    latency_ms=(perf_counter() - started_at) * 1_000,
                    attempts=attempt,
                    idempotency_key=call.idempotency_key,
                )
            except ValidationError:
                future.cancel()
                error_message = "invalid tool arguments"
                break
            except TimeoutError:
                future.cancel()
                error_message = "tool execution timed out"
                logger.warning(
                    "tool execution timed out",
                    extra={"tool_name": call.name, "attempt": attempt},
                )
            except SQLAlchemyError:
                error_message = "tool execution failed"
                logger.exception(
                    "database health tool failed",
                    extra={"tool_name": call.name, "attempt": attempt},
                )
            except Exception:
                error_message = "tool execution failed"
                logger.exception(
                    "tool execution failed",
                    extra={"tool_name": call.name, "attempt": attempt},
                )
                break

            if attempt < attempt_limit:
                sleep(self._retry_delay_seconds)

        return ToolResult(
            tool_name=call.name,
            status=ToolExecutionStatus.FAILED,
            output={},
            error=error_message,
            latency_ms=(perf_counter() - started_at) * 1_000,
            attempts=attempt,
            idempotency_key=call.idempotency_key,
        )
