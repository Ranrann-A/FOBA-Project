"""2025 New York HMDA lending dashboard.

Start with: streamlit run app.py
Built from the group's cleaned 2025 HMDA CSV and saved Google Colab model evaluations.
"""
from pathlib import Path
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
    NAVY, TEAL, ORANGE, outcome_stacked_chart, race_dot_chart,
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

def display_kpis(cards):
    """Show each KPI in a native Streamlit card so labels and notes wrap cleanly."""
    # Two rows (3 + 2) allow long labels to wrap on narrower screens.
    for row in (cards[:3], cards[3:]):
        columns = st.columns(len(row), gap="small")
        for column, (label, value, note) in zip(columns, row):
            with column:
                with st.container(border=True):
                    st.caption(label)
                    st.markdown(f"### {value}")
                    st.caption(note)


def chart_header(title, description):
    """Native headings avoid showing raw HTML on different Streamlit versions."""
    st.markdown(f"#### {title}")
    st.caption(description)


def takeaway(message):
    st.caption(f"**Insight:** {message}")


def show_plot(fig, key):
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
        key=key,
    )


def show_table(t, percent=None):
    out=t.copy()
    if percent:
        for c in percent:
            if c in out:
                out[c]=out[c].map(lambda x:f"{x:.1%}")
    st.dataframe(out,hide_index=True,use_container_width=True)

def readable_table(t):
    """Native table that scrolls horizontally if the screen is narrow."""
    column_config = {}
    if "Model" in t.columns:
        column_config["Model"] = st.column_config.TextColumn("Model", width="large")
    st.dataframe(
        t,
        hide_index=True,
        use_container_width=True,
        column_config=column_config,
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

st.caption("FOUNDATIONS OF BUSINESS ANALYTICS · 2025 HMDA")
st.title("New York Mortgage Lending Analytics")
st.write(
    "JPMorgan Chase Bank, N.A. · New York State · 2025 reportable HMDA transactions. "
    "Explore lending activity and observed credit outcomes, then review how two models "
    "classify historical decisions."
)

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
    st.subheader("Key performance indicators")
    cards=[
        ("Processed Applications",pretty_int(s["processed"]),"Action codes 1–5"),
        ("Credit Decisions",pretty_int(s["decisions"]),"Approvals + denials · actions 1–3"),
        ("Originated Loans",pretty_int(s["originated"]),"Completed originations · action 1"),
        ("Denial Rate",pretty_pct(s["denial_rate"]),"Denied ÷ credit decisions"),
        ("Median Loan Amount",pretty_amount(s["median_loan"]),"All filtered records, incl. purchases"),
    ]
    display_kpis(cards)
    st.caption(
        "Counts and percentages use different HMDA populations when appropriate. "
        "The median loan amount describes all currently filtered transactions, including purchased loans. "
        "This is why it is $295K with no filters, rather than the processed-applications median."
    )

    if filtered.empty:
        st.info("No transactions match these filters. Select a different county, loan purpose, or loan type.")
    else:
        processed,decisions,denied,originated=populations(filtered)
        st.subheader("Lending activity and outcomes")
        c1,c2=st.columns(2,gap="medium")
        with c1:
            with st.container(border=True):
                chart_header("Transaction Outcome Distribution","All filtered HMDA transactions · share of reported outcomes")
                t=outcome_table(filtered)
                show_plot(outcome_stacked_chart(t),key="outcomes")
                with st.expander("See counts and percentages by outcome"):
                    show_table(t,percent=["Share"])
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

        st.subheader("Denial patterns")
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

        st.subheader("Applicant outcomes")
        with st.container(border=True):
            chart_header("Observed Denial Rate by Race","Dot plot · race groups with at least 30 decisions under the selected filters")
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
    st.caption(
        "**Interpretation:** This dashboard describes 2025 HMDA reporting for one lender in one state. "
        "It does not control for every underwriting factor, establish causation, or indicate whether "
        "an individual mortgage applicant should be approved."
    )

with tab_predict:
    st.subheader("Historical predictive classification")
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

    st.subheader("Model evaluation")
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

    st.subheader("Confusion matrix")
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
    st.subheader("Stability and interpretation")
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
    st.caption(
        "**Model limits:** These models describe historical decisions from a single lender and year. "
        "They exclude race, ethnicity, sex, and age as inputs. Missing credit scores and other "
        "underwriting data limit interpretation. Do not use the models to make individual mortgage-approval decisions."
    )
    st.download_button(
        "Download model-evaluation CSVs (ZIP)",
        data=results_zip(str(RESULTS)),
        file_name="HMDA_Predictive_Results_for_Streamlit.zip",
        mime="application/zip",use_container_width=False
    )

st.divider()
st.caption(
    "Source: 2025 HMDA Loan Application Register, New York State, JPMorgan Chase Bank, N.A. "
    "Counts represent reported transactions, not necessarily distinct borrowers. "
    "Dashboard results are historical and descriptive; model results are held-out evaluations, "
    "not credit recommendations."
)
