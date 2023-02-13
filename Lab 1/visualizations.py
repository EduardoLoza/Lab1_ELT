# Import libraries
import plotly.express as px
import pandas as pd


## -------------------------------------- Visualization functions -------------------------------------- ##

def pie_chart(df):
    """
    Interactive pie charts.

    """

    # Stock Weightings
    fig1 = px.pie(df, values="Peso (%)", names="Ticker", title="Pesos de cada Activo en NAFTRAC")

    # Sector Weightings
    df = df.groupby("Sector").sum()
    if df["Peso (%)"].sum() != 1:
        df.loc["Efectivo", :] = [1 - df["Peso (%)"].sum(), 0]

    df.reset_index(inplace=True)
    fig2 = px.pie(df, values="Peso (%)", names="Sector", title="Pesos de cada Sector en NAFTRAC ")

    return fig1, fig2


def time_series(df, title):
    """
    Interactive time series plots.

    """

    fig = px.line(x=df.index, y=df.Capital, title=title,
                  labels={"x": "Date", "y": "Mexican Pesos MXN"})

    return fig

