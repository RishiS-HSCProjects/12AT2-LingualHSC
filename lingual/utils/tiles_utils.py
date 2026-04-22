from dataclasses import dataclass, field
from typing import Any, Iterable

@dataclass()
class TileItem:
    """ Represents an individual tile item with a value, category, label, and optional payload. """
    value: str
    category: str = ""
    label: str | None = None
    payload: dict[str, Any] = field(default_factory=dict) # field(default_factory=dict) to avoid mutable default argument

    def to_dict(self) -> dict[str, Any]:
        """ Convert the TileItem instance to a dictionary with payload (if it exists). """
        
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
    """ Represents a section of tiles, containing an ID, title, description, and a list of TileItems. """
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
                # If the item is already a TileItem instance, we can directly append it to the tiles list.
                self.tiles.append(item)
                continue

            # Create a TileItem from the tuple (value, category) and add it to the tiles list.
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
