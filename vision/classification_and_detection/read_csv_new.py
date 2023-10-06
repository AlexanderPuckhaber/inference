import pandas as pd
import os
import json

# perf_output_dir = 'perf_output'

perf_output_index_filename = 'my_output_index2.csv'

index_df = pd.read_csv(perf_output_index_filename)

dataframes = []

for index, row in index_df.iterrows():
    file_path = row['perf_output_filename']
    with open(file_path, 'r') as f:
        df = pd.read_csv(file_path, skiprows=2, names=['time', 'count', 'extra', 'counter', 'task_clock', 'multiplexing_frac', 'stat', 'stat_desc'])
        
        

        # print(df)

        df = df.drop(df[df['count'] == '<not counted>'].index)
        df = df.drop(df[df['count'] == '<not supported>'].index)

        df['count'] = df['count'].astype(float)

        df['multiplexing_frac'] = df['multiplexing_frac'].astype(float)

        if df['multiplexing_frac'].min() < 100.0:
            print("Error: multiplexing was used! A simple aggregation may produce skewed results!")
            print(file_path)
            exit(1)

        agg_totals = df.groupby(['counter'])['count'].sum()

        row.index.names = ['key']
        agg_totals.index.names = ['key']

        # print(row)
        # print(agg_totals)

        # new_df = pd.DataFrame([row, agg_totals])

        new_df = pd.concat([row, agg_totals], axis=0)
        # print(new_df.T)
        new_df = pd.DataFrame(new_df).T
        print(new_df)

        dataframes.append(new_df)


# merge dataframes
merged_df = pd.concat(dataframes, axis=0)

print(merged_df)

merged_df.to_csv('merged_df_new2.csv')