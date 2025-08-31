# Project Summary
This project analyzes lifestyle datasets related to food intake, sleep patterns, and work productivity. It aims to extract actionable insights through data visualization and statistical analysis, enhancing personal well-being and productivity. By leveraging data-driven insights, the project seeks to provide users with a comprehensive understanding of their lifestyle habits over a two-year period. Recent advancements include a detailed three-way analysis of the interactions between sleep, diet, and work, providing deeper insights into their correlations and effects on personal productivity.

# Project Module Description
The project consists of the following functional modules:
- **Data Loading**: Read and understand the structure and content of the provided Excel files.
- **Data Visualization**: Generate visual representations of the data to facilitate easier interpretation.
- **Exploratory Data Analysis (EDA)**: Analyze the data to identify patterns and trends.
- **Insight Generation**: Produce actionable insights based on the analysis.
- **Reporting**: Create a comprehensive report summarizing the findings and save it in the designated output directory.
- **Advanced Analysis**: Conduct in-depth analysis to explore the relationships between sleep, diet, and work, including specialized visualizations and statistical validation.

# Directory Tree
```
/workspace
├── uploads
│   ├── chong-food.xlsx
│   ├── chong-sleep.xlsx
│   └── chong-work.xlsx
├── outputs
│   ├── food_data_cleaned.csv
│   ├── sleep_data_cleaned.csv
│   ├── work_data_cleaned.csv
│   ├── correlation_analysis.csv
│   ├── comprehensive_dataset_analysis.txt
│   ├── detailed_eda_summary.txt
│   ├── visualization_summary.txt
│   ├── visualizations
│   │   ├── food_intake_analysis.png
│   │   ├── sleep_patterns_analysis.png
│   │   ├── work_productivity_analysis.png
│   │   ├── cross_dataset_analysis.png
│   │   └── comprehensive_dashboard.png
│   ├── advanced_analysis
│   │   ├── FINAL_COMPREHENSIVE_REPORT.md
│   │   ├── comprehensive_daily_metrics.csv
│   │   ├── advanced_correlation_matrix.csv
│   │   ├── cross_domain_correlations.csv
│   │   ├── hypothesis_testing_results.csv
│   │   ├── correlation_validation.csv
│   │   ├── pattern_stability_analysis.csv
│   │   ├── evidence_based_insights.csv
│   │   ├── 3d_advanced_relationships.png
│   │   ├── statistical_validation.png
│   │   ├── team_verification_checklist.csv
│   │   └── analysis_completion_summary.csv
├── code.ipynb
```
- **uploads/**: Contains the input Excel files for analysis.
- **outputs/**: Destination for the generated reports, cleaned datasets, visualizations, and analysis summaries.
- **advanced_analysis/**: Contains outputs from the advanced analysis, including reports, metrics, and visualizations.

# File Description Inventory
- **chong-food.xlsx**: Dataset related to food habits.
- **chong-sleep.xlsx**: Dataset related to sleep patterns.
- **chong-work.xlsx**: Dataset related to work activities.
- **food_data_cleaned.csv**: Restructured food intake data.
- **sleep_data_cleaned.csv**: Processed sleep metrics.
- **work_data_cleaned.csv**: Work productivity data.
- **correlation_analysis.csv**: Cross-dataset correlations.
- **FINAL_COMPREHENSIVE_REPORT.md**: Complete report of the advanced analysis.
- **comprehensive_daily_metrics.csv**: Multi-dimensional daily data.
- **advanced_correlation_matrix.csv**: Results of the advanced correlation analysis.
- **cross_domain_correlations.csv**: Inter-domain relationships identified.
- **hypothesis_testing_results.csv**: Results of statistical tests performed.
- **correlation_validation.csv**: Results comparing statistical methods.
- **pattern_stability_analysis.csv**: Analysis of temporal stability.
- **evidence_based_insights.csv**: Summary of validated insights.
- **3d_advanced_relationships.png**: Visualizations of multi-dimensional relationships.
- **statistical_validation.png**: Plots for statistical validation.
- **team_verification_checklist.csv**: Checklist for verification processes.
- **analysis_completion_summary.csv**: Summary of analysis completion metrics.

# Technology Stack
- Python: Primary programming language for data analysis.
- Pandas: Library for data manipulation and analysis.
- Matplotlib/Seaborn: Libraries for data visualization.

# Usage
1. **Install Dependencies**: Ensure that Python and the required libraries (Pandas, Matplotlib, Seaborn) are installed in your environment.
2. **Load Data**: Use the provided scripts to read the Excel files from the uploads directory.
3. **Analyze Data**: Execute the analysis functions to generate insights and visualizations.
4. **Generate Reports**: Run the reporting functions to create and save the final report in the outputs directory.
5. **Advanced Analysis**: Follow the instructions in `code.ipynb` to perform the advanced analysis and generate specialized visualizations.
