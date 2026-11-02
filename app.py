"""2025 New York HMDA lending dashboard.

Start with: streamlit run app.py
Built from the group's cleaned 2025 HMDA CSV and saved Google Colab model evaluations.
"""
from pathlib import Path
import html
import io
import zipfile

import pandas as pd
import streamlit as st

from data_logic import (
    COUNTIES_NY, LOAN_TYPES, prepare_data, apply_filters, populations,
    summary, outcome_table, purpose_table, reason_table, dti_table,
    race_table, validate_model_files
)
from charts import (
    NAVY, TEAL, ORANGE, OUTCOME_COLORS, outcome_stacked_chart, race_dot_chart,
    horizontal_counts, purpose_chart, rate_chart,
    metrics_comparison_chart, confusion_chart, importance_chart,
)

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "HMDA_NY_2025_Cleaned.csv"
RESULTS = ROOT / "results"

st.set_page_config(
    page_title="2025 New York HMDA | Lending Analytics",
    page_icon="🏦", layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
:root { --ink:#18344F; --muted:#62758B; --teal:#177E88; --line:#E5EBF1; --soft:#F4F8FA; }
html, body, [class*="css"], [data-testid="stApp"] {
  font-family: "Arial", "Helvetica Neue", sans-serif;
}
[data-testid="stAppViewContainer"] { background-color:#F7F9FC; }
[data-testid="stHeader"] { background-color:transparent; }
[data-testid="stSidebar"] { background:#EEF4F8; }
.block-container { max-width:1450px; padding-top:1.65rem; padding-bottom:2.4rem; }
h1, h2, h3, h4, p, div, label, span {
  overflow-wrap:break-word;
}
h1, h2, h3 { color:var(--ink); letter-spacing:-.012em; }
h1 { font-size:clamp(1.65rem,2.7vw,2.4rem) !important; line-height:1.2 !important; }
h2 { font-size:1.35rem !important; line-height:1.3 !important; }
p { line-height:1.55; }
[data-testid="stMarkdownContainer"] p { overflow-wrap:anywhere; }
[data-testid="stVerticalBlockBorderWrapper"] {
  border-color:#E0E8EF !important;
  border-radius:16px !important;
  background:#FFFFFF;
  box-shadow:0 2px 14px rgba(24,52,79,.025);
}
[data-testid="stTabs"] [data-baseweb="tab"] {
  font-weight:700; font-size:1.02rem; white-space:normal; height:auto;
  padding:11px 16px; min-height:44px;
}
[data-testid="stPlotlyChart"] { max-width:100% !important; }
div[data-testid="stMetric"] { background:#FFFFFF; }
.header-eyebrow { color:#137783;font-size:.78rem;font-weight:800;letter-spacing:.115em;text-transform:uppercase; }
.intro { color:#5A6D83; max-width:980px; line-height:1.55; font-size:1rem; margin-top:4px; margin-bottom:10px; }
.metric-grid {
  display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:12px; margin:13px 0 15px;
}
.metric-card {
  background:#FFFFFF;border:1px solid #DFE7EE;border-radius:16px;
  padding:18px 15px 15px; min-width:0; min-height:138px;
  border-top:4px solid #1B8290;
  box-shadow:0 2px 14px rgba(24,52,79,.035);
}
.metric-label { font-size:.79rem; font-weight:700; line-height:1.3; color:#526980; 
  white-space:normal;overflow-wrap:anywhere;min-height:2.15em; }
.metric-value {font-size:clamp(1.27rem,2vw,1.94rem);font-weight:800;color:#18344F;
  line-height:1.2;letter-spacing:-.025em;white-space:normal;overflow-wrap:anywhere;margin:9px 0;}
.metric-foot {font-size:.74rem;line-height:1.35;color:#66798D;white-space:normal;overflow-wrap:anywhere;}
.section-kicker {font-size:.81rem;letter-spacing:.1em;text-transform:uppercase;
  color:#167F88;font-weight:800;margin-top:18px;margin-bottom:8px;}
.chart-heading {font-size:1.06rem;line-height:1.35;font-weight:800;
  color:#193852;margin-bottom:2px; overflow-wrap:anywhere;}
.chart-caption {font-size:.83rem;color:#60738A;line-height:1.45;margin-bottom:7px;}

.outcome-grid {
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:8px 12px;
  margin:0 0 13px;
}
.outcome-entry {
  display:flex;
  align-items:flex-start;
  gap:8px;
  background:#F8FBFD;
  border:1px solid #E7EDF3;
  border-radius:9px;
  padding:9px 10px;
  min-width:0;
}
.outcome-swatch {
  width:10px;height:10px;flex:0 0 10px;
  border-radius:3px;margin-top:4px;
}
.outcome-details {min-width:0;flex:1;}
.outcome-title {
  font-size:.78rem;line-height:1.35;font-weight:700;color:#28425A;
  overflow-wrap:break-word;
}
.outcome-stats {font-size:.73rem;line-height:1.45;color:#647A8F;overflow-wrap:break-word;}
@media (max-width:450px) {.outcome-grid{grid-template-columns:repeat(1,minmax(0,1fr));}}
.takeaway {background:#F0F6F8;border-left:3px solid #1D8590;border-radius:0 9px 9px 0;
  padding:11px 13px;color:#38546D;font-size:.86rem;line-height:1.55;
  white-space:normal;overflow-wrap:anywhere;}
.soft-note {font-size:.86rem;line-height:1.56;color:#60758B;margin:8px 0 12px;overflow-wrap:anywhere;}
.footer {margin-top:22px;padding-top:17px;border-top:1px solid #DCE5EC;color:#697C8F;
  font-size:.83rem;line-height:1.55;}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {color:#18344F;}
.table-scroll {overflow-x:auto;max-width:100%;border:1px solid #DEE7EF;border-radius:12px;
  background:white;margin:.55rem 0 .65rem;}
.clean-table {border-collapse:collapse;width:100%;min-width:660px;font-size:.85rem;color:#233A51;}
.clean-table th {background:#EAF2F6;color:#24435B;font-weight:800;text-align:left;
  padding:13px 12px;line-height:1.4;white-space:normal;overflow-wrap:anywhere;}
.clean-table td {padding:12px;border-top:1px solid #EDF1F5;line-height:1.4;
  white-space:normal;overflow-wrap:anywhere;}
.clean-table tr:nth-child(even) td {background:#F8FBFD;}
.clean-table td:first-child {font-weight:700;min-width:135px;}
.clean-table td:not(:first-child) {white-space:nowrap;}
@media (max-width:1100px) {.metric-grid{grid-template-columns:repeat(3,minmax(0,1fr));}}
@media (max-width:700px) {
 .metric-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;}
 .metric-card{padding:13px 11px;min-height:119px;}
 .metric-value{font-size:1.4rem;}
 .block-container {padding-left:.8rem;padding-right:.8rem;}
}
@media (max-width:420px) {.metric-grid{grid-template-columns:repeat(1,minmax(0,1fr));}}
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_data(path: str):
    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    return prepare_data(df)

@st.cache_data(show_spinner=False)
def load_model_results(folder: str):
    folder=Path(folder)
    comp=pd.read_csv(folder/"HMDA_Predictive_Model_Comparison.csv")
    cm=pd.read_csv(folder/"HMDA_Predictive_Confusion_Matrices.csv")
    cv=pd.read_csv(folder/"HMDA_Predictive_Cross_Validation.csv")
    feature=pd.read_csv(folder/"HMDA_Predictive_Feature_Importance.csv")
    validate_model_files(comp,cm)
    return comp,cm,cv,feature

@st.cache_data(show_spinner=False)
def results_zip(folder: str):
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(Path(folder).glob("*.csv")):
            z.write(p,arcname=p.name)
    return b.getvalue()

def pretty_int(x): return f"{x:,}"
def pretty_pct(x): return f"{x*100:.2f}%" if x is not None else "N/A"
def pretty_amount(x): return f"${x/1000:,.0f}K" if x is not None else "N/A"

def metric_html(label, value, foot):
    esc=lambda s:html.escape(str(s))
    return f"""<div class="metric-card">
    <div class="metric-label">{esc(label)}</div>
    <div class="metric-value">{esc(value)}</div>
    <div class="metric-foot">{esc(foot)}</div></div>"""

def chart_header(title, description):
    st.markdown(f'<div class="chart-heading">{html.escape(title)}</div><div class="chart-caption">{html.escape(description)}</div>',unsafe_allow_html=True)


def outcome_breakdown(table):
    """Readable legend for the stacked chart, including both count and percentage."""
    items = []
    for row in table.itertuples(index=False):
        label = html.escape(str(row.Outcome))
        color = OUTCOME_COLORS.get(str(row.Outcome), "#91A2B5")
        items.append(
            '<div class="outcome-entry">'
            f'<span class="outcome-swatch" style="background:{color}"></span>'
            '<div class="outcome-details">'
            f'<div class="outcome-title">{label}</div>'
            f'<div class="outcome-stats">{int(row.Count):,} records · {float(row.Share):.1%}</div>'
            '</div></div>'
        )
    return '<div class="outcome-grid">' + "".join(items) + '</div>'

def takeaway(message):
    st.markdown(f'<div class="takeaway">{html.escape(message)}</div>',unsafe_allow_html=True)

def show_plot(fig,key):
    st.plotly_chart(fig,use_container_width=True,theme=None,
                    config={"displayModeBar":False,"responsive":True},key=key)

def show_table(t, percent=None):
    out=t.copy()
    if percent:
        for c in percent:
            if c in out:
                out[c]=out[c].map(lambda x:f"{x:.1%}")
    st.dataframe(out,hide_index=True,use_container_width=True)

def readable_table(t):
    # Unlike a compact interactive grid, this table wraps headers and model names.
    # Smaller screens can scroll the table horizontally without losing text.
    def esc(x): return html.escape(str(x))
    heads="".join(f"<th scope='col'>{esc(c)}</th>" for c in t.columns)
    rows="".join("<tr>"+"".join(f"<td>{esc(v)}</td>" for v in values)+"</tr>"
                 for values in t.itertuples(index=False,name=None))
    st.markdown(
        f'<div class="table-scroll" role="region" aria-label="Model results table" tabindex="0">'
        f'<table class="clean-table"><thead><tr>{heads}</tr></thead><tbody>{rows}</tbody></table></div>',
        unsafe_allow_html=True
    )

if not DATA.is_file():
    st.error("The cleaned HMDA CSV is missing from the data/ folder.")
    st.stop()
try:
    base=load_data(str(DATA))
    comp,cm,cv,importance=load_model_results(str(RESULTS))
except Exception as exc:
    st.error(f"Could not load the project data: {exc}")
    st.stop()

st.markdown('<div class="header-eyebrow">FOUNDATIONS OF BUSINESS ANALYTICS · 2025 HMDA</div>',unsafe_allow_html=True)
st.title("New York Mortgage Lending Analytics")
st.markdown('<div class="intro">JPMorgan Chase Bank, N.A. · New York State · 2025 reportable HMDA transactions. Explore lending activity and observed credit outcomes, then review how two models classify historical decisions.</div>',unsafe_allow_html=True)

# Sidebar selections: empty selection explicitly means no restriction.
st.sidebar.header("Explore the lending data")
st.sidebar.caption("Filters update the five KPIs and all five descriptive charts. Leave a selection empty to show all categories.")

county_codes=sorted(base["county_code"].dropna().unique().tolist(),key=lambda code:COUNTIES_NY.get(code,code))
purpose_options=sorted(base["loan_purpose_display"].dropna().unique().tolist())
loan_type_options=sorted(base["loan_type"].dropna().unique().tolist(),
                          key=lambda code: LOAN_TYPES.get(code,code))

def clear_filters():
    st.session_state["filter_county"]=[]
    st.session_state["filter_purpose"]=[]
    st.session_state["filter_loan_type"]=[]

counties=st.sidebar.multiselect(
    "County",options=county_codes,
    format_func=lambda x:COUNTIES_NY.get(x,f"County {x}"),
    key="filter_county",placeholder="All 62 counties",
    help="Choose one or more counties. An empty selection includes all counties."
)
purposes=st.sidebar.multiselect(
    "Loan purpose", options=purpose_options, key="filter_purpose",
    placeholder="All loan purposes",
    help="The purpose filter also applies to purchased loans in the full transaction-outcome chart."
)
loan_types=st.sidebar.multiselect(
    "Loan type",options=loan_type_options,
    format_func=lambda x:LOAN_TYPES.get(x,f"Loan type {x}"),
    key="filter_loan_type",placeholder="All loan types"
)
st.sidebar.button("Reset all filters",use_container_width=True,on_click=clear_filters)
filtered=apply_filters(base,counties,purposes,loan_types)
s=summary(filtered)
st.sidebar.divider()
st.sidebar.caption(f"**{s['records']:,}** of **{len(base):,}** total HMDA records currently shown.")
st.sidebar.caption("**Important:** Purchased loans are excluded from credit-decision metrics. Filter selections do not change the saved predictive model results.")

tab_overview,tab_predict=st.tabs(["Lending Overview","Predictive Analysis"])

with tab_overview:
    st.markdown('<div class="section-kicker">Key performance indicators</div>',unsafe_allow_html=True)
    cards=[
        ("Processed Applications",pretty_int(s["processed"]),"Action codes 1–5"),
        ("Credit Decisions",pretty_int(s["decisions"]),"Approvals + denials · actions 1–3"),
        ("Originated Loans",pretty_int(s["originated"]),"Completed originations · action 1"),
        ("Denial Rate",pretty_pct(s["denial_rate"]),"Denied ÷ credit decisions"),
        ("Median Loan Amount",pretty_amount(s["median_loan"]),"All filtered records, incl. purchases"),
    ]
    st.markdown('<div class="metric-grid">'+"".join(metric_html(*c) for c in cards)+'</div>',unsafe_allow_html=True)
    st.markdown(
        '<div class="soft-note">Counts and percentages use different HMDA populations when appropriate. '
        'The median loan amount describes all currently filtered transactions, including purchased loans. '
        'This is why it is $295K with no filters, rather than the processed-applications median.</div>',
        unsafe_allow_html=True)

    if filtered.empty:
        st.info("No transactions match these filters. Select a different county, loan purpose, or loan type.")
    else:
        processed,decisions,denied,originated=populations(filtered)
        st.markdown('<div class="section-kicker">Lending activity and outcomes</div>',unsafe_allow_html=True)
        c1,c2=st.columns(2,gap="medium")
        with c1:
            with st.container(border=True):
                chart_header("Transaction Outcome Distribution","All filtered HMDA transactions · 100% stacked share of reported outcomes")
                t=outcome_table(filtered)
                show_plot(outcome_stacked_chart(t),key="outcomes")
                st.markdown(outcome_breakdown(t),unsafe_allow_html=True)
                takeaway(f"{s['purchased']:,} of the selected records were purchased loans. They contribute to the activity total but were not approved or denied by this reporting institution, so excluding them from decision rates prevents misleading comparisons.")
        with c2:
            with st.container(border=True):
                chart_header("Loan Purpose Distribution","Institution-processed applications only · share of processed applications")
                t_p=purpose_table(processed)
                if t_p.empty:
                    st.info("No institution-processed applications match these filters.")
                else:
                    show_plot(purpose_chart(t_p),key="purpose")
                    top=t_p.iloc[0]
                    takeaway(f"{top['Purpose']} makes up {top['Share']:.1%} of institution-processed applications in this selection. This identifies the main source of application activity for lending operations to monitor.")

        st.markdown('<div class="section-kicker">Denial patterns</div>',unsafe_allow_html=True)
        c3,c4=st.columns(2,gap="medium")
        with c3:
            with st.container(border=True):
                chart_header("Primary Reasons for Denial","Denied applications only · reported first denial reason")
                t_r=reason_table(denied)
                if t_r.empty:
                    st.info("No denied applications match these filters.")
                else:
                    show_plot(horizontal_counts(t_r,"Reason",height=435,max_ticks=21),key="reasons")
                    top_reason=t_r.iloc[0]
                    takeaway(f"{top_reason['Reason']} leads the reported primary reasons ({top_reason['Share']:.1%} of denied applications here). This can help managers prioritize which reported denial patterns to review; it does not prove that one factor independently caused the decision.")

        with c4:
            with st.container(border=True):
                chart_header("Observed Denial Rate by DTI","Credit decisions only · denials divided by decisions within each reported DTI group")
                t_d=dti_table(decisions)
                if t_d.empty:
                    st.info("No credit decisions match these filters.")
                else:
                    show_plot(rate_chart(t_d,"DTI",overall=s["denial_rate"],height=435),key="dti")
                    high_dti=t_d[t_d.DTI.isin(["50%-60%",">60%"])]
                    if not high_dti.empty:
                        h=high_dti.sort_values("Rate",ascending=False).iloc[0]
                        dti_takeaway=(f"The {h['DTI']} group has an observed denial rate of {h['Rate']:.1%} "
                                      f"across {int(h['Decisions']):,} decisions. "
                                      "This highlights a high-denial segment for closer review, not a causal relationship. ")
                    else:
                        dti_takeaway="Compare category rates to see where observed denials are concentrated. "
                    takeaway(dti_takeaway+
                        f"The dotted line is the overall filtered rate ({pretty_pct(s['denial_rate'])}); "
                        "36–49% exact DTI values are grouped for readability.")

        st.markdown('<div class="section-kicker">Applicant outcomes</div>',unsafe_allow_html=True)
        with st.container(border=True):
            chart_header("Observed Denial Rate by Race","Dot plot · reported race groups with at least 30 filtered credit decisions")
            t_race=race_table(decisions,min_n=30)
            if t_race.empty:
                st.info("No individual reported race category has at least 30 credit decisions with these filters. Broaden the filters to display this comparison.")
            else:
                show_plot(race_dot_chart(t_race,overall=s["denial_rate"]),key="race")
                high=t_race.sort_values("Rate",ascending=False).iloc[0]
                race_takeaway=(f"The highest displayed observed rate is {high['Rate']:.1%} "
                               f"for {high['Race']} ({int(high['Decisions']):,} decisions). "
                               "These comparisons may guide further descriptive review, but are unadjusted and do not prove discrimination or causation. "
                               "Joint, unavailable, and groups under 30 decisions are not displayed. "
                               "The dotted line shows the overall filtered rate.")
                takeaway(race_takeaway)
        with st.expander("View the exact numbers behind the five charts"):
            st.markdown("**Transaction outcomes**")
            show_table(outcome_table(filtered),percent=["Share"])
            st.markdown("**Loan purpose**")
            show_table(purpose_table(processed),percent=["Share"])
            st.markdown("**Primary denial reasons**")
            show_table(reason_table(denied),percent=["Share"])
            st.markdown("**Debt-to-income groups**")
            show_table(dti_table(decisions),percent=["Rate"])
            st.markdown("**Race groups (at least 30 decisions)**")
            show_table(race_table(decisions),percent=["Rate"])
    st.markdown('<div class="soft-note">**Interpretation:** This dashboard describes 2025 HMDA reporting for one lender in one state. It does not control for every underwriting factor, establish causation, or indicate whether an individual mortgage applicant should be approved.</div>',unsafe_allow_html=True)

with tab_predict:
    st.markdown('<div class="section-kicker">Historical predictive classification</div>',unsafe_allow_html=True)
    st.markdown("### How well did the models distinguish approved and denied decisions?")
    st.write(
        "The models were trained and evaluated in Google Colab using **11,168 historical credit decisions**. "
        "A stratified 80/20 split produced **8,934 training records** and **2,234 held-out test records**. "
        "The majority-class baseline, Logistic Regression, and Random Forest were compared using several metrics."
    )
    st.info(
        "**These are fixed held-out test results from the group's Colab run.** "
        "County, loan-purpose, and loan-type filters on the left affect only Lending Overview, "
        "not the model-evaluation tables or charts on this tab."
    )

    st.markdown('<div class="section-kicker">Model evaluation</div>',unsafe_allow_html=True)
    model_show=comp[["Model","Accuracy","Denial Precision","Denial Recall","Denial F1","ROC-AUC","Average Precision"]].copy()
    for col in ["Accuracy","Denial Precision","Denial Recall"]:
        model_show[col]=model_show[col].map(lambda x:f"{x:.1%}")
    for col in ["Denial F1","ROC-AUC","Average Precision"]:
        model_show[col]=model_show[col].map(lambda x:f"{x:.3f}")
    readable_table(model_show)
    st.caption("Denial is the positive class. The baseline predicts every record as approved, so it has high accuracy but identifies no denials.")
    c5,c6=st.columns([1.3,1],gap="medium")
    with c5:
        with st.container(border=True):
            chart_header("Test-set Performance","Precision, recall, F1, and ROC-AUC · higher is better")
            show_plot(metrics_comparison_chart(comp),key="model_performance")
    with c6:
        with st.container(border=True):
            chart_header("What the scores mean","Focus on finding denials without over-flagging approvals")
            st.markdown(
                "**Precision**: Of the records predicted as denied, how many were actually denied?\n\n"
                "**Recall**: Of all actual denials, how many did the model find?\n\n"
                "**F1-score**: A balance of precision and recall.\n\n"
                "**ROC-AUC**: How well the model ranks denied versus approved decisions at different thresholds."
            )
            rf=comp[comp.Model=="Random Forest"].iloc[0]
            lr=comp[comp.Model=="Logistic Regression"].iloc[0]
            takeaway(
                f"Random Forest has higher test F1 ({rf['Denial F1']:.3f}) and ROC-AUC ({rf['ROC-AUC']:.3f}); "
                f"Logistic Regression has slightly higher recall ({lr['Denial Recall']:.1%} vs {rf['Denial Recall']:.1%}). "
                "No single metric tells the whole story."
            )

    st.markdown('<div class="section-kicker">Confusion matrix</div>',unsafe_allow_html=True)
    choice=st.selectbox("Choose a model to inspect",
                        options=comp.Model.tolist(),index=2,
                        help="This changes only the confusion-matrix view, not the test results.")
    with st.container(border=True):
        c7,c8=st.columns([1.25,1],gap="medium")
        with c7:
            show_plot(confusion_chart(cm,choice),key=f"confusion_{choice}")
        with c8:
            sub=cm[cm.Model==choice]
            def get_count(actual,predicted):
                return int(sub[(sub.Actual==actual)&(sub.Predicted==predicted)].Count.sum())
            correct=get_count("Denied","Denied")
            missed=get_count("Denied","Approved")
            flagged=get_count("Approved","Denied")
            st.markdown(f"**Correctly identified denials:** {correct:,}")
            st.markdown(f"**Missed denials:** {missed:,}")
            st.markdown(f"**Approved decisions incorrectly flagged as denied:** {flagged:,}")
            st.caption("A missed denial is an actual denied decision that the model labels approved. An incorrect denial flag is an approved decision that the model labels denied.")
    st.markdown('<div class="section-kicker">Stability and interpretation</div>',unsafe_allow_html=True)
    c9,c10=st.columns(2,gap="medium")
    with c9:
        with st.container(border=True):
            chart_header("Training vs. Test Performance","Large gaps can indicate overfitting")
            overfit=comp[["Model","Training F1","Denial F1","Training ROC-AUC","ROC-AUC"]].copy()
            for col in ["Training F1","Denial F1","Training ROC-AUC","ROC-AUC"]:
                overfit[col]=overfit[col].map(lambda v:f"{v:.3f}")
            readable_table(overfit)
            rf=comp[comp.Model=="Random Forest"].iloc[0]
            takeaway(
                f"Random Forest training F1 is {rf['Training F1']:.3f}, while its test F1 is {rf['Denial F1']:.3f}. "
                f"The gap of {rf['Training F1']-rf['Denial F1']:.3f} suggests some overfitting. "
                "The test set was not used to train the models."
            )
            st.markdown("**Training-only cross-validation (3 folds)**")
            show_cv=cv[["Model","Validation F1 Mean","Validation F1 SD","Validation ROC-AUC Mean"]].copy()
            for col in ["Validation F1 Mean","Validation F1 SD","Validation ROC-AUC Mean"]:
                show_cv[col]=show_cv[col].map(lambda v:f"{v:.3f}")
            readable_table(show_cv)
            st.caption("Cross-validation uses only the training data; the held-out test set remains separate.")
    with c10:
        with st.container(border=True):
            chart_header("Random Forest Variable Importance","Permutation importance · top reported variables")
            show_plot(importance_chart(importance,top=9),key="feature_importance")
            takeaway(
                "DTI is the strongest variable in this model's permutation-importance analysis. "
                "A larger bar means shuffling that variable reduced average precision more. "
                "It does not prove the variable caused denial."
            )
    st.markdown(
        '<div class="soft-note"><b>Model limits:</b> These models describe historical decisions from a single lender and year. '
        'They exclude race, ethnicity, sex, and age as inputs. Missing credit scores and other underwriting data limit interpretation. '
        'Do not use the models to make individual mortgage-approval decisions.</div>',
        unsafe_allow_html=True
    )
    st.download_button(
        "Download model-evaluation CSVs (ZIP)",
        data=results_zip(str(RESULTS)),
        file_name="HMDA_Predictive_Results_for_Streamlit.zip",
        mime="application/zip",use_container_width=False
    )

st.markdown('<div class="footer">Source: 2025 HMDA Loan Application Register, New York State, JPMorgan Chase Bank, N.A. · '
            'Counts represent reported transactions, not necessarily distinct borrowers. '
            'Dashboard results are historical and descriptive; model results are held-out evaluations, not credit recommendations.</div>',
            unsafe_allow_html=True)
