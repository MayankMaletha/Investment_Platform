"""Runtime compatibility patches for local development/test interpreters."""

from __future__ import annotations

import inspect
from typing import Any, ForwardRef, cast


def _patch_pydantic_v1_forward_refs() -> None:
    """Make Pydantic v1's forward-ref helper compatible with Python 3.12."""
    try:
        from pydantic.v1 import typing as pydantic_v1_typing
    except Exception:
        return

    evaluate = ForwardRef._evaluate
    if "recursive_guard" not in inspect.signature(evaluate).parameters:
        return

    def evaluate_forwardref(type_: ForwardRef, globalns: Any, localns: Any) -> Any:
        return cast(Any, type_)._evaluate(
            globalns,
            localns,
            recursive_guard=set(),
        )

    pydantic_v1_typing.evaluate_forwardref = evaluate_forwardref


_patch_pydantic_v1_forward_refs()
