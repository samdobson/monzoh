"""Type definitions for Monzo API data structures."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    # JSON-compatible value types (recursive)
    JSONValue: TypeAlias = str | int | float | bool | None | "JSONObject" | "JSONArray"
    JSONObject: TypeAlias = dict[str, JSONValue]
    JSONArray: TypeAlias = list[JSONValue]
else:
    # Runtime definitions to avoid circular references
    JSONValue: TypeAlias = str | int | float | bool | None | dict | list
    JSONObject: TypeAlias = dict[str, JSONValue]
    JSONArray: TypeAlias = list[JSONValue]

# Metadata type for transaction annotations and similar key-value data
MetadataValue: TypeAlias = str | int | float | bool | None
Metadata: TypeAlias = dict[str, MetadataValue]
