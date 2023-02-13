import data, visualizations, functions


## ------------------------------------------ Main functionality ------------------------------------------ ##

def lab_passive(naftrac_date=20210129, capital=1000000, comission=0.125):
    """
    Lab. 1. Passive Investment Strategy.

    """

    df, naftrac_date = data.file_reading(naftrac_date=naftrac_date)
    df = data.data_wrangling(df)
    fig1, fig2 = visualizations.pie_chart(df)

    df_passive,fig3, df_metrics = functions.passive_investment_strategy(df, naftrac_date, capital, comission,
                                                                         "Passive Investment Strategy: NAFTRAC")

    return df_passive, df_metrics, fig1, fig2, fig3