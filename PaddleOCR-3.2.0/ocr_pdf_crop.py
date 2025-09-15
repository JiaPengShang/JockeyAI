import argparse
from PIL import Image
from paddleocr import PaddleOCR


def to_poly4(p):
    if hasattr(p, "tolist"):
        p = p.tolist()
    if len(p) == 4 and all(isinstance(v, (int, float)) for v in p):
        x1, y1, x2, y2 = p
        p = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
    return [[int(x), int(y)] for x, y in p]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=str)
    ap.add_argument("output", type=str)
    ap.add_argument("--lang", type=str,default="en")
    ap.add_argument("--font", type=str)
    args = ap.parse_args()

    ocr = PaddleOCR(
        lang=args.lang,
        use_textline_orientation=True,
        device="gpu"
    )


    results = ocr.predict(args.input)
    print(results)
    res = results[0] if isinstance(results, list) else results


    polys  = res.get("rec_polys") or res.get("dt_polys") or res.get("rec_boxes") or []
    boxes  = [to_poly4(p) for p in polys]
    txts   = res.get("rec_texts")  or [""] * len(boxes)
    scores = res.get("rec_scores") or None

    img = Image.open(args.input).convert("RGB")
    vis = draw_ocr(img, boxes, txts, scores, font_path=(args.font or None))
    Image.fromarray(vis).save(args.output)
    print(f"finish {len(boxes)} -per- -> {args.output}")



if __name__ == "__main__":
    main()
