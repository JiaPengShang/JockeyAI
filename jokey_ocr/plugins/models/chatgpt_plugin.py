from __future__ import annotations
import base64
import json
from typing import Optional, Any, Dict, List
import requests
from PIL import Image

from plugins.base import Plugin, PluginOutput, validate_plugin_output


def encode_image_to_data_url(path: str) -> str:
    """Convert image to base64 data URL for API input."""
    with Image.open(path) as im:
        im = im.convert("RGB")
        from io import BytesIO
        buf = BytesIO()
        im.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{b64}"


class ChatgptRefinePlugin(Plugin):
    name = "gpt_refine"
    version = "v4o"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5",
        api_base: str = "https://api.openai.com/v1",
        system_tip: Optional[str] = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        self.system_tip = system_tip

    def _build_sys_msg(self) -> str:
        """System prompt (English)."""
        return self.system_tip or (
            "You are a *pluginized* document understanding and correction module.\n"
            "Inputs: (1) the original image; (2) the upstream unified JSON (items/meta).\n"
            "Rules: The IMAGE is the source of truth; upstream JSON is evidence/candidates.\n"
            "Task: For each item, review items.orig/corr and fix if needed. "
            "Fill corr_conf/action/reason when you change something.\n"
            "Hard requirements:\n"
            "  - Output **one single line** of JSON only (same schema: items/meta). No extra text.\n"
            "  - For every items[i]: if you modify it, set changed=true, and set action (keep|fix|drop|review) and a brief reason.\n"
            "  - Keep index stable; reuse upstream box when possible."
        )

    def _call_openai(self, payload: Dict[str, Any]) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        print(">>> sending Post")
        resp = requests.post(f"{self.api_base}/chat/completions",
                             headers=headers, data=json.dumps(payload))
        print("<<< response:", resp.status_code)

        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def process(
        self,
        image_path: str,
        upstream: Optional[PluginOutput] = None,
        **kwargs: Any,
    ) -> PluginOutput:
        # 1) Inputs
        print(f">>> running {self.name} plugin...")
        image_data_url = encode_image_to_data_url(image_path)
        prev_json = upstream or {"items": [], "meta": {"stage": "start", "version": "v1"}}

        sys_msg = self._build_sys_msg()
        print(sys_msg)
        user_msgs: List[Dict[str, Any]] = [
            {"type": "image_url", "image_url": {"url": image_data_url}},
            {"type": "text",
             "text": "Here is the upstream unified JSON (items/meta). "
                     "Strictly follow the plugin contract and output JSON with the same schema only:\n"
                     + json.dumps(prev_json, ensure_ascii=False)},
        ]

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msgs},
            ],
        }

        # 2) Call GPT
        print(">>> calling GPT...")
        content = self._call_openai(payload)
        print("<<< response finish:")

        # 3) Parse output
        print(">>> parsing GPT output...")
        content = content.strip()
        line = content.splitlines()[-1].strip() if content else ""
        if not (line.startswith("{") and line.endswith("}")):
            raise ValueError("GPT output is not a single-line JSON.")

        out: PluginOutput = json.loads(line)

        # Ensure meta reflects current stage
        meta = out.setdefault("meta", {})
        meta.setdefault("stage", self.name)
        meta.setdefault("version", self.version)

        # Normalize items: index, box fallback, correct `source`
        items = out.get("items", [])
        prev_items = (prev_json or {}).get("items", [])
        for i, it in enumerate(items):
            if not isinstance(it, dict):
                continue
            it.setdefault("index", i)

            # Keep/restore box if missing
            if ("box" not in it or not it["box"]) and i < len(prev_items):
                if isinstance(prev_items[i], dict) and "box" in prev_items[i]:
                    it["box"] = prev_items[i]["box"]

            # Decide whether this item is refined here
            changed_flag = it.get("changed") is True
            action = (it.get("action") or "").lower()
            corr = it.get("corr")
            orig = it.get("orig")
            refined = changed_flag or action in {"fix", "drop", "review"} or (corr is not None and corr != orig)

            if refined:
                it["source"] = self.name
            else:
                # keep prior source if exists, otherwise default to current
                if "source" not in it and i < len(prev_items) and isinstance(prev_items[i], dict):
                    it["source"] = prev_items[i].get("source", self.name)
                else:
                    it.setdefault("source", self.name)

        # 4) Validate
        validate_plugin_output(out, require_boxes=True)
        return out
