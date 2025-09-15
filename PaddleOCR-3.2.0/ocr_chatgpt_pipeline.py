import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image

from paddleocr import PaddleOCR
from tools.infer.utility import draw_ocr


def to_poly4(p):
    if hasattr(p, "tolist"):
        p = p.tolist()
    if len(p) == 4 and all(isinstance(v, (int, float)) for v in p):
        x1, y1, x2, y2 = p
        p = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
    return [[int(x), int(y)] for x, y in p]


def main():
    ap = argparse.ArgumentParser(description="Wrapper: image -> OCR -> (optional) ChatGPT refine, without touching original script.")
    ap.add_argument("input", type=str, help="input image path")
    ap.add_argument("--lang", type=str, default="en")
    # Visualization: call the user's original script (optional)
    ap.add_argument("--visual_out", type=str, default=None, help="optional path to save visualization using original ocr_pdf_crop.py")
    ap.add_argument("--font", type=str, default=None)
    ap.add_argument("--call_original", action="store_true", help="if set, call original ocr_pdf_crop.py to generate visualization")
    # ChatGPT options
    ap.add_argument("--use_chatgpt", action="store_true", help="send both image+OCR to ChatGPT")
    ap.add_argument("--openai_api_key", type=str, default="", help="OpenAI API key (leave empty to skip)")
    ap.add_argument("--openai_model", type=str, default="gpt-4o-mini")
    ap.add_argument("--openai_api_base", type=str, default="https://api.openai.com/v1")
    ap.add_argument("--out_csv", type=str, default=None, help="save the CSV part of the model output (if any)")
    ap.add_argument("--out_json", type=str, default=None, help="save the last-line JSON {\"corrected_texts\": [...]}")
    args = ap.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    # 1) OCR locally
    ocr = PaddleOCR(lang=args.lang, use_textline_orientation=True, device="gpu")
    results = ocr.predict(str(input_path))
    res = results[0] if isinstance(results, list) else results

    polys  = res.get("rec_polys") or res.get("dt_polys") or res.get("rec_boxes") or []
    boxes  = [to_poly4(p) for p in polys]
    txts   = res.get("rec_texts")  or [""] * len(boxes)
    scores = res.get("rec_scores") or [None] * len(boxes)
    print(f"[OCR] items: {len(boxes)}")

    # # 2) Optional visualization via original script
    # if args.visual_out:
    #     print("[VIS] drawing visualization directly (no second model load)")
    #     img = Image.open(str(input_path)).convert("RGB")
    #     vis = draw_ocr(img, boxes, txts, scores, font_path=(args.font or None))
    #     Image.fromarray(vis).save(args.visual_out)
    #     print(f"[VIS SAVED] {args.visual_out}")



    # 3) Optionally call ChatGPT
    # if args.use_chatgpt and args.openai_api_key:

    refined_json_obj = None
    csv_part = None
    if args.use_chatgpt and args.openai_api_key:
        from chatgpt_refine import encode_image_to_data_url, chatgpt_refine

        image_data_url = encode_image_to_data_url(str(input_path))
        ocr_items = [{"box": b, "text": t, "score": s} for b, t, s in zip(boxes, txts, scores)]
        try:
            refined = chatgpt_refine(
                api_key=args.openai_api_key,
                image_data_url=image_data_url,
                ocr_items=ocr_items,
                model=args.openai_model,
                api_base=args.openai_api_base,
            )
            print("[PIPELINE] using ChatGPT refined JSON:", bool(refined_json_obj))
            print("\n[ChatGPT RESULT]\n")
            print(refined)

            # Save CSV + JSON
            lines = [ln for ln in refined.strip().splitlines() if ln.strip()]
            last = lines[-1] if lines else ""
            if last.startswith("{") and last.endswith("}"):
                try:
                    refined_json_obj = json.loads(last)
                    csv_part = "\n".join(lines[:-1]).strip()
                except Exception:
                    refined_json_obj = None
                    csv_part = refined
            else:
                refined_json_obj = None
                csv_part = refined

        except Exception as e:
            print("[ChatGPT ERROR]", str(e))
    else:
        if args.use_chatgpt and not args.openai_api_key:
            print("[ChatGPT SKIPPED] openai_api_key not provided.")

    # 3.5) calcu char_agreement and merge into refined_json_obj
    def _levenshtein(a: str, b: str) -> int:
        a, b = a or "", b or ""
        la, lb = len(a), len(b)
        dp = list(range(lb + 1))
        for i in range(1, la + 1):
            prev, dp[0] = dp[0], i
            for j in range(1, lb + 1):
                cur = dp[j]
                cost = 0 if a[i - 1] == b[j - 1] else 1
                dp[j] = min(dp[j] + 1,  # deletion
                            dp[j - 1] + 1,  # insertion
                            prev + cost)  # substitution
                prev = cur
        return dp[lb]

    def _char_agreement(orig: str, corr: str) -> float:
        if not orig and not corr: return 1.0
        dist = _levenshtein(orig or "", corr or "")
        denom = max(len(orig or ""), len(corr or ""), 1)
        return round(1.0 - dist / denom, 4)

    corrected_boxes = boxes
    corrected_texts = txts
    if refined_json_obj and "items" in refined_json_obj:
        items = refined_json_obj["items"]

        for it in items:
            orig = it.get("orig") or ""
            corr = it.get("corr") or ""
            it["char_agreement"] = _char_agreement(orig, corr)
            if not it.get("box"):
                idx = it.get("index")
                if isinstance(idx, int) and 0 <= idx < len(boxes):
                    it["box"] = boxes[idx]

        corrected_texts = [txt for txt in txts]
        for it in items:
            idx = it.get("index")
            corr = it.get("corr")
            if isinstance(idx, int) and 0 <= idx < len(corrected_texts) and isinstance(corr, str):
                corrected_texts[idx] = corr

    # 3.8) draw
    if args.visual_out:
        img = Image.open(str(input_path)).convert("RGB")
        from PIL import ImageDraw, ImageFont
        import numpy as np
        vis = img.copy()
        draw = ImageDraw.Draw(vis)

        font = None
        if args.font:
            try:
                font = ImageFont.truetype(args.font, 16)
            except Exception:
                font = None


        if refined_json_obj and "items" in refined_json_obj:
            for it in refined_json_obj["items"]:
                box = it.get("box") or []
                changed = bool(it.get("changed"))
                corr = it.get("corr") or ""
                ca = it.get("char_agreement")

                color = (255, 0, 0) if changed else (0, 180, 0)
                if len(box) >= 4:

                    draw.line(box + [box[0]], width=2, fill=color)
                    label = f"{corr} (ca={ca})"
                    x = min(p[0] for p in box);
                    y = min(p[1] for p in box)
                    draw.rectangle([x, y - 18, x + 8 * len(label) + 6, y], fill=(255, 255, 255, 200))
                    draw.text((x + 3, y - 18), label, fill=(0, 0, 0), font=font)


            tables = refined_json_obj.get("tables") or []
            for tb in tables:
                cell_box_ids = tb.get("cell_box_ids") or []
                for r, row_cells in enumerate(cell_box_ids):
                    for c, idx_list in enumerate(row_cells):
                        pts = []
                        for idx in (idx_list or []):
                            if isinstance(idx, int) and 0 <= idx < len(boxes):
                                pts.extend(boxes[idx])
                        if pts:
                            xs = [p[0] for p in pts];
                            ys = [p[1] for p in pts]
                            x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
                            draw.rectangle([x1, y1, x2, y2], outline=(0, 0, 255), width=2)
        else:
            vis = Image.fromarray(draw_ocr(img, boxes, corrected_texts, scores, font_path=(args.font or None)))

        vis.save(args.visual_out)
        print(f"[VIS SAVED] {args.visual_out}")

    # 3.9) json and csv
    if args.out_csv and csv_part:
        with open(args.out_csv, "w", encoding="utf-8") as f:
            f.write(csv_part)
        print(f"[Saved CSV] {args.out_csv}")

    if args.out_json:
        export_obj = refined_json_obj or {
            "items": [
                {"index": i, "orig": o, "corr": c, "changed": (o != c), "ocr_score": s, "corr_conf": None,
                 "char_agreement": _char_agreement(o, c), "box": b}
                for i, (o, c, s, b) in enumerate(zip(txts, corrected_texts, scores, boxes))
            ],
            "tables": []
        }
        with open(args.out_json, "w", encoding="utf-8") as f:
            json.dump(export_obj, f, ensure_ascii=False, indent=2)
        print(f"[Saved JSON] {args.out_json}")

    # 4) Save raw OCR JSON
    raw_json_path = input_path.with_suffix(".raw_ocr.json")
    raw = [{"box": b, "text": t, "score": s} for b, t, s in zip(boxes, txts, scores)]
    with open(raw_json_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)
    print(f"[Saved RAW OCR] {raw_json_path}")


if __name__ == "__main__":
    main()
