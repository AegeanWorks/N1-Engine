# N1-Engine

<!-- aegean:media:start -->
<p align="center"><img src="assets/social-preview.png" alt="N1-Engine social preview" width="100%"></p>
<p align="center"><a href="LICENSE"><img src="https://img.shields.io/badge/license-AL--1.1-2f9e44" alt="License"></a> <a href="https://github.com/AegeanWorks/AIKit"><img src="https://img.shields.io/badge/AIKit-integrated-6f42c1" alt="AIKit Integrated"></a></p>
<!-- aegean:media:end -->


*A local-first, privacy-focused, and scientifically rigorous platform for personal N=1 experimentation.*

The **N1-Engine** is a local-first Python platform designed for rigorous N=1 self-experimentation analysis. It empowers individuals to treat their life as a laboratory, applying scientific statistical methods to personal data to determine what truly works for them.

**What it is:**
- A structured tool for logging life interventions (e.g., "Started Magnesium", "Quit Caffeine") and tracking daily metrics (e.g., "Sleep Quality", "Energy Level").
- A statistical analysis engine that compares baseline periods against intervention periods to detect significant changes.
- A cross-platform desktop application built with Python and PyQt6.
- A privacy-focused tool: All data is stored locally on your machine in a SQLite database.

**What it is NOT:**
- **Not medical advice:** This is a software tool for data analysis. It does not replace professional medical advice. Consult a doctor for health decisions.
- **Not a causal proof engine:** It identifies correlations and statistically significant shifts. However, in single-subject experiments, unmeasured confounding variables (like stress, weather, or placebo effects) can influence results.

## 2. Scientific Philosophy

This tool is built on the principles of "N=1 structured inference":
*   **Epistemic Humility:** We acknowledge the limitations of self-experimentation. Results are indicators, not absolute truths.
*   **Conservative Interpretation:** It favors caution. It flags small sample sizes, multiple comparisons, and insufficient data to prevent overconfidence.
*   **Reproducibility:** Analysis is deterministic and repeatable.
*   **Separation of Concerns:** Data entry is distinct from analysis to minimize observer bias.

-   **Privacy First:** Your data is yours. It never leaves your computer.
-   **Scientific Rigor:** The analysis goes beyond simple "before and after" comparisons, incorporating checks for data stability, effect size, and statistical significance to prevent common misinterpretations.
-   **User Empowerment:** Provides clear, understandable reports to help you make informed decisions based on your own data.
-   **Offline & Local:** No cloud, no subscriptions, no internet required.

## ⚡ 30-Second Cold-Start Quick Reference

- **Runtime Prerequisites**: Python 3.11+ with the `requirements.txt` stack (pandas, numpy, scipy, statsmodels, SQLAlchemy, PyQt6)
- **Canonical Regression Shield Gate**:
  ```bash
  python -m pytest tests
  ```

### 🛠️ AIKit Commands (run from the AIKit workspace root)
| Role | Command |
|---|---|
| Status, task and gates | `python aikit.py status N1-Engine` |
| Delivery check (clean tree + map) | `python aikit.py check N1-Engine --strict` |
| Repair memory and map, then check | `python aikit.py fix N1-Engine` |
| Resume an interrupted task | `python aikit.py resume N1-Engine` |

---

## Key Features

