import visualizations
import numpy as np
import pandas as pd
import yfinance as yf
import datetime

class Passive:

    def __init__(self):
        pass

    @staticmethod
    def read_file() -> pd.DataFrame:
        df = pd.read_csv('~\\Documents\\ITESO\\MyST\\Modulo 1\\Lab 1\\files\\NAFTRAC_20210129.csv', skiprows=2)
        df = df.loc[:, ['Ticker', 'Peso (%)']]
        df.dropna(subset=['Peso (%)'], inplace=True)
        df['Ticker'] = df['Ticker'].str.replace('*', '', regex=False)
        df['Ticker'] = df['Ticker'].str.replace('MEXCHEM', 'ORBIA')
        df['Ticker'] = df['Ticker'].str.replace('LIVEPOLC.1', 'LIVEPOLC-1', regex=False)
        df.set_index('Ticker', inplace=True)
        df.drop(["KOFUBL", "MXN", "NMKA",], inplace=True)
        return df

    def get_historical(self) -> pd.DataFrame:
        df = self.read_file()
        df_tickers = df.index.to_list()
        historical = pd.DataFrame()
        for i in df_tickers:
            try:
                stock = i + ".MX"
                historical[i] = yf.download(stock, start='2021-01-29', progress=False).loc[:, 'Adj Close']
            except:
                pass
        end_date = datetime.datetime.today()
        start_date = datetime.datetime(2021, 1, 29)
        periods = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        s = pd.date_range('2021-01-29', periods=periods, freq='BM')
        historical = historical.reindex(index=s)
        return historical

    def get_passive_table(self) -> pd.DataFrame:
        historic = self.get_historical()
        historic_ = pd.DataFrame(historic.iloc[0, :])
        historic_.columns = (['Price'])
        weights = self.read_file()
        historic_ = pd.concat([historic_, weights], axis=1)
        historic_['Comision_por_Accion'] = historic_['Price'] * 0.00125
        presupuesto = 1000000
        historic_['Acciones'] = (presupuesto * (historic_['Peso (%)']) / 100) / (
                    historic_['Price'] + historic_['Comision_por_Accion'])
        historic_['Acciones'] = historic_['Acciones'].apply(np.floor)
        historic_['Capital'] = np.round(historic_['Acciones'] * (historic_['Price'] + historic_['Comision_por_Accion']),
                                        2)

        # CASH
        historic_.loc['CASH'] = [100 - sum(historic_['Peso (%)']), 0, 0, 0,
                                 ((100 - sum(historic_['Peso (%)'])) / 100) * presupuesto]

        for i in historic.columns:
            historic['Capital_' + i] = np.round(
                historic_['Acciones'][i] * (historic[i] + historic_['Comision_por_Accion'][i]), 2)

        historic['Capital_CASH'] = historic_['Capital']['CASH']
        num_acc = len(historic_) - 1
        historic['Capital_Total'] = historic.iloc[:, num_acc:].sum(axis=1)

        # Rend
        historic['Rend'] = historic['Capital_Total'].pct_change()
        historic.fillna(0, inplace=True)

        return historic.iloc[:, -2:]

    def get_rend(self) -> pd.DataFrame:
        df = self.get_passive_table()
        df['Rend_accum'] = (df['Capital_Total'] - df['Capital_Total'][0]) / df['Capital_Total'][0]
        return df

