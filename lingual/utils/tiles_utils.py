from dataclasses import dataclass, field
from typing import Any, Iterable

@dataclass(frozen=True)
class TileItem:
    value: str
    category: str = ""
    label: str | None = None
    payload: dict[str, Any] = field(default_factory=dict) # field(default_factory=dict) to avoid mutable default argument. Recommendation from GitHub Copilot.

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "value": self.value,
            "category": self.category,
            "label": self.label if self.label is not None else self.value,
        }

        if self.payload:
            data["payload"] = self.payload

        return data

@dataclass
class TileSection:
    id: str
    title: str
    description: str = ""
    tiles: list[TileItem] = field(default_factory=list)

    def add_tile(self, value: str, category: str = "", label: str | None = None, payload: dict[str, Any] | None = None) -> "TileSection":
        self.tiles.append(
            TileItem(
                value=value,
                category=category,
                label=label,
                payload=payload or {},
            )
        )
        return self

    def add_tiles(self, items: Iterable[TileItem | tuple[str, Any]]) -> "TileSection":
        for item in items:
            if isinstance(item, TileItem):
                self.tiles.append(item)
                continue

            value, category = item
            category_name = getattr(category, "name", str(category)) if category is not None else ""
            self.add_tile(str(value), category=category_name)

        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tiles": [tile.to_dict() for tile in self.tiles],
        }
