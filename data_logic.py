"""Deterministic descriptive calculations for the 2025 New York HMDA dashboard.

Only historical, aggregate HMDA records are used. These functions never train models.
"""
from pathlib import Path
import pandas as pd
import numpy as np

COUNTIES_NY = {
"36001":"Albany","36003":"Allegany","36005":"Bronx","36007":"Broome",
"36009":"Cattaraugus","36011":"Cayuga","36013":"Chautauqua","36015":"Chemung",
"36017":"Chenango","36019":"Clinton","36021":"Columbia","36023":"Cortland",
"36025":"Delaware","36027":"Dutchess","36029":"Erie","36031":"Essex",
"36033":"Franklin","36035":"Fulton","36037":"Genesee","36039":"Greene",
"36041":"Hamilton","36043":"Herkimer","36045":"Jefferson","36047":"Kings (Brooklyn)",
"36049":"Lewis","36051":"Livingston","36053":"Madison","36055":"Monroe",
"36057":"Montgomery","36059":"Nassau","36061":"New York (Manhattan)","36063":"Niagara",
"36065":"Oneida","36067":"Onondaga","36069":"Ontario","36071":"Orange",
"36073":"Orleans","36075":"Oswego","36077":"Otsego","36079":"Putnam",
"36081":"Queens","36083":"Rensselaer","36085":"Richmond (Staten Island)","36087":"Rockland",
"36089":"St. Lawrence","36091":"Saratoga","36093":"Schenectady","36095":"Schoharie",
"36097":"Schuyler","36099":"Seneca","36101":"Steuben","36103":"Suffolk",
"36105":"Sullivan","36107":"Tioga","36109":"Tompkins","36111":"Ulster",
"36113":"Warren","36115":"Washington","36117":"Wayne","36119":"Westchester",
"36121":"Wyoming","36123":"Yates"
}
LOAN_TYPES = {"1":"Conventional","2":"FHA","3":"VA","4":"RHS / FSA"}
OUTCOME_NAMES = {
    "1":"Loan Originated","2":"Approved, Not Accepted","3":"Application Denied",
    "4":"Withdrawn by Applicant","5":"File Closed for Incompleteness","6":"Purchased Loan",
}
OUTCOME_ORDER = [OUTCOME_NAMES[x] for x in ["1","2","3","4","5","6"]]
DTI_ORDER = ["<20%","20%-<30%","30%-<36%","36%-39%","40%-44%","45%-49%","50%-60%",">60%","Not Available"]
RACE_FOCUS = ["Black or African American","White","Asian","American Indian or Alaska Native",
              "Native Hawaiian or Other Pacific Islander","2 or more minority races"]
NUMERIC_REQUIRED = ("loan_amount",)
REQUIRED = {"action_taken","loan_purpose_label","loan_type","county_code",
            "denial_reason_1_label","derived_race","debt_to_income_ratio","loan_amount"}

def prepare_data(source: pd.DataFrame) -> pd.DataFrame:
    """Keep HMDA categorical codes as strings and add display fields only."""
    missing = REQUIRED - set(source.columns)
    if missing:
        raise ValueError(f"Cleaned CSV missing columns: {', '.join(sorted(missing))}")
    d = source.copy()
    # Read as strings to preserve county FIPS codes and the literal NA sentinel.
    for col in ["action_taken","loan_type","county_code","loan_purpose_label","denial_reason_1_label","derived_race","debt_to_income_ratio"]:
        d[col] = d[col].astype("string").str.strip()
    d["loan_amount_numeric"] = pd.to_numeric(d["loan_amount"],errors="coerce")
    d["county_display"] = d["county_code"].map(COUNTIES_NY).fillna(d["county_code"].map(lambda x: f"County {x}" if pd.notna(x) else "County Not Available"))
    d["loan_type_display"] = d["loan_type"].map(LOAN_TYPES).fillna("Other / Not Available")
    d["loan_purpose_display"] = d["loan_purpose_label"].fillna("Not Available")
    d["outcome_display"] = d["action_taken"].map(OUTCOME_NAMES).fillna("Other / Not Available")
    return d

def apply_filters(d, counties=None, purposes=None, loan_types=None):
    """An empty selection means all; each selected category narrows the current file."""
    out = d
    for column, selections in [
        ("county_code",counties),
        ("loan_purpose_display",purposes),
        ("loan_type",loan_types),
    ]:
        if selections:
            out=out[out[column].isin(selections)]
    return out

def populations(filtered):
    """Each measure uses its proper HMDA population."""
    processed=filtered[filtered["action_taken"].isin(["1","2","3","4","5"])]
    decisions=filtered[filtered["action_taken"].isin(["1","2","3"])]
    denied=filtered[filtered["action_taken"]=="3"]
    originated=filtered[filtered["action_taken"]=="1"]
    return processed, decisions, denied, originated

