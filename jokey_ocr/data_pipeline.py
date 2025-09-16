from __future__ import annotations

import argparse
import json
from pathlib import Path

from plugins.base import PluginOutput, validate_plugin_output
from plugins.models.ali_table_gen_plugin import AliTableGenPlugin

from plugins.models.chatgpt_plugin import ChatgptRefinePlugin
from plugins.models.gpt_table_gen_plugin import GptTableGenPlugin
from plugins.models.ppocr_plugin import PaddleocrPlugin
from plugins.tools.char_agreement_plugin import CharAgreementPlugin


def load_plugin_cfg(path: str | None) -> dict:
    """Load plugin configuration from a JSON file (path only)."""
    if not path:
        return {}
    p = Path(path)
    if p.suffix.lower() == ".json" and p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"Plugin config not found: {p}")


def main():
    ap = argparse.ArgumentParser(description="Plugin pipeline")
    ap.add_argument("input", type=str, help="input image path")
    ap.add_argument("--out_json", type=str, default=None, help="save final JSON to path")
    ap.add_argument("--char_set_action", action="store_true",
                    help="Enable CharAgreementPlugin to set action based on thresholds")
    ap.add_argument("--pipeline", type=str,
                    default="paddleocr,gpt_refine,char_agreement,ali_table",
                    help="comma-separated plugins, e.g. 'paddleocr,gpt_refine,char_agreement'")
    ap.add_argument("--plugin_cfg", type=str, default=None,
                    help="path to JSON config file for plugins")
    args = ap.parse_args()

    img = str(Path(args.input))
    if not Path(img).exists():
        raise FileNotFoundError(img)

    # Load plugin config
    plugin_cfg = load_plugin_cfg(args.plugin_cfg)

    def _get(name: str):
        name = name.strip().lower()

        if name in {"ali_table", "ali_table_gen", "dashscope_table", "qwen_table"}:
            print("in")
            cfg = dict(plugin_cfg.get("ali_table", {}))
            if not cfg.get("api_key"):
                raise ValueError("ali_table requires its own api_key (set in --plugin_cfg.ali_table.api_key)")
            cfg.setdefault("api_base", "https://dashscope.aliyuncs.com/compatible-mode/v1")
            cfg.setdefault("model", "qwen-plus")
            return AliTableGenPlugin(**cfg)

        if name == "paddleocr":
            cfg = {"lang": "en"}
            cfg.update(plugin_cfg.get("paddleocr", {}))
            cfg.setdefault("device", "cpu")  # default to CPU
            return PaddleocrPlugin(**cfg)

        if name in {"gpt_refine", "chatgpt"}:
            cfg = dict(plugin_cfg.get("gpt_refine", {}))
            if not cfg.get("api_key"):
                raise ValueError("gpt_refine requires an OpenAI api_key "
                                 "(set in --plugin_cfg.gpt_refine.api_key)")
            return ChatgptRefinePlugin(**cfg)

        if name in {"char_agreement", "char"}:
            cfg = {"set_action": args.char_set_action}
            cfg.update(plugin_cfg.get("char_agreement", {}))
            return CharAgreementPlugin(**cfg)

        if name in {"ali_table", "ali_table_gen", "dashscope_table", "qwen_table"}:
            cfg = dict(plugin_cfg.get("ali_table", {}))
            if not cfg.get("api_key"):
                raise ValueError("ali_table requires its own api_key (set in --plugin_cfg.ali_table.api_key)")
            cfg.setdefault("api_base", "https://dashscope.aliyuncs.com/compatible-mode/v1")
            cfg.setdefault("model", "qwen-plus")
            return AliTableGenPlugin(**cfg)

        # —— 新增：GPT 表格生成 ——
        if name in {"gpt_table", "openai_table"}:
            cfg = dict(plugin_cfg.get("gpt_table", {}))
            if not cfg.get("api_key"):
                raise ValueError("gpt_table requires an OpenAI api_key (set in --plugin_cfg.gpt_table.api_key)")
            cfg.setdefault("api_base", "https://api.openai.com/v1")
            cfg.setdefault("model", "gpt-5")
            return GptTableGenPlugin(**cfg)

        raise ValueError(f"Unknown plugin: {name}")

    # Build pipeline
    plugin_names = [s for s in args.pipeline.split(",") if s.strip()]
    pipeline = [_get(n) for n in plugin_names]

    # Run pipeline
    out: PluginOutput = {"items": [], "meta": {"stage": "start", "version": "v1"}}
    for plugin in pipeline:
        out = plugin.process(img, upstream=out)
        validate_plugin_output(out, require_boxes=True)
        print(f"[{plugin.name}] processed, items: {len(out.get('items', []))}")

    if args.out_json:
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"[Saved JSON] {args.out_json}")


if __name__ == "__main__":
    main()
