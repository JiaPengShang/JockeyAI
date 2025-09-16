from abc import ABC, abstractmethod
from typing import Tuple, List, Literal, TypedDict, Optional, Any

__all__ = [
    "Point", "Polygon4", "Action",
    "Item", "Meta", "PluginOutput",
    "Plugin",
    "to_poly4_any", "validate_plugin_output",
]


Point = Tuple[int, int]                      # (x, y)
Polygon4 = List[Point]                       # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
Action = Literal["keep", "fix", "drop", "review"]

# plugins ocr data
class Item(TypedDict, total=False):
    index: int
    box: Polygon4               # polygon proto
    orig: str                   # ori texts input
    corr: str                   # correction typename
    changed: bool
    ocr_score: Optional[float]
    corr_conf: Optional[float]
    action: Action
    reason: Optional[str]
    source: str                 # plugins name
    char_agreement: Optional[float]  # modified similarity score

# plugins meta data
class Meta(TypedDict, total=False):
    stage: str      # stage name
    version: str    # version name

# plugins merged output
class PluginOutput(TypedDict, total=False):
    items: List[Item]
    meta: Meta


class Plugin(ABC):
    """
    Unified plugins protocol:
- Input: image_path (required), upstream output (optional; None indicates a default starting point)
- Output: Must conform to the PluginOutput schema, and all items must contain a 4-point polygon box.
    """
    name: str = "plugins"
    version: str = "v1"

    @abstractmethod
    def process(
        self,
        image_path: str,
        upstream: Optional[PluginOutput] = None,
        **kwargs: Any,
    ) -> PluginOutput:
        raise NotImplementedError

# ---- Tools ----
def to_poly4_any(box: Any) -> Polygon4:
        """
        Converts a rectangle [x1, y1, x2, y2] or a NumPy/Torch tensor to a 4-point polygon.
If it is already a 4-point polygon, ensure it is int.
        """
        # numpy/torch
        if hasattr(box, "tolist"):
            box = box.tolist()

        # square
        if isinstance(box, (list, tuple)) and len(box) == 4 and all(isinstance(v, (int, float)) for v in box):
            x1, y1, x2, y2 = box
            box = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]

        # exception handling
        if not (isinstance(box, (list, tuple)) and len(box) == 4 and all(
                isinstance(pt, (list, tuple)) and len(pt) == 2 for pt in box)):
            raise ValueError("box must be a 4-point polygon or rect [x1,y1,x2,y2]")

        return [(int(pt[0]), int(pt[1])) for pt in box]  # type: ignore


def validate_plugin_output(out: PluginOutput, require_boxes: bool = True) -> None:
        """
        Quick check: Conforms to the unified schema requirements.
- By default, all items are required to have a 4-dot box (this is mandatory in your protocol).
- Contains at least the items field (can be an empty list).
        """
        if not isinstance(out, dict):
            raise ValueError("PluginOutput must be a dict")

        items = out.get("items", [])
        if items is None or not isinstance(items, list):
            raise ValueError("PluginOutput.items must be a list")

        for i, it in enumerate(items):
            if not isinstance(it, dict):
                raise ValueError(f"items[{i}] must be a dict")
            if require_boxes:
                if "box" not in it:
                    raise ValueError(f"items[{i}].box is required by protocol")
                it["box"] = to_poly4_any(it["box"])


            if "index" not in it:
                it["index"] = i
            if "orig" not in it:
                it["orig"] = it.get("corr", "")
            if "corr" not in it:
                it["corr"] = it.get("orig", "")

            it.setdefault("changed", it.get("orig", "") != it.get("corr", ""))
            it.setdefault("action", "keep")
            it.setdefault("source", "plugins")

        out.setdefault("tables", [])
        meta = out.setdefault("meta", {})
        meta.setdefault("stage", "plugins")
        meta.setdefault("version", "v1")