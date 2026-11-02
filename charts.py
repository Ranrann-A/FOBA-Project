"""Consistent, responsive Plotly charts for the HMDA Streamlit app."""
import textwrap
import pandas as pd
import numpy as np
import plotly.graph_objects as go

NAVY="#163652"
TEAL="#177E88"
TEAL_PALE="#9CCDD0"
ORANGE="#C57B41"
GRAY="#91A2B5"
GRID="#E7ECF3"
FONT="#26394F"

# Consistent outcome colors for the 100% stacked transaction chart and its key.
OUTCOME_COLORS = {
    "Loan Originated": "#177E88",
    "Approved, Not Accepted": "#8193AD",
    "Application Denied": "#D27B50",
    "Withdrawn by Applicant": "#8A7DB2",
    "File Closed for Incompleteness": "#C29A4F",
    "Purchased Loan": "#326A9D",
}

def wrap_label(text, width=20):
    # Plotly supports HTML breaks, which prevent long tick labels from being clipped.
    return "<br>".join(textwrap.wrap(str(text), width=width, break_long_words=False, break_on_hyphens=False)) or str(text)

def style_chart(fig, height=350, margin=None):
    fig.update_layout(
        height=height, autosize=True,
        paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
        font=dict(family="Arial, Helvetica, sans-serif",size=12,color=FONT),
        margin=margin or dict(l=20,r=23,t=25,b=28),
        showlegend=False, bargap=0.34,
        hoverlabel=dict(bgcolor="white",font_size=13,font_family="Arial, Helvetica, sans-serif"),
    )
    fig.update_xaxes(showgrid=True,gridcolor=GRID,zeroline=False,linecolor=GRID,
                     tickfont=dict(size=11),automargin=True)
    fig.update_yaxes(showgrid=False,zeroline=False,linecolor=GRID,tickfont=dict(size=11),
                     automargin=True)
    return fig


def outcome_stacked_chart(table):
    """A single 100% horizontal bar showing how all reported outcomes add up."""
    t = table[table["Count"] > 0].copy()
    if t.empty:
        return go.Figure()
    fig = go.Figure()
    for _, row in t.iterrows():
        outcome = str(row["Outcome"])
        share = float(row["Share"])
        count = int(row["Count"])
        fig.add_trace(go.Bar(
            name=outcome,
            x=[share * 100],
            y=["All transactions"],
            orientation="h",
            marker=dict(color=OUTCOME_COLORS.get(outcome, GRAY), line=dict(color="white",width=1.2)),
            width=0.56,
            text=[f"{share:.0%}" if share >= 0.10 else ""],
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(size=12,color="white"),
            hovertemplate=(
                f"<b>{outcome}</b><br>"
                f"Records: {count:,}<br>"
                f"Share: {share:.2%}<extra></extra>"
            ),
        ))
    style_chart(fig, height=155, margin=dict(l=13,r=14,t=5,b=28))
    fig.update_layout(
        barmode="stack",
        showlegend=False, bargap=0.25,
        uniformtext=dict(minsize=11,mode="hide"),
    )
    fig.update_xaxes(
        range=[0,100],
        tickmode="array",
        tickvals=[0,25,50,75,100],
        ticktext=["0%","25%","50%","75%","100%"],
        showgrid=False,
        linecolor=GRID,
        tickfont=dict(size=11),
        fixedrange=True,
    )
    fig.update_yaxes(visible=False,fixedrange=True)
    return fig

def race_dot_chart(table, overall=None):
    """A dot plot for observed group denial percentages and group sizes."""
    t = table.copy().sort_values("Rate", ascending=True)
    if t.empty:
        return go.Figure()
    labels = t["Race"].astype(str).tolist()
    rates = (t["Rate"].astype(float)*100).tolist()
    decisions = t["Decisions"].astype(int).tolist()
    denied = t["Denied"].astype(int).tolist()
    upper = max(35, min(105, max(rates)+12))
    fig = go.Figure(go.Scatter(
        x=rates,
        y=labels,
        mode="markers+text",
        marker=dict(size=15,color=TEAL,line=dict(width=2,color="white")),
        text=[f"{v:.1f}%" for v in rates],
        textposition=["middle left" if v>upper-13 else "middle right" for v in rates],
        textfont=dict(size=12,color=NAVY),
        customdata=np.column_stack([decisions,denied]),
        hovertemplate=(
            "<b>%{y}</b><br>Denial rate: %{x:.2f}%"
            "<br>Credit decisions: %{customdata[0]:,}"
            "<br>Denied: %{customdata[1]:,}<extra></extra>"
        ),
        cliponaxis=False,
    ))
    style_chart(
        fig,
        height=max(315, len(t)*55+110),
        margin=dict(l=16,r=47,t=24,b=38),
    )
    fig.update_xaxes(
        title="Observed denial rate",
        range=[0,upper],
        ticksuffix="%",
        dtick=10 if upper<=55 else 20,
        showgrid=True,
        gridcolor=GRID,
        fixedrange=True,
    )
    fig.update_yaxes(
        tickmode="array",
        tickvals=labels,
        ticktext=[wrap_label(x,32) for x in labels],
        categoryorder="array",
        categoryarray=labels,
        showgrid=False,
        fixedrange=True,
    )
    if overall is not None:
        fig.add_vline(x=overall*100,line_width=1.5,line_dash="dot",line_color=ORANGE)
    return fig