def summary(filtered):
    processed, decisions, denied, originated = populations(filtered)
    amounts=filtered["loan_amount_numeric"].dropna()
    return {
        "records":len(filtered),
        "processed":len(processed),
        "decisions":len(decisions),
        "denied":len(denied),
        "originated":len(originated),
        "purchased":int((filtered["action_taken"]=="6").sum()),
        "denial_rate":len(denied)/len(decisions) if len(decisions) else None,
        "median_loan":float(amounts.median()) if len(amounts) else None,
    }

def outcome_table(filtered):
    counts=filtered["outcome_display"].value_counts()
    out=pd.DataFrame({"Outcome":OUTCOME_ORDER,"Count":[int(counts.get(o,0)) for o in OUTCOME_ORDER]})
    out=out[out.Count>0].copy()
    out["Share"]=out["Count"]/len(filtered) if len(filtered) else np.nan
    return out

def purpose_table(processed):
    if processed.empty: return pd.DataFrame(columns=["Purpose","Count","Share"])
    out=processed["loan_purpose_display"].value_counts().reset_index()
    out.columns=["Purpose","Count"]
    out["Share"]=out.Count/len(processed)
    return out

def reason_table(denied):
    if denied.empty: return pd.DataFrame(columns=["Reason","Count","Share"])
    out=denied["denial_reason_1_label"].fillna("Not Available").replace("","Not Available").value_counts().reset_index()
    out.columns=["Reason","Count"]
    out["Share"]=out.Count/len(denied)
    return out

def dti_group(code):
    if pd.isna(code): return "Not Available"
    code=str(code).strip()
    if code in {"","NA","nan","None"}: return "Not Available"
    if code in {"<20%","20%-<30%","30%-<36%","50%-60%",">60%"}: return code
    try:
        x=float(code)
        if 36<=x<=39: return "36%-39%"
        if 40<=x<=44: return "40%-44%"
        if 45<=x<=49: return "45%-49%"
        if 50<=x<=60: return "50%-60%"
        if x>60: return ">60%"
        if x<20: return "<20%"
        if x<30: return "20%-<30%"
        if x<36: return "30%-<36%"
    except ValueError:
        pass
    return "Not Available"

def dti_table(decisions):
    if decisions.empty:return pd.DataFrame(columns=["DTI","Decisions","Denied","Rate"])
    tmp=decisions[["debt_to_income_ratio","action_taken"]].copy()
    tmp["DTI"]=tmp["debt_to_income_ratio"].map(dti_group)
    tmp["is_denied"]=(tmp["action_taken"]=="3").astype(int)
    g=tmp.groupby("DTI", observed=True).agg(Decisions=("is_denied","size"),Denied=("is_denied","sum"))
    out=g.reindex(DTI_ORDER,fill_value=0).reset_index()
    out=out[out.Decisions>0].copy()
    out["Rate"]=out.Denied/out.Decisions
    return out

def race_table(decisions, min_n=30):
    """Race rates for specified derived-race categories; exclude Joint/Unavailable."""
    if decisions.empty:return pd.DataFrame(columns=["Race","Decisions","Denied","Rate"])
    tmp=decisions[decisions.derived_race.isin(RACE_FOCUS)][["derived_race","action_taken"]].copy()
    tmp["is_denied"]=(tmp.action_taken=="3").astype(int)
    g=tmp.groupby("derived_race").agg(Decisions=("is_denied","size"),Denied=("is_denied","sum"))
    g=g[g.Decisions>=min_n].copy()
    if g.empty:return pd.DataFrame(columns=["Race","Decisions","Denied","Rate"])
    g["Rate"]=g.Denied/g.Decisions
    out=g.reset_index().rename(columns={"derived_race":"Race"})
    return out.sort_values(["Decisions","Race"],ascending=[False,True])

def validate_model_files(comparison, confusion):
    required={"Model","Accuracy","Denial Precision","Denial Recall","Denial F1","ROC-AUC","Training F1","Training ROC-AUC"}
    if not required.issubset(comparison.columns): raise ValueError("Model comparison CSV is missing expected columns.")
    if not {"Model","Actual","Predicted","Count"}.issubset(confusion.columns): raise ValueError("Confusion matrix CSV is missing expected columns.")
    for _,r in comparison.iterrows():
        rows=confusion[confusion.Model==r.Model]
        if len(rows)!=4:raise ValueError(f"Confusion rows missing for {r.Model}")
        tp=int(rows[(rows.Actual=="Denied") & (rows.Predicted=="Denied")].Count.sum())
        fn=int(rows[(rows.Actual=="Denied") & (rows.Predicted=="Approved")].Count.sum())
        fp=int(rows[(rows.Actual=="Approved") & (rows.Predicted=="Denied")].Count.sum())
        precision=tp/(tp+fp) if tp+fp else 0
        recall=tp/(tp+fn) if tp+fn else 0
        if abs(precision-float(r["Denial Precision"]))>0.0001 or abs(recall-float(r["Denial Recall"]))>0.0001:
            raise ValueError(f"Model comparison and confusion matrix disagree: {r.Model}")
    return True
