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

    # 2) Optional visualization via original script
    if args.visual_out:
        print("[VIS] drawing visualization directly (no second model load)")
        img = Image.open(str(input_path)).convert("RGB")
        vis = draw_ocr(img, boxes, txts, scores, font_path=(args.font or None))
        Image.fromarray(vis).save(args.visual_out)
        print(f"[VIS SAVED] {args.visual_out}")

    # 3) Optionally call ChatGPT
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
            print("\n[ChatGPT RESULT]\n")
            print(refined)

            # Save CSV + JSON if requested.
            lines = refined.strip().splitlines()
            json_tail = None
            if lines:
                last = lines[-1].strip()
                csv_part = "\n".join(lines[:-1]).strip() if (last.startswith("{") and last.endswith("}")) else refined

                if args.out_csv and csv_part:
                    with open(args.out_csv, "w", encoding="utf-8") as f:
                        f.write(csv_part)
                    print(f"[Saved CSV] {args.out_csv}")

                if args.out_json and last.startswith("{") and last.endswith("}"):
                    with open(args.out_json, "w", encoding="utf-8") as f:
                        f.write(last)
                    print(f"[Saved JSON] {args.out_json}")

        except Exception as e:
            print("[ChatGPT ERROR]", str(e))
    else:
        if args.use_chatgpt and not args.openai_api_key:
            print("[ChatGPT SKIPPED] openai_api_key not provided.")

    # 4) Save raw OCR JSON
    raw_json_path = input_path.with_suffix(".raw_ocr.json")
    raw = [{"box": b, "text": t, "score": s} for b, t, s in zip(boxes, txts, scores)]
    with open(raw_json_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)
    print(f"[Saved RAW OCR] {raw_json_path}")


if __name__ == "__main__":
    main()
