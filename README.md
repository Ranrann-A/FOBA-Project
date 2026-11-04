# 2025 New York HMDA Lending Analytics

An interactive **two-tab Streamlit dashboard** using the group's cleaned 2025 New York
HMDA extract for JPMorgan Chase Bank, N.A. and the **actual saved model results** from
the group's executed Google Colab notebook.

## Dashboard contents

**Lending Overview**
- 5 KPIs: Processed Applications, Credit Decisions, Originated Loans, Denial Rate,
  and Median Loan Amount.
- 5 charts: Transaction Outcomes, Loan Purpose Distribution, Primary Denial Reasons,
  Observed Denial Rate by DTI, and Observed Denial Rate by Race.
- 3 **working filters**, located in the sidebar: County, Loan Purpose, and Loan Type.
  You can select multiple items in each filter. An empty filter means **All**.
- Charts show readable labels, hover details, brief interpretation notes, and an
  expandable section with the exact data tables.

**Predictive Analysis**
- Fixed held-out test results saved from Google Colab for a majority-class baseline,
  Logistic Regression, and Random Forest.
- Comparison table and chart, selectable confusion matrix, training vs test performance,
  three-fold training cross-validation, and Random Forest permutation importance.
- A ZIP download containing the four underlying predictive-results CSV files.

**Important:** The sidebar filters only affect *Lending Overview*. The model-comparison
tab is intentionally fixed because it reports **one historical held-out test evaluation**.
Changing a county filter does not retrain or reevaluate the models.

## Data and denominator rules

| Statistic | Records counted |
| --- | --- |
| Total reported HMDA transactions | Actions 1–6 |
| Processed applications | Actions 1–5 |
| Credit decisions | Actions 1–3 |
| Originated loans | Action 1 |
| Denials | Action 3 |
| Purchased loans | Action 6, **not** counted as decisions |
| Denial rate | Denials ÷ decisions (only actions 1–3) |
| Median loan amount | All currently filtered transactions, **including purchases** |
| Race comparison | Derived race categories with at least 30 filtered decisions, excluding Joint and Race Not Available |

The data represents **transactions, not necessarily distinct people or borrowers**.
When a filter reduces a race group below 30 decisions, the chart suppresses it.
Unadjusted observed differences do **not** prove causation or discrimination.

The displayed DTI chart groups exact HMDA DTI categories of 36–39, 40–44,
and 45–49 for readability. The 50%–60% and above-60% groups are kept separate.

With no filters, expected core numbers are:
- 24,722 total HMDA records
- 14,735 processed applications
- 11,168 credit decisions
- 9,163 originations
- 1,717 denials; denial rate 15.37%
- $295K median loan amount across all 24,722 transactions

## Folder structure

```text
HMDA_Streamlit_Dashboard/
├── app.py
├── charts.py
├── data_logic.py
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml
├── data/
│   └── HMDA_NY_2025_Cleaned.csv
└── results/
    ├── HMDA_Predictive_Model_Comparison.csv
    ├── HMDA_Predictive_Confusion_Matrices.csv
    ├── HMDA_Predictive_Cross_Validation.csv
    └── HMDA_Predictive_Feature_Importance.csv
```

## Run locally

1. Unzip the project into a directory.
2. Open a terminal **in the directory containing `app.py`**.
3. Use **Python 3.12** for this pinned environment. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the app:
   ```bash
   streamlit run app.py
   ```
5. Streamlit prints a local URL, normally `http://localhost:8501`.

You do **not** need to train a model to run the dashboard. The historical
evaluation results are already in the `results/` folder.

## Publish on Streamlit Community Cloud

1. Create a GitHub repository and upload **the unzipped project files**, preserving
   the folders `data/`, `results/`, and `.streamlit/`.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/), connect GitHub,
   and create an app from that repository.
3. Set the main app file path to `app.py` and select **Python 3.12** in the deployment's advanced settings.
   This set of pinned versions is intended for Python 3.12, not Python 3.14.
4. Deploy and test the public URL in a private/incognito browser window.
5. Check that all three filters work, the figures update correctly, and the
   Predictive Analysis tab still shows the same model evaluation metrics.

A live `*.streamlit.app` URL is generated **after deployment**. This ZIP does not
create a live site by itself. Current free-hosting limits and sleep policies
are subject to change.

## Presentation guide

- Begin with the five KPIs and explain that **purchased loans are not credit decisions**.
- Demonstrate County, Loan Purpose, and Loan Type filters to show how the
  descriptive charts and metrics update together.
- Show the separate denominators for denial rate and denial reasons.
- Explain why the median loan amount includes purchased loans in this dashboard.
- On Predictive Analysis, compare Random Forest vs Logistic Regression, discuss
  missed denials, and note possible Random Forest overfitting.
- Emphasize that prediction scores are **historical test results**, not actual
  mortgage approvals and not causal explanations.

## Limitations

The dashboard describes one lender, one state, and one reporting year.
The public HMDA records do not include credit scores and other underwriting
information. Models may learn historical underwriting patterns and their
limitations. They must not be used to decide whether any individual receives
a loan, and demographic differences are purely descriptive.


## Stabilizing an existing Community Cloud deployment

If you previously deployed with a different Python version (for example, 3.14)
and broad dependency ranges, **do not update only `requirements.txt` and leave
Python on 3.14**: the exact `numpy`/`pyarrow` versions above were chosen for
Python 3.12.

1. In GitHub, replace the root-level `app.py` and `requirements.txt` files.
   `charts.py`, `data_logic.py`, the cleaned CSV, and all model-results CSVs stay unchanged.
2. On Streamlit Community Cloud, check the deployed app's Python runtime.
   Select **Python 3.12** if the app settings provide that control. Some existing
   deployments require redeployment to change the Python version. If so, deploy
   from the same GitHub repo/branch with Python 3.12; the new app's URL might differ.
3. Reboot or redeploy, then check the newest Cloud logs show the pinned packages,
   not `streamlit==1.66.1` or `plotly==6.9.0`.
4. Open the app in an incognito window and verify both tabs. The native Streamlit
   headings, notes, and KPI cards avoid raw `<div>` text if HTML handling changes.

### If Plotly fails to load again

A browser error mentioning `PlotlyChart...js` is a **frontend asset failure**.
It is not proof that HMDA data calculations failed. Capture the app's exact URL,
current Python and Streamlit versions from the matching Cloud logs, and the
browser Console/Network error. If the problem continues even on the pinned
Python 3.12 deployment, it may be a Streamlit Cloud/browser asset delivery problem
that needs to be reported to Streamlit, not an error in the mortgage analysis.

**Scope of this patch:** Deployment stability and text presentation only.
The underlying descriptive counts, filters, chart calculations, and saved
predictive-model results have not been modified.
