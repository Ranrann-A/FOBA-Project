"""Run `python verify_data.py` to check the files supplied with this dashboard."""
from pathlib import Path
import pandas as pd
from data_logic import prepare_data, summary, populations, dti_table, race_table, validate_model_files

here = Path(__file__).resolve().parent
df = prepare_data(pd.read_csv(here/"data"/"HMDA_NY_2025_Cleaned.csv",
                             dtype=str,keep_default_na=False,na_values=[""]))
s = summary(df)
assert len(df) == 24722, f"Unexpected row count: {len(df)}"
assert (s["processed"],s["decisions"],s["originated"],s["denied"],s["purchased"]) == (14735,11168,9163,1717,9987)
assert round(s["denial_rate"]*100,2)==15.37
assert s["median_loan"]==295000
processed,decisions,denied,originated = populations(df)
assert dti_table(decisions).set_index("DTI").loc[">60%","Denied"]==385
assert round(float(race_table(decisions).set_index("Race").loc["Black or African American","Rate"])*100,2)==26.45

model_results=here/"results"
comp=pd.read_csv(model_results/"HMDA_Predictive_Model_Comparison.csv")
confusion=pd.read_csv(model_results/"HMDA_Predictive_Confusion_Matrices.csv")
assert validate_model_files(comp,confusion)
assert abs(float(comp.set_index("Model").loc["Random Forest","Denial F1"])-0.593343)<1e-5

print("PASS: HMDA data populations, selected descriptive rates, and model-result files are consistent.")
