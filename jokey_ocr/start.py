#!/usr/bin/env python3
"""
start.py
- Reads a single global config.json
- Picks profile + input/output paths from config.json
- Builds --pipeline and --plugin_cfg for data_pipeline.py
- One click: just `python start.py`
"""
import json, os, sys, subprocess
import tempfile
from pathlib import Path

def main():
    cfg_path = os.environ.get("OCR_PIPELINE_CONFIG", "config.json")
    profile = None

    # optional: allow override profile or config
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--profile" and i + 1 < len(sys.argv):
            profile = sys.argv[i+1]
            i += 2
            continue
        if sys.argv[i] == "--config" and i + 1 < len(sys.argv):
            cfg_path = sys.argv[i+1]
            i += 2
            continue
        i += 1

    cfg_p = Path(cfg_path)
    if not cfg_p.exists():
        raise FileNotFoundError(f"Config not found: {cfg_p}")

    cfg = json.loads(cfg_p.read_text(encoding="utf-8"))
    if not profile:
        profile = cfg.get("default_profile", "prod")
    prof = cfg["profiles"][profile]

    # 从 config.json 读取输入输出路径
    input_path = cfg.get("input_path", "./input.png")
    out_json = cfg.get("output_path", "./result.json")

    # Build pipeline according to enabled flags
    steps = ["paddleocr"]
    if prof.get("char_agreement", {}).get("enabled"):
        steps.append("char_agreement")
    if prof.get("chatgpt", {}).get("enabled"):
        steps.append("gpt_refine")


    if prof.get("gpt_table", {}).get("enabled"):
        steps.append("gpt_table")
    if prof.get("ali_table", {}).get("enabled"):
        steps.append("ali_table")
    pipeline = ",".join(steps)

    # Build plugin_cfg mapping expected by data_pipeline.py
    plugin_cfg = {}
    plugin_cfg["paddleocr"] = {
        "lang": prof.get("paddleocr", {}).get("lang", "en")
    }

    # —— 新增：gpt_table ——
    if "gpt_table" in prof:
        g = prof["gpt_table"]
        plugin_cfg["gpt_table"] = {}
        if g.get("api_key"):
            plugin_cfg["gpt_table"]["api_key"] = g["api_key"]
        if g.get("model"):
            plugin_cfg["gpt_table"]["model"] = g["model"]
        if g.get("api_base"):
            plugin_cfg["gpt_table"]["api_base"] = g["api_base"]
        if g.get("out"):
            plugin_cfg["gpt_table"]["out"] = g["out"]
        if g.get("format"):
            plugin_cfg["gpt_table"]["format"] = g["format"]
        if g.get("sheet_name"):
            plugin_cfg["gpt_table"]["sheet_name"] = g["sheet_name"]

    if "chatgpt" in prof:
        c = prof["chatgpt"]
        plugin_cfg["gpt_refine"] = {}
        if c.get("api_key"):
            plugin_cfg["gpt_refine"]["api_key"] = c["api_key"]
        if c.get("model"):
            plugin_cfg["gpt_refine"]["model"] = c["model"]
        if c.get("api_base"):
            plugin_cfg["gpt_refine"]["api_base"] = c["api_base"]

    if "char_agreement" in prof:
        ca = prof["char_agreement"]
        plugin_cfg["char_agreement"] = {}
        if "set_action" in ca:
            plugin_cfg["char_agreement"]["set_action"] = bool(ca["set_action"])
        # Whether to add the CLI flag --char_set_action (default False)
        char_set_action = bool(ca.get("set_action", False))
    else:
        char_set_action = False


    if "ali_table" in prof:
        a = prof["ali_table"]
        plugin_cfg["ali_table"] = {}
        # 这三项至少要传，data_pipeline.py 里会校验 api_key
        if a.get("api_key"):
            plugin_cfg["ali_table"]["api_key"] = a["api_key"]
        if a.get("model"):
            plugin_cfg["ali_table"]["model"] = a["model"]
        if a.get("api_base"):
            plugin_cfg["ali_table"]["api_base"] = a["api_base"]
        # 可选输出配置（如果你的 AliTableGenPlugin 支持）
        if a.get("out"):
            plugin_cfg["ali_table"]["out"] = a["out"]
        if a.get("format"):
            plugin_cfg["ali_table"]["format"] = a["format"]
        if a.get("sheet_name"):
            plugin_cfg["ali_table"]["sheet_name"] = a["sheet_name"]



    # Write plugin_cfg to a temporary JSON file; pass file path to subprocess.
    with tempfile.NamedTemporaryFile(prefix="plugin_cfg_", suffix=".json", delete=False, mode="w", encoding="utf-8") as tmp:
        json.dump(plugin_cfg, tmp, ensure_ascii=False)
        cfg_file_path = tmp.name

    cmd = [
        sys.executable, "data_pipeline.py", input_path,
        "--pipeline", pipeline,                 # pipeline is already a string
        "--plugin_cfg", cfg_file_path,          # pass file path instead of inline JSON
        "--out_json", out_json
    ]
    if char_set_action:
        cmd.append("--char_set_action")

    # Print a redacted command (do not leak api key)
    printable_cmd = cmd[:]
    try:
        idx = printable_cmd.index("--plugin_cfg") + 1
        # show only the filename (not contents)
        printable_cmd[idx] = "(cfg file)"
    except Exception:
        pass
    print("Running:", " ".join(printable_cmd))

    subprocess.check_call(cmd)

if __name__ == "__main__":
    main()
