## Diary Extraction Evaluation

This guide explains how to evaluate the output of `diary_extractor.py` against a ground-truth JSON file.

### 1) Prediction JSON
Run the extractor on your PDF to produce a prediction file:

```bash
python diary_extractor.py JockeyDiaries230725.pdf --out JockeyDiaries230725_pred.json --dpi 200 --lang zh
```

This produces a JSON with the following structure:

```json
{
  "source_pdf": "JockeyDiaries230725.pdf",
  "page_count": 10,
  "entries": [
    {
      "date": "2024-07-25",
      "time": "08:00",
      "meal_type": "breakfast",
      "items": [{ "name": "oatmeal", "quantity": "1", "unit": "bowl" }],
      "notes": null
    }
  ],
  "pages": [
    { "page": 1, "raw_text": "...", "structured": { "entries": [ ... ] } }
  ]
}
```

### 2) Ground-Truth JSON
Prepare a ground-truth JSON that contains at least `entries` with the same schema as above. Only the `entries` array is used by the evaluator.

Minimal example:

```json
{
  "entries": [
    {
      "date": "2024-07-25",
      "time": "08:00",
      "meal_type": "breakfast",
      "items": [
        { "name": "oatmeal", "quantity": "1", "unit": "bowl" },
        { "name": "banana", "quantity": "1", "unit": "pc" }
      ],
      "notes": null
    }
  ]
}
```

Notes:
- `date` should be `YYYY-MM-DD`.
- `meal_type` one of: `breakfast`, `lunch`, `dinner`, `snack`, `other`. Chinese variants like `早餐/午餐/晚餐/加餐` are normalized automatically.
- Item names are matched by exact normalized name for metrics. Consider standardizing names (e.g., lowercase, singular) in ground truth.

### 3) Run Evaluator

```bash
python evaluation.py --pred JockeyDiaries230725_pred.json --gt JockeyDiaries230725_gt.json --pretty
```

### 4) Metrics Reported

- **entries.precision / recall / f1**: Match on `(date, meal_type)` pairs.
- **fields.date_accuracy / time_accuracy / meal_type_accuracy**: Accuracy over matched entries.
- **items.precision / recall / f1**: Item-level matching by `name` within matched entries.
- **items.quantity_accuracy_on_matched_names / unit_accuracy_on_matched_names**: Correctness of `quantity` and `unit` where names matched.
- Also shows counts and lists of missing/extra entry keys to aid debugging.

### 5) Tips

- If OCR produces variants of names (e.g., `oat meal` vs `oatmeal`), consider adding a normalization step to the ground truth or enhancing `evaluation.py` to use fuzzy matching.
- For partial-day PDFs, ensure your ground truth only includes entries present in the evaluated pages.
- You can aggregate multiple PDFs by concatenating their `entries` into one ground-truth file and evaluating file-by-file.


