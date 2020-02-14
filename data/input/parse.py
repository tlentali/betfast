import pandas as pd 
import numpy as np

df = pd.read_csv('people_team.csv')
df_merge = df.merge(df, on='team')
results = pd.crosstab(df_merge.peolpe_x, df_merge.peolpe_y)
np.fill_diagonal(results.values, 1)
results = results.replace({0:1, 1:0})
results.to_csv('affinity.csv', index=None, sep=';')