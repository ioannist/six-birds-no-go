"""Witness registry loader utilities."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Witness:
    """Immutable witness record with raw payload."""

    id: str
    raw: dict[str, Any]


def parse_rational(value: Any) -> Fraction:
    """Parse rational values from integer or string forms."""
    if isinstance(value, bool):
        raise ValueError("boolean is not a rational number")
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("empty rational string")
        if "." in text:
            raise ValueError(f"decimal literals are not allowed: {value!r}")
        return Fraction(text)
    raise ValueError(f"unsupported rational value type: {type(value).__name__}")


def load_witness_registry(config_path: str = "configs/witnesses.yaml") -> dict[str, Any]:
    path = Path(config_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level must be an object")
    return data


def list_witness_ids(config_path: str = "configs/witnesses.yaml") -> list[str]:
    data = load_witness_registry(config_path)
    witnesses = data.get("witnesses")
    if not isinstance(witnesses, list):
        raise ValueError("witnesses must be a list")
    ids: list[str] = []
    for item in witnesses:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            ids.append(item["id"])
    return ids


def load_witness(witness_id: str, config_path: str = "configs/witnesses.yaml") -> Witness:
    data = load_witness_registry(config_path)
    witnesses = data.get("witnesses")
    if not isinstance(witnesses, list):
        raise ValueError("witnesses must be a list")

    for item in witnesses:
        if isinstance(item, dict) and item.get("id") == witness_id:
            return Witness(id=witness_id, raw=item)
    raise KeyError(f"unknown witness id: {witness_id}")


def matrix_to_fractions(matrix: list[list[Any]]) -> list[list[Fraction]]:
    """Convert a matrix of rational-encoded values into Fractions."""
    return [[parse_rational(x) for x in row] for row in matrix]


def vector_to_fractions(vector: list[Any]) -> list[Fraction]:
    """Convert a rational-encoded vector into Fractions."""
    return [parse_rational(x) for x in vector]
