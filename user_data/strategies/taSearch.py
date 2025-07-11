import pandas as pd
import numpy as np
import talib.abstract as ta

from scipy import signal


class TaSearch:
    n: int

    def __init__(self, n: int):
        self.n = n
        pd.set_option('display.max_rows', 100000)
        pd.set_option('display.precision', 10)
        pd.set_option('mode.chained_assignment', None)

    def percentage(self, df: pd.DataFrame) -> float:
        # mean = df['close'].mean()
        max = df['close'].max()
        min = df['close'].min()

        p = self.diff_percentage(min, max)

        return abs(p)

    def find_extremes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parameters
        ----------
        n : int
            Number of points to be checked before and after
        """

        df['id'] = range(0, len(df))
        df['rsi_7'] = ta.RSI(df['close'], timeperiod=7)

        df['market'] = ''
        df['percentage'] = ''
        df['buy_stride'] = -1
        df['buy_past_rsi'] = -1

        df['buy'] = ''
        df['ex_min_percentage'] = ''
        df['ex_min'] = df.iloc[signal.argrelextrema(df.close.values, np.less_equal, order=self.n)[0]]['close']
        df['ex_max_percentage'] = ''
        df['ex_max'] = df.iloc[signal.argrelextrema(df.close.values, np.greater_equal, order=self.n)[0]]['close']
        df['sell'] = ''

        # find Min
        # -----

        ex_min = df.query(f'ex_min > 0')
        ex_min_index = ex_min.index.values.tolist()
        ex_min_index.reverse()

        for id in ex_min_index:
            max = df.query(f'index < {id} and ex_max > 0')
            last = max[-1:]

            if last.size > 0:
                per = float(
                    self.diff_percentage(
                        v1=ex_min.loc[id]['close'],
                        v2=last['close']
                    )
                )
                df['ex_min_percentage'].loc[id] = -per

        # find Max
        # -----
        ex_max = df.query(f'ex_max > 0')
        ex_max_index = ex_max.index.values.tolist()
        ex_max_index.reverse()

        for id in ex_max_index:
            max = df.query(f'index < {id} and ex_min > 0')
            last = max[-1:]

            if last.size > 0:
                per = float(
                    self.diff_percentage(
                        v2=ex_max.loc[id]['close'],
                        v1=last['close']
                    )
                )
                df['ex_max_percentage'].loc[id] = per

        # clean NaN
        df['ex_min'] = df['ex_min'].apply(lambda x: x if float(x) > 0 else '')
        df['ex_max'] = df['ex_max'].apply(lambda x: x if float(x) > 0 else '')

        return df

    def market(self, df: pd.DataFrame, n: int) -> int:
        mean = self.mean(df=df, n=n)
        market = 1

        if mean[2][3] < mean[1][0] and mean[2][3] < mean[0]:
            market = -1

        return market

    def mean(self, df: pd.DataFrame, n: int) -> []:
        n0 = n - self.n
        n25 = n0 + int(self.n / 4)
        n50 = n0 + int(self.n / 2)
        n75 = n0 + int(self.n / 2) + int(self.n / 4)
        n100 = n

        mean = df[n0: n100]['close'].mean()
        mean2 = [
            df[n0: n50]['close'].mean(),
            df[n50: n100]['close'].mean(),
        ]
        mean4 = [
            df[n0: n25]['close'].mean(),
            df[n25: n50]['close'].mean(),
            df[n50: n75]['close'].mean(),
            df[n75: n100]['close'].mean(),
        ]

        return mean, mean2, mean4

    def diff_percentage(self, v2, v1) -> float:
        diff = ((v2 - v1) / ((v2 + v1) / 2)) * 100
        diff = np.round(diff, 4)

        return diff