def horizontal_counts(table, label_col, color=TEAL, height=355, max_ticks=18):
    t=table.copy().sort_values("Count",ascending=True)
    labels=t[label_col].astype(str).tolist()
    fig=go.Figure()
    fig.add_trace(go.Bar(
        x=t.Count.tolist(),y=labels,orientation="h",marker_color=color,
        customdata=np.stack([t["Share"].to_numpy()],axis=-1) if "Share" in t else None,
        hovertemplate="<b>%{y}</b><br>Records: %{x:,}<br>Share: %{customdata[0]:.1%}<extra></extra>"
        if "Share" in t else "<b>%{y}</b><br>Records: %{x:,}<extra></extra>",
        text=[f"{int(x):,}" for x in t.Count],textposition="outside",
        textfont=dict(size=11,color=NAVY),cliponaxis=False,
    ))
    style_chart(fig,height=max(height,52*len(t)+70),margin=dict(l=20,r=52,t=24,b=24))
    fig.update_yaxes(tickmode="array",tickvals=labels,
                     ticktext=[wrap_label(x,max_ticks) for x in labels])
    fig.update_xaxes(title=None, rangemode="tozero", tickformat=",")
    return fig

def purpose_chart(table):
    t=table.copy()
    labels=t.Purpose.astype(str).tolist()
    fig=go.Figure(go.Bar(
        x=labels, y=t.Share.to_numpy()*100,
        marker_color=[TEAL if i==0 else TEAL_PALE for i in range(len(t))],
        customdata=np.stack([t.Count.to_numpy()],axis=-1),
        text=[f"{p:.1%}" for p in t.Share],textposition="outside",
        textfont=dict(size=11,color=NAVY), cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Applications: %{customdata[0]:,}<br>Share: %{y:.1f}%<extra></extra>",
    ))
    style_chart(fig, height=355,margin=dict(l=35,r=20,t=26,b=68))
    fig.update_xaxes(tickmode="array",tickvals=labels,
                     ticktext=[wrap_label(x,13) for x in labels],tickangle=0,
                     tickfont=dict(size=10))
    fig.update_yaxes(title=None,ticksuffix="%",rangemode="tozero")
    return fig

def rate_chart(table, category, overall=None, height=420, threshold=None):
    t=table.copy().sort_values("Rate",ascending=True)
    cats=t[category].astype(str).tolist()
    if "Decisions" not in t.columns: raise ValueError("Rate chart needs decision counts.")
    values=t.Rate.to_numpy()*100
    colors=[(TEAL if (threshold is None or int(n)>=threshold) else GRAY) for n in t.Decisions]
    fig=go.Figure(go.Bar(
        x=values, y=cats, orientation="h",marker_color=colors,
        customdata=np.stack([t.Decisions.to_numpy(),t.Denied.to_numpy()],axis=-1),
        text=[f"{p:.1f}%" for p in values],textposition="outside",
        textfont=dict(size=11,color=NAVY),cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Denial rate: %{x:.2f}%<br>Decisions: %{customdata[0]:,}<br>Denied: %{customdata[1]:,}<extra></extra>",
    ))
    style_chart(fig,max(height,len(t)*44+100), margin=dict(l=18,r=62,t=24,b=24))
    fig.update_xaxes(title=None,range=[0,max(104.0, max(values,default=0)+8)],ticksuffix="%")
    fig.update_yaxes(tickmode="array",tickvals=cats,ticktext=[wrap_label(c,21) for c in cats])
    if overall is not None:
        fig.add_vline(x=overall*100,line_width=1.5,line_dash="dot",line_color=ORANGE)
    return fig