class Active:

    def __init__(self):
        pass

    @staticmethod
    def get_historical() -> pd.DataFrame:
        return Passive().get_historical()

    def get_sharpe(self) -> pd.DataFrame:
        df = self.get_historical()
        ret = df.pct_change().dropna()
        w = []
        sharpe = []
        s = []
        er = []
        r = ret.mean()
        cov = np.cov(r)
        for j in range(100000):
            a = np.random.random(len(df.columns))
            a /= np.sum(a)
            ren = a.dot(r)
            ss = np.sqrt(a.dot(cov).dot(a.T))
            sh = ren / ss
            w.append(a)
            s.append(ss)
            er.append(ren)
            sharpe.append(sh)
        portfolio = {'Returns': er, 'Volatility': s, 'Sharpe Ratio': sharpe}
        for i, j in enumerate(df):
            portfolio[j + ' Weight'] = [Weight[i] for Weight in w]
        portfolio = pd.DataFrame(portfolio)
        order = ['Returns', 'Volatility', 'Sharpe Ratio'] + [j + ' Weight' for j in df]
        portfolio = portfolio[order]
        max_sharpe = portfolio['Sharpe Ratio'].max()
        max_sharpe_port = portfolio.loc[portfolio['Sharpe Ratio'] == max_sharpe]
        cols = df.columns
        weights = max_sharpe_port.iloc[:, 3:]
        weights = weights.T
        weights = weights.set_index(cols)
        weights.columns = ['Peso (%)']
        weights['Peso (%)'] = weights['Peso (%)'] * 100
        return weights
def passive_investment_strategy(df, naftrac_date, capital, comission, title):
    """
    Passive Investment Strategy general functions.

    """

    # Data download from yfinance
    start_date = pd.to_datetime(str(naftrac_date))
    stock_prices = pd.DataFrame()

    for stock in list(df["Ticker"]):
        stock_prices[stock] = yf.download(stock, start_date, progress=False, show_errors=False)["Adj Close"]

    stock_prices.reset_index(inplace=True)
    stock_prices = stock_prices.groupby([stock_prices["Date"].dt.year, stock_prices["Date"].dt.month],
                                        as_index=False).last()
    stock_prices.set_index("Date", inplace=True)

    # Passive strategy backtest
    position_values = [np.floor((capital * weights_i) / (price_i * (1 + comission / 100))) for price_i, weights_i in
                       zip(list(stock_prices.iloc[0, :]), list(df["Peso (%)"]))]
    cash = capital - np.dot(position_values, stock_prices.iloc[0, :] * (1 + comission / 100))

    df_passive = pd.DataFrame(index=stock_prices.index)
    df_passive["Capital"] = np.dot(stock_prices, position_values) + cash
    df_passive["Return"] = df_passive["Capital"].pct_change()
    df_passive["Cummulative Return"] = (df_passive["Return"] + 1).cumprod() - 1

    fig = visualizations.time_series(df_passive, title)

    # Performance
    df_metrics = pd.DataFrame(index=["rend_m", "rend_c", "sharpe"], columns=["descripción", "inv_pasiva"])
    df_metrics.loc["rend_m", "descripción"] = "Rendimiento promedio mensual"
    df_metrics.loc["rend_m", "inv_pasiva"] = df_passive["Return"].dropna().mean()
    df_metrics.loc["rend_c", "descripción"] = "Rendimiento mensual acumulado"
    df_metrics.loc["rend_c", "inv_pasiva"] = df_passive["Cummulative Return"][-1]
    df_metrics.loc["sharpe", "descripción"] = "Sharpe ratio"
    df_metrics.loc["sharpe", "inv_pasiva"] = df_passive["Return"].dropna().mean() / df_passive["Return"].dropna().std()

    return df_passive, fig, df_metrics

class Metrics:

    def __init__(self):
        pass

    @staticmethod
    def get_metrics() -> pd.DataFrame:
        passive = Passive().get_rend()
        rf = 0.075*3
        metric_df = pd.DataFrame(data={'medida': ['rend_m', 'rend_c', 'sharpe'],
                                       'decripcion': ['Rendimiento Promedio Mensual', 'Rendimiento mensual acumulado',
                                                      'Sharpe Ratio'],
                                       'inv_pasiva': [passive['Rend'].mean(), passive['Rend_accum'][-1],
                                                      (passive['Rend_accum'][-1] - rf) / passive['Rend_accum'].std()]})
        return metric_df
