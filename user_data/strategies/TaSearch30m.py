import pandas as pd

from freqtrade.strategy.interface import IStrategy
from .taSearch import TaSearch


class TaSearch30m(IStrategy):
    search: TaSearch

    n: int = 72
    minimal_roi = {
        "0": 0.05
    }
    stoploss = -0.05
    timeframe = '30m'

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.search = TaSearch(n=self.n)

    def populate_indicators(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']

        df = self.search.find_extremes(df)
        df = self.buy_past_rsi(df)
        df = self.buy_stride(df)

        return df

    def buy_past_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        for i, row in df[::-1].iterrows():
            df['percentage'].loc[i] = self.search.percentage(df[i - 48 * 4:i - 24])  # * 0.7

            if df.loc[i]['ex_min_percentage'] and df.loc[i]['ex_min_percentage'] < -df.loc[i]['percentage']:
                c = 0
                for x in range(i - 48, i):
                    if x > 1 and df.loc[x]['rsi_7'] < 25:
                        c += 1
                        df['buy_past_rsi'].loc[x] = c
                        df['buy_past_rsi'].loc[i] = c
                        df['percentage'].loc[x] = df.loc[i]['percentage']

        return df

    def buy_stride(self, df: pd.DataFrame) -> pd.DataFrame:
        for i, row in df[::-1].iterrows():
            if 20 < df.loc[i]['rsi_7'] < 45:
                for x in range(i - 24, i):
                    if x > 1 \
                            and df.loc[x]['ex_min_percentage'] \
                            and df.loc[x]['ex_min_percentage'] < -df.loc[i]['percentage']:
                        df['buy_stride'].loc[i] = i - x
                        df['buy_past_rsi'].loc[i] = df.loc[x]['buy_past_rsi']

                        df['market'].loc[i] = self.search.market(df=df, n=i)
                        df['percentage'].loc[i] = df.loc[i]['percentage']
        return df

    def populate_buy_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df.loc[
            (df['buy_stride'] > -1) &
            (df['buy_past_rsi'] > -1) &
            (df['market'] == -1),
            'buy'
        ] = 1

        return df

    def populate_sell_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df.loc[(df['rsi_7'] > 85), 'sell'] = 1

        return df
