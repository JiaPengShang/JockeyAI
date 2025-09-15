import argparse
import base64
import json
import requests
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


def encode_image_to_data_url(path):
    with Image.open(path) as im:
        im = im.convert("RGB")
        from io import BytesIO
        buf = BytesIO()
        im.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{b64}"


def chatgpt_refine(
    api_key: str,
    image_data_url: str,
    ocr_items: list,
    model: str = "gpt-5",
    api_base: str = "https://api.openai.com/v1",
    system_tip: str = None
):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    ocr_payload = [
        {
            "box": item.get("box"),
            "text": item.get("text", ""),
            "score": item.get("score"),
        }
        for item in ocr_items
    ]

    sys_msg = system_tip or (
        "你是一个OCR后处理助手。现在你会同时看到原始图片和OCR结果（含坐标）。"
        "请你：1) 合理纠错不确定文本；2) 在可能时恢复表格结构；3) 输出尽量干净的结果。"
        "输出规范：\n"
        "- 若识别到表格，请先给出简洁CSV（仅一个表，不要加解释性文字）。\n"
        "- 若无表格，则输出纠正后的纯文本（不加前后缀）。\n"
        "- 另外，请在最后一行以JSON单独给出：{\"corrected_texts\":[...]}，"
        "数组元素按OCR输入顺序给出模型修订后的每段文本。"
    )

    user_msgs = [
        {
            "type": "text",
            "text": (
                    "Result:：\n"
                    + json.dumps(ocr_payload, ensure_ascii=False)
            ),
        },
        {
            "type": "image_url",
            "image_url": {"url": image_data_url},
        },
    ]

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msgs},
        ]
    }

    resp = requests.post(f"{api_base}/chat/completions", headers=headers, data=json.dumps(payload))
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=str)
    ap.add_argument("output", type=str)
    ap.add_argument("--lang", type=str, default="en")
    ap.add_argument("--font", type=str)
    # --- ChatGPT ---
    ap.add_argument("--use_chatgpt", action="store_true")
    ap.add_argument("--openai_api_key", type=str, default="")
    ap.add_argument("--openai_model", type=str, default="gpt-5")
    ap.add_argument("--openai_api_base", type=str)
    ap.add_argument("--out_csv", type=str, default=None)
    ap.add_argument("--out_json", type=str, default=None)
    args = ap.parse_args()

    # 1) OCR
    ocr = PaddleOCR(lang=args.lang, use_textline_orientation=True, device="gpu")
    results = ocr.predict(args.input)
    res = results[0] if isinstance(results, list) else results

    polys  = res.get("rec_polys") or res.get("dt_polys") or res.get("rec_boxes") or []
    boxes  = [to_poly4(p) for p in polys]
    txts   = res.get("rec_texts")  or [""] * len(boxes)
    scores = res.get("rec_scores") or [None] * len(boxes)

    # 2) Visualization
    img = Image.open(args.input).convert("RGB")
    vis = draw_ocr(img, boxes, txts, scores, font_path=(args.font or None))
    Image.fromarray(vis).save(args.output)
    print(f"[OCR] {len(boxes)} items -> {args.output}")

    # 3) chatgpt
    if args.use_chatgpt and args.openai_api_key:
        image_data_url = encode_image_to_data_url(args.input)
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

            # 4) format output
            lines = refined.strip().splitlines()
            json_tail = None
            if lines:
                last = lines[-1].strip()
                if last.startswith("{") and last.endswith("}"):
                    json_tail = last
                    csv_part = "\n".join(lines[:-1]).strip()
                else:
                    csv_part = refined

                if args.out_csv and csv_part:
                    with open(args.out_csv, "w", encoding="utf-8") as f:
                        f.write(csv_part)
                    print(f"[Saved CSV] {args.out_csv}")

                if args.out_json and json_tail:
                    with open(args.out_json, "w", encoding="utf-8") as f:
                        f.write(json_tail)
                    print(f"[Saved JSON] {args.out_json}")

        except requests.HTTPError as e:
            print("[ChatGPT ERROR]", e.response.text if e.response is not None else str(e))
        except Exception as e:
            print("[ChatGPT ERROR]", str(e))
    else:
        if args.use_chatgpt and not args.openai_api_key:
            print("[ChatGPT SKIPPED] API KEY NOT FOUND")


if __name__ == "__main__":
    main()
