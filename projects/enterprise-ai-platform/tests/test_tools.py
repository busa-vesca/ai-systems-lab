from unittest.mock import MagicMock

import pytest
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
        (
            DatabaseHealthTool(
                make_session_factory(scalar_result=1),
            ),
        )
    )

    result = executor.execute(
        ToolCall(name="check_database_health", arguments={})
    )

    assert result.status is ToolExecutionStatus.SUCCEEDED
    assert result.output == {"database_available": True}
    assert result.error is None


def test_database_health_tool_rejects_arguments() -> None:
    executor = SafeToolExecutor(
        (
            DatabaseHealthTool(
                make_session_factory(scalar_result=1),
            ),
        )
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


def test_executor_rejects_tool_outside_allowlist() -> None:
    executor = SafeToolExecutor(())

    with pytest.raises(ToolNotAllowedError):
        executor.execute(ToolCall(name="run_shell", arguments={}))
