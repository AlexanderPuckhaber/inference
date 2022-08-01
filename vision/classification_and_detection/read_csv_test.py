import pandas as pd
import os
import json

perf_output_dir = 'perf_output'

filenames = os.listdir(perf_output_dir)

dataframes = []

for filename in filenames:
    file_path = os.path.join(perf_output_dir, filename)
    with open(file_path, 'r') as f:
        firstline = f.readline()
        args = json.loads(firstline)
        secondline = f.readline()
        perf_time_start = secondline.split('# started on ')[1]

        # read perf csv
        df = pd.read_csv(file_path, sep=',', skiprows=2, names=['count', 'data_type', 'event', 'unk1', 'unk2', 'computed_value', 'computed_name'])
        df.assign(name='perf_time_start')
        df['perf_time_start'] = perf_time_start
        for arg in args:
            arg_header = 'arg.{}'.format(arg)
            df.assign(name=arg_header)
            df[arg_header] = str(args[arg])

        # print(df)
        dataframes.append(df)

    # merge dataframes
    merged_df = pd.concat(dataframes)

    print(merged_df)

    merged_df.to_csv('merged_df.csv')