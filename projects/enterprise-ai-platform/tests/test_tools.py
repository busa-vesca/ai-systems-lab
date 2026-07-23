from time import sleep
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from enterprise_ai_platform.tools import (
    DatabaseHealthTool,
    SafeToolExecutor,
    ToolCall,
    ToolExecutionStatus,
    ToolNotAllowedError,
)


def make_session_factory(*, scalar_result: int) -> sessionmaker[Session]:
    session = MagicMock(spec=Session)
    session.scalar.return_value = scalar_result
    context_manager = MagicMock()
    context_manager.__enter__.return_value = session
    context_manager.__exit__.return_value = False
    factory = MagicMock(return_value=context_manager)
    return factory


def test_database_health_tool_returns_success() -> None:
    executor = SafeToolExecutor(
        (DatabaseHealthTool(make_session_factory(scalar_result=1)),)
    )

    result = executor.execute(
        ToolCall(name="check_database_health", arguments={})
    )

    assert result.status is ToolExecutionStatus.SUCCEEDED
    assert result.output == {"database_available": True}
    assert result.error is None
    assert result.attempts == 1


def test_database_health_tool_rejects_arguments() -> None:
    executor = SafeToolExecutor(
        (DatabaseHealthTool(make_session_factory(scalar_result=1)),)
    )

    result = executor.execute(
        ToolCall(
            name="check_database_health",
            arguments={"sql": "DROP TABLE incidents"},
        )
    )

    assert result.status is ToolExecutionStatus.FAILED
    assert result.output == {}
    assert result.error == "invalid tool arguments"
    assert result.attempts == 1


def test_executor_rejects_tool_outside_allowlist() -> None:
    executor = SafeToolExecutor(())

    with pytest.raises(ToolNotAllowedError):
        executor.execute(ToolCall(name="run_shell", arguments={}))


class FlakyTool:
    name = "flaky"
    retry_safe = True

    def __init__(self) -> None:
        self.calls = 0

    def run(self, _arguments: dict[str, object]) -> dict[str, object]:
        self.calls += 1
        if self.calls == 1:
            raise SQLAlchemyError("temporary failure")
        return {"recovered": True}


class SlowTool:
    name = "slow"
    retry_safe = True

    def run(self, _arguments: dict[str, object]) -> dict[str, object]:
        sleep(0.05)
        return {"finished": True}


class UnsafeFailingTool:
    name = "unsafe"
    retry_safe = False

    def __init__(self) -> None:
        self.calls = 0

    def run(self, _arguments: dict[str, object]) -> dict[str, object]:
        self.calls += 1
        raise SQLAlchemyError("failure")


def test_retry_safe_tool_recovers_on_second_attempt() -> None:
    tool = FlakyTool()
    executor = SafeToolExecutor(
        (tool,),
        max_attempts=2,
        retry_delay_seconds=0,
    )

    result = executor.execute(ToolCall(name="flaky", arguments={}))

    assert result.status is ToolExecutionStatus.SUCCEEDED
    assert result.output == {"recovered": True}
    assert result.attempts == 2
    assert tool.calls == 2


def test_slow_tool_returns_controlled_timeout() -> None:
    executor = SafeToolExecutor(
        (SlowTool(),),
        max_attempts=1,
        timeout_seconds=0.01,
    )

    result = executor.execute(ToolCall(name="slow", arguments={}))

    assert result.status is ToolExecutionStatus.FAILED
    assert result.error == "tool execution timed out"
    assert result.attempts == 1


def test_non_retry_safe_tool_is_never_repeated() -> None:
    tool = UnsafeFailingTool()
    executor = SafeToolExecutor(
        (tool,),
        max_attempts=3,
        retry_delay_seconds=0,
    )

    result = executor.execute(ToolCall(name="unsafe", arguments={}))

    assert result.status is ToolExecutionStatus.FAILED
    assert result.attempts == 1
    assert tool.calls == 1
