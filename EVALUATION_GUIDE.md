# Diary Extractor Accuracy Evaluation Guide

## 概述

这个评估系统帮助你比较 `diary_extractor.py` 的提取结果与原始PDF的准确率。系统支持前十页的详细评估。

## 文件说明

- `simple_evaluator.py` - 主要评估脚本
- `evaluation_template.json` - 评估模板（需要手动填写）
- `sample_evaluation.json` - 示例评估（已填写）
- `sample_evaluation_metrics.json` - 评估指标结果
- `page_1.png` 到 `page_10.png` - PDF页面图像

## 使用方法

### 步骤1：生成评估模板

```bash
python3 simple_evaluator.py --pdf JockeyDiaries230725.pdf --json JockeyDiaries230725.json --pages 10
```

这会生成：
- `evaluation_template.json` - 需要填写的评估模板
- `page_1.png` 到 `page_10.png` - PDF页面图像

### 步骤2：手动评估

1. 打开每个 `page_N.png` 文件查看PDF页面
2. 打开 `evaluation_template.json` 文件
3. 对每一页填写以下信息：
   - `manual_classification`: 正确的页面分类
   - `classification_correct`: true/false
   - `content_accuracy_rating`: 0-100的准确率评分
   - `content_accuracy_percentage`: 0-1的准确率百分比
   - `specific_issues`: 具体问题描述
   - `comments`: 其他评论

### 步骤3：计算评估结果

```bash
python3 simple_evaluator.py --calculate --output evaluation_template.json
```

## 评估指标

### 整体指标
- **分类准确率**: 页面类型分类的正确率
- **内容准确率**: 内容提取的准确率（0-100分）

### 分类别指标
- **food_diary**: 食物日记的准确率
- **riding_diary**: 骑行日记的准确率
- **sleep_diary_morning**: 睡眠日记（早晨）的准确率
- **sleep_diary_night**: 睡眠日记（夜晚）的准确率

## 示例结果

基于示例评估的 results：

```
📊 EVALUATION SUMMARY
============================================================
📄 Total pages evaluated: 10
🎯 Overall classification accuracy: 100.0%
📝 Overall content accuracy: 81.0%

📊 Category-wise breakdown:
  food_diary:
    Pages: 3
    Classification accuracy: 100.0%
    Content accuracy: 78.3%
  riding_diary:
    Pages: 3
    Classification accuracy: 100.0%
    Content accuracy: 88.3%
  sleep_diary_night:
    Pages: 2
    Classification accuracy: 100.0%
    Content accuracy: 80.0%
  sleep_diary_morning:
    Pages: 2
    Classification accuracy: 100.0%
    Content accuracy: 75.0%
```

## 评估标准

### 分类准确率
- 页面类型必须完全匹配
- 选项：`food_diary`, `riding_diary`, `sleep_diary_morning`, `sleep_diary_night`

### 内容准确率评分
- **90-100分**: 完美提取，所有信息准确
- **80-89分**: 很好，少量小错误
- **70-79分**: 良好，有一些错误但主要信息正确
- **60-69分**: 一般，有较多错误
- **0-59分**: 较差，大量错误或缺失信息

## 常见问题

### Q: 如何判断页面分类是否正确？
A: 查看PDF页面内容：
- 包含食物列表和日期 → `food_diary`
- 包含马匹骑行数据 → `riding_diary`
- 包含睡眠时间、质量等 → `sleep_diary_morning`
- 包含睡前活动、咖啡因等 → `sleep_diary_night`

### Q: 如何评估内容准确率？
A: 比较提取的内容与PDF实际内容：
- 姓名、日期是否正确
- 食物名称是否准确
- 数字数据是否正确
- 分类字段是否匹配

### Q: 可以评估更多页面吗？
A: 可以，修改 `--pages` 参数：
```bash
python3 simple_evaluator.py --pages 20  # 评估前20页
```

## 输出文件

- `evaluation_template.json` - 评估模板
- `evaluation_template_metrics.json` - 评估指标
- `page_N.png` - PDF页面图像
- `sample_evaluation.json` - 示例评估
- `sample_evaluation_metrics.json` - 示例指标

## 注意事项

1. 确保PDF和JSON文件存在
2. 评估需要手动进行，确保准确性
3. 建议先查看示例评估了解格式
4. 评估结果会保存到JSON文件中