def metrics_comparison_chart(comp):
    t=comp[comp.Model!="Majority-Class Baseline"].copy()
    x=t.Model.tolist()
    fig=go.Figure()
    for col,name,color in [
        ("Denial Precision","Precision",GRAY),
        ("Denial Recall","Recall",TEAL),
        ("Denial F1","F1",ORANGE),
        ("ROC-AUC","ROC-AUC",NAVY),
    ]:
        fig.add_trace(go.Bar(
            name=name,x=x,y=t[col].to_numpy()*100,
            marker_color=color,
            hovertemplate=f"<b>%{{x}}</b><br>{name}: %{{y:.1f}}%<extra></extra>",
        ))
    style_chart(fig,height=375,margin=dict(l=35,r=12,t=25,b=32))
    fig.update_layout(showlegend=True,barmode="group",bargap=.3,
                      legend=dict(orientation="h",yanchor="bottom",y=1.04,xanchor="left",x=0,
                      font=dict(size=11)))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(range=[0,105],ticksuffix="%")
    return fig

def confusion_chart(confusion, model):
    rows=confusion[confusion.Model==model]
    def c(a,p):
        return int(rows[(rows.Actual==a)&(rows.Predicted==p)].Count.sum())
    # Rows = actual, cols = predicted
    z=[[c("Approved","Approved"),c("Approved","Denied")],
       [c("Denied","Approved"),c("Denied","Denied")]]
    labels=[["Correct approvals","Incorrect denial flags"],["Missed denials","Correct denials"]]
    fig=go.Figure(go.Heatmap(
        z=z,x=["Predicted Approved","Predicted Denied"],y=["Actually Approved","Actually Denied"],
        colorscale=[[0,"#E8F3F4"],[0.45,"#7EB5BD"],[1,NAVY]],showscale=False,
        hovertemplate="%{y}<br>%{x}<br>Records: %{z:,}<extra></extra>",
    ))
    for i in range(2):
        for j in range(2):
            fig.add_annotation(
                x=j,y=i,text=f"<b>{z[i][j]:,}</b><br>{wrap_label(labels[i][j],16)}",
                showarrow=False,font=dict(size=12,color=NAVY if z[i][j]<700 else "#FFFFFF")
            )
    style_chart(fig,height=330,margin=dict(l=15,r=10,t=24,b=35))
    fig.update_yaxes(autorange="reversed",tickmode="array",tickvals=["Actually Approved","Actually Denied"],
                      ticktext=["Actually<br>Approved","Actually<br>Denied"])
    fig.update_xaxes(side="bottom",tickangle=0,showgrid=False,tickmode="array",
                     tickvals=["Predicted Approved","Predicted Denied"],
                     ticktext=["Predicted<br>Approved","Predicted<br>Denied"])
    return fig

VARIABLE_NAMES = {
    "debt_to_income_ratio":"Debt-to-income ratio",
    "loan_amount":"Loan amount",
    "income":"Applicant income",
    "loan_to_value_ratio":"Loan-to-value ratio",
    "property_value":"Property value",
    "loan_term":"Loan term",
    "loan_purpose":"Loan purpose",
    "loan_type":"Loan type",
    "lien_status":"Lien status",
    "occupancy_type":"Occupancy type",
    "preapproval":"Preapproval",
    "conforming_loan_limit":"Conforming loan limit",
    "interest_only_payment":"Interest-only payment",
    "balloon_payment":"Balloon payment",
    "construction_method":"Construction method",
    "total_units":"Total units",
    "open_end_line_of_credit":"Open-end line of credit",
    "business_or_commercial_purpose":"Business/commercial purpose",
}

def importance_chart(feature_table, top=9):
    t=feature_table.sort_values("Mean Average-Precision Decrease",ascending=False).head(top).copy()
    t["name"]=t.Variable.map(VARIABLE_NAMES).fillna(t.Variable.str.replace("_"," ").str.title())
    t=t.sort_values("Mean Average-Precision Decrease")
    fig=go.Figure(go.Bar(
        x=t["Mean Average-Precision Decrease"],
        y=t["name"],orientation="h",
        marker_color=[TEAL if float(x)>0 else GRAY for x in t["Mean Average-Precision Decrease"]],
        error_x=dict(type="data",array=t["Repeat Standard Deviation"].tolist(),visible=True,
                     color=GRAY,thickness=1.2),
        hovertemplate="<b>%{y}</b><br>Average-precision decrease: %{x:.3f}<extra></extra>",
    ))
    style_chart(fig,height=max(310,40*len(t)+72),margin=dict(l=18,r=20,t=24,b=35))
    fig.update_yaxes(tickmode="array",tickvals=t["name"],ticktext=[wrap_label(x,24) for x in t["name"]])
    fig.update_xaxes(title="Average-precision decrease when shuffled",tickformat=".2f",zeroline=True,zerolinecolor=GRID)
    return fig
