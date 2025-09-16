# plugins/ppocr_plugin.py
from typing import Optional, Any

from plugins.base import Plugin, PluginOutput, to_poly4_any, validate_plugin_output
from paddleocr import PaddleOCR

class PaddleocrPlugin(Plugin):
    name = "paddleocr"
    version = "v5"

    def __init__(self, lang: str = "en", device: str = "gpu") -> None:
        self.lang = lang
        self.device = device
        self.ocr = PaddleOCR(lang=lang, use_textline_orientation=True, device=device)

    def process(
        self,
        image_path: str,
        upstream: Optional[PluginOutput] = None,
        **kwargs: Any,
    ) -> PluginOutput:
        # run PP-OCR
        print(f">>> running {self.name} plugin...")
        results = self.ocr.predict(image_path)
        res = results[0] if isinstance(results, list) else results

        # PP-OCR data encoding
        polys  = res.get("rec_polys") or res.get("dt_polys") or res.get("rec_boxes") or []
        texts  = res.get("rec_texts")  or [""] * len(polys)
        scores = res.get("rec_scores") or [None] * len(polys)

        items = []
        for i, (box, txt, sc) in enumerate(zip(polys, texts, scores)):
            items.append({
                "index": i,
                "box": to_poly4_any(box),  # polygon
                "orig": txt,
                "corr": txt,
                "changed": False,
                "ocr_score": sc,
                "corr_conf": None,
                "action": "keep",
                "reason": None,
                "source": self.name,
            })

        out: PluginOutput = {
            "items": items,
            "meta": {"stage": self.name, "version": self.version},
        }


        # validate
        validate_plugin_output(out, require_boxes=True)
        return out