-   **Experiment-Centric Workspace:** Manage all your interventions in one place and perform actions (logging, analysis) in the context of a selected experiment.
-   **Metric & Event Logging:** Track both quantitative daily metrics (e.g., "Sleep Quality": 8.5) and qualitative, confounding events (e.g., "High Stress Day").
-   **Robust Statistical Analysis:**
    -   Compares baseline vs. intervention periods.
    -   Calculates effect size (Cohen's d) to show the *magnitude* of change.
    -   Provides both parametric (Welch's t-test) and non-parametric (Mann-Whitney U) p-values.
    -   Uses Bootstrap Resampling to generate robust 95% Confidence Intervals.
    -   Checks for baseline trends to ensure stability before the intervention.
-   **Built-in Scientific Safeguards:** Automatically warns you about small sample sizes, the risks of multiple comparisons, and other statistical pitfalls.
-   **Data Visualization:** Instantly plot time-series charts for any metric within an intervention.
-   **Customizable Settings:** Tune the analysis parameters to fit your needs.
-   **Full Data Portability:** Import and export all your data to CSV for backup or external analysis.

---

## Installation

**Prerequisites:**
-   Python 3.11 or higher.

**Step-by-Step Setup:**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/AegeanWorks/N1-Engine.git
    cd N1-Engine
    ```

2.  **Create and activate a virtual environment (Recommended):**
    *   **Linux/macOS:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    *   **Windows:**
        ```cmd
        python -m venv venv
        venv\Scripts\activate
        ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python run_gui.py
    ```
    The application will start, and a local database file (`main.db`) will be created automatically in the project's root directory.

---

## Comprehensive Usage Guide

The application is organized into a main **Workspace** and several global tabs.

### The Workspace

This is the central hub for all your experimental work. It is split into two parts:
1.  **Interventions Table (Top):** A master list of all your experiments.
2.  **Action Tabs (Bottom):** A set of tabs (`Metric Setup`, `Logging`, `Events`, `Analysis`) that are scoped to the intervention you select from the table above.

#### Managing Interventions

An "intervention" is any change you are making that you want to test (e.g., "Vitamin D Supplement," "Daily Meditation," "Ketogenic Diet").

-   **Add Intervention:** Click to open a dialog where you can define your experiment.
    -   **Name:** A clear, unique name for the intervention.
    -   **Start Date:** The date the intervention begins. This is the critical date that separates the "baseline" from the "intervention" period.
    -   **Projected End Date (Optional):** The date you *plan* to end the experiment. This is for planning and does not affect analysis.
    -   **Actual End Date (Optional):** The date the intervention *actually* ended.
-   **Edit Selected:** Modify the details of an existing intervention.
-   **Close Selected (End Now):** A shortcut to set the "Actual End Date" of a selected intervention to today.

#### Workspace Tabs

You must select an intervention from the top table to activate the `Logging`, `Events`, and `Analysis` tabs.

##### 1. Metric Setup
This tab is for defining *what* you will measure. It is always enabled.
-   **Add Metric:** Define a new metric with a name, description, and unit (e.g., Name: "Sleep Quality", Description: "Subjective rating from 1-10", Unit: "score").
-   **Why define metrics?** This ensures consistency. You can only log data for metrics that have been defined here, preventing typos (e.g., "Sleep" vs. "Sleep Quality").

##### 2. Logging
This is where you enter your daily quantitative data for the selected intervention.
-   Select a **Date**.
-   Choose a **Metric Name** from the dropdown (populated from `Metric Setup`).
-   Enter the numeric **Value**.
-   Click **Log Metric**.
-   The bottom half of this tab allows you to **visualize** any metric you've logged for the selected intervention.

##### 3. Events
This tab is crucial for good science. Use it to log significant, qualitative events that could act as **confounding variables**.
-   **Log Event:** Record an event with a name, date/time, severity, and notes.
-   **Example:** If your sleep quality suddenly drops, you can check here to see if it coincided with an event like "High Stress Day," "Sick," or "Traveled." This provides context that numbers alone cannot.

##### 4. Analysis
This is the core analytical engine.
1.  **Select a Metric:** Choose the outcome metric you want to analyze from the dropdown.
2.  **Set Analysis Windows:**
    -   **Baseline Days:** How many days of data *before* the intervention's start date to use as the control period.
    -   **Intervention Days:** How many days of data *after* the start date to include in the test period.
3.  **Run Analysis:** Generates a detailed statistical report.

**Understanding the Analysis Report:**

-   **Windows:** A summary of the data in each period (count, mean, standard deviation).
-   **Trend:** Shows the linear trend (slope) of the data during each window. A significant p-value (e.g., p < 0.05) in the **baseline trend** is a red flag, suggesting your metric was already changing *before* the intervention started.
-   **Mean Difference:** The simplest outcome: `(Intervention Mean) - (Baseline Mean)`.
-   **Cohen's d (Effect Size):** This measures the *magnitude* of the change, independent of sample size. It's one of the most important results.
    -   `~0.2`: Small effect (potentially unnoticeable)
    -   `~0.5`: Medium effect (noticeable)
    -   `~0.8+`: Large effect (easily noticeable)
-   **Bootstrap 95% CI:** The 95% Confidence Interval for the mean difference. This provides a range of plausible values for the true effect. **If this range does not include zero, the result is statistically significant at the p < 0.05 level.** This is often more intuitive and robust than a p-value alone. The resampler uses a fixed seed, so the same data produces the same interval.
-   **p-values:**
    -   **Welch's t-test:** A standard test to see if the means of two groups are different.
    -   **Mann-Whitney U:** A non-parametric alternative that doesn't assume the data is normally distributed. It's more reliable for small sample sizes or data that isn't bell-shaped (like subjective 1-10 scales).
    -   *Interpretation:* A p-value of `< 0.05` is conventionally considered "statistically significant," meaning there's less than a 5% probability of observing such a result if there were no real effect.
-   **Warnings:** The engine automatically flags potential issues, such as insufficient data or a high risk of false positives from testing too many metrics.

### Global Tabs

These tabs perform actions across your entire dataset.

##### Summarizer
Generate a quick summary of all metrics and events logged for a specific intervention or within a manual date range.

##### Data Management
Import and export your entire database to CSV files. This is essential for backups or for analyzing your data with other tools (e.g., R, Python notebooks).

##### Settings
Configure the default parameters used by the Analysis Engine, such as the minimum number of data points required for a warning.

---

## Troubleshooting

*   **"Analysis Failed":** The most common cause is insufficient data. Ensure you have at least 3 data points in *both* the baseline and intervention windows you've defined.
*   **"Database Locked":** This can happen if another instance of the N1-Engine is running. Ensure only one instance is open.
*   **"Import Failed":** Double-check that your CSV file's column headers and date formats match the requirements specified in the Data Management tab.

---

## Developer Guide

### 📦 What's Inside

```text
N1-Engine/
├── .aikit/                  <- AIKit project memory: config, guidelines, decisions, ledger, map
├── main/
│   ├── __init__.py          <- package marker
│   ├── config.py            <- scientific thresholds and database URL
│   ├── core/                <- business logic: statistics, ORM models, database, reporting
│   ├── gui/                 <- PyQt6 widgets, windows and dialogs
│   ├── api/                 <- reserved package (empty)
│   └── utils/               <- reserved package (empty)
├── tests/                   <- pytest regression suite
├── run_gui.py               <- application entry point
├── requirements.txt         <- declared dependencies
├── README.md
├── assets/
├── COMMERCIAL.md
├── LICENSE
├── LICENSES/                 <- REUSE license texts
├── REUSE.toml                <- Machine-readable SPDX metadata
└── .gitignore
```

### Running Tests

The project uses `pytest` for testing.

```bash
# Install pytest if you haven't already
pip install pytest

# Run all tests from the root directory
python -m pytest tests
```

## Contributing

Contributions are welcome! Please feel free to fork the repository, create a feature branch, and submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

---

## Disclaimer

The N1-Engine is a tool for informational and educational purposes only. It is **not a substitute for professional medical advice, diagnosis, or treatment**. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. Never disregard professional medical advice or delay in seeking it because of something you have read or analyzed with this tool.

<!-- aegean:brand-assets:start -->
## 🎨 Brand Assets

> **AI-Generated Brand Artwork.** The banner and logo are **AI-generated brand assets**. They are illustrative and may not literally depict every feature or the full project scope.
<!-- aegean:brand-assets:end -->

## 📜 License

Free for personal use under the Aegean License 1.1 (AL-1.1); see [LICENSE](LICENSE). Any commercial use needs the Aegean Commercial License 1.0 (ACL-1.0); see [COMMERCIAL.md](COMMERCIAL.md).

<!-- aegean:screenshots:start -->
## Screenshots

<a href="https://github.com/AegeanWorks/N1-Engine/commit/6f6a75e"><img src="assets/screenshots/2026-11-03-main.png" alt="N1-Engine workspace at 2026-11-03"></a>

*commit `6f6a75e` · 2026-11-03 · window 1016x839 · blank-database workspace via N1_DATABASE_URL (ADR-004)*
<!-- aegean:screenshots:end -->
