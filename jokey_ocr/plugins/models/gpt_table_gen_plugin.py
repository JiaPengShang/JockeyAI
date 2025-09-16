from __future__ import annotations
import json
import base64
from typing import Any, Dict, List, Optional
import requests
import pandas as pd
from PIL import Image

from plugins.base import Plugin, PluginOutput, validate_plugin_output


def _encode_image_to_data_url(path: str) -> str:
    with Image.open(path) as im:
        im = im.convert("RGB")
        from io import BytesIO
        buf = BytesIO()
        im.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{b64}"


class GptTableGenPlugin(Plugin):
    """
    OpenAI (GPT) table generator, mirroring AliTableGenPlugin.
    Inputs: original image + final unified JSON (items/meta)
    Output: tables spec (JSON) and optional rendered file (xlsx/csv/md).
    """
    name = "gpt_table"
    version = "v1"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5",
        api_base: str = "https://api.openai.com/v1",
        out: Optional[str] = None,
        format: str = "xlsx",
        sheet_name: str = "Sheet1",
        system_tip: Optional[str] = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.api_base = api_base.rstrip("/")
        self.out = out
        self.format = (format or "xlsx").lower()
        self.sheet_name = sheet_name
        self.system_tip = system_tip

    # ---- API helpers ----
    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _call_openai(self, messages: List[Dict[str, Any]]) -> str:
        payload = {"model": self.model, "messages": messages}
        resp = requests.post(f"{self.api_base}/chat/completions",
                             headers=self._headers(),
                             data=json.dumps(payload))
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _sys_prompt(self) -> str:
        return self.system_tip or (
            "You are a table designer specialized in understanding documents from IMAGE + OCR JSON.\n"
            "Input: (1) the original image; (2) a unified JSON with items/meta.\n"
            "Goal: Produce meaningful, well-structured tables that reflect the content. "
            "Use corrected text (corr) when available; fall back to orig.\n"
            "Rules:\n"
            " - Reply with ONE SINGLE LINE of JSON only, no extra text.\n"
            " - Schema: {\"tables\":[{\"name\":\"string\",\"columns\":[\"...\"],\"rows\":[[...], ...]}]}\n"
            " - Derive useful columns (normalize numbers/dates, split combined fields) when obvious.\n"
            " - If multiple logical tables exist (e.g., line items vs totals), output multiple entries."
        )

    def _design_tables(self, image_path: str, upstream: PluginOutput) -> Dict[str, Any]:
        image_data_url = _encode_image_to_data_url(image_path)
        messages = [
            {"role": "system", "content": self._sys_prompt()},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": image_data_url}},
                {"type": "text", "text": "Here is the final unified JSON (items/meta). "
                                          "Return ONLY a single-line JSON with the requested tables schema:\n"
                                          + json.dumps(upstream, ensure_ascii=False)}
            ]},
        ]
        out = self._call_openai(messages).strip()
        line = out.splitlines()[-1].strip()
        if not (line.startswith("{") and line.endswith("}")):
            raise ValueError("GptTableGen output is not a single-line JSON.")
        data = json.loads(line)
        if not isinstance(data, dict) or "tables" not in data:
            raise ValueError("GptTableGen JSON must contain a 'tables' array.")
        return data

    def _render(self, tables: List[Dict[str, Any]]) -> Optional[str]:
        if not self.out:
            return None
        out_path = self.out
        fmt = self.format

        if fmt == "xlsx":
            with pd.ExcelWriter(out_path, engine="xlsxwriter") as writer:
                for i, t in enumerate(tables):
                    name = (t.get("name") or f"{self.sheet_name}_{i+1}")[:31]
                    cols = t.get("columns") or []
                    rows = t.get("rows") or []
                    df = pd.DataFrame(rows, columns=cols if cols else None)
                    df.to_excel(writer, index=False, sheet_name=name or f"Sheet{i+1}")
            return out_path

        if fmt == "csv":
            t = tables[0] if tables else {"columns": [], "rows": []}
            cols = t.get("columns") or []
            rows = t.get("rows") or []
            df = pd.DataFrame(rows, columns=cols if cols else None)
            df.to_csv(out_path, index=False)
            return out_path

        if fmt == "md":
            t = tables[0] if tables else {"columns": [], "rows": []}
            cols = t.get("columns") or []
            rows = t.get("rows") or []
            lines = []
            if cols:
                lines.append("| " + " | ".join(cols) + " |")
                lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
            for r in rows:
                vals = [str(v) if v is not None else "" for v in r]
                lines.append("| " + " | ".join(vals) + " |")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return out_path

        raise ValueError(f"Unsupported table format: {fmt}")

    def process(self, image_path: str, upstream: Optional[PluginOutput] = None, **kwargs: Any) -> PluginOutput:
        base = upstream or {"items": [], "meta": {"stage": "start", "version": "v1"}}

        # 1) design tables using OpenAI
        spec = self._design_tables(image_path, base)
        tables = spec.get("tables", [])

        # 2) attach to meta & optionally render
        meta = base.setdefault("meta", {})
        meta["stage"] = self.name
        meta["version"] = self.version

        path = self._render(tables)
        if path:
            meta["table_file"] = path
            meta["table_format"] = self.format

        validate_plugin_output(base, require_boxes=True)
        return base
