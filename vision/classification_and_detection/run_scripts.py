import os
import subprocess
import random
import time
import pandas as pd

perf_ctl_fifo_path = os.path.join('/tmp/', 'perf_ctl.fifo')
perf_output_dir = 'perf_output'

index_filename = 'perf_output_index.csv'


dataset_folder = 'data'
models_folder = 'models'

env_vars = 'DATA_DIR={} MODEL_DIR={}'.format(dataset_folder, models_folder)

perf_sw_events = 'task-clock,context-switches,cpu-migrations,page-faults'



perf_hw_event_sets = [
    # 'cycles,cache-references,cache-misses',
    # 'instructions,branches,branch-misses',
    # 'L1-dcache-loads,L1-dcache-load-misses,dTLB-load-misses,dtlb_load_misses.miss_causes_a_walk'

    # CFG_IPC
    'CPU_CLK_UNHALTED,INST_RETIRED,CYCLE_ACTIVITY.STALLS_LDM_PENDING,FP_ARITH_INST_RETIRED.SCALAR',
    # CFG_CACHEMPKI
    'MEM_LOAD_UOPS_RETIRED.L1_MISS,L2_TRANS.RFO,MEM_LOAD_UOPS_RETIRED.L2_MISS,OFFCORE_REQUESTS.DEMAND_RFO',
    # CFG_BRANCHES
    # 'br_inst_retired.all_branches,br_misp_retired.all_branches,br_inst_retired:conditional,br_inst_retired:near_call',
    'br_inst_retired.all_branches,br_misp_retired.all_branches',
    # CFG_TLBMPKI
    'DTLB_LOAD_MISSES.MISS_CAUSES_A_WALK,DTLB_STORE_MISSES.MISS_CAUSES_A_WALK,DTLB_LOAD_MISSES.STLB_HIT,DTLB_STORE_MISSES.STLB_HIT'
]

base_commands = [
    './run_local.sh onnxruntime resnet50 cpu --dataset-path data/imagenet/ --model models/resnet50_v1.onnx --inputs input_tensor:0'.format(os.path.join(dataset_folder, 'imagenet')),
#     './run_local.sh cpu --profile ssd-mobilenet-onnxruntime --dataset coco-300 --dataset-path {dataset_path} \
# --model models/ssd_mobilenet_v1_coco_2018_01_28.onnx'.format(dataset_path=os.path.join(dataset_folder, 'coco-300')),
    # './run_local.sh onnxruntime ssd-resnet34 cpu --outputs detection_bboxes:0,detection_scores:0,detection_classes:0 --dataset-path {dataset_path} --model models/ssd_resnet34_mAP_20.2.onnx --inputs image:0'.format(dataset_path=os.path.join(dataset_folder, 'coco-1200'))
]

command_list = []

# scenarios = ['Offline', 'SingleStream', 'MultiStream', 'Server'];
scenarios = ['Offline']

# thread_counts = [1, 2, 4, 12]
thread_counts = [1]

# img_counts = [1, 2, 4, 8]
img_counts = [8]

num_samples = 4

'''
        subprocess.Popen([
        "echo \'{args_str}\' > {csv_path}; perf stat -x , -e {perf_events} -p {pid} -o {csv_path} --append".format(
            args_str=args_str, pid=os.getpid(), csv_path=perf_output_filename, perf_events=args.perf_events)], shell=True)'''

for perf_hw_event_set in perf_hw_event_sets:
    perf_event_str = perf_hw_event_set + ',' + perf_sw_events

    perf_command = 'perf stat -I 100 -x , -D -1 -e {perf_events} --control fd:${ctl_fd}'.format(perf_events=perf_event_str, ctl_fd='{ctl_fd}')

    for sample in range(num_samples):
        for scenario in scenarios:
            for threads in thread_counts:
                for count in img_counts:
                    for base_command in base_commands:

                        common_args = '--scenario {scenario} --threads {threads} --count {count} --perf-enable-fifo {perf_ctl_fifo}'.format(scenario=scenario, threads=threads, count=count, perf_ctl_fifo = perf_ctl_fifo_path)
                        command = base_command + ' ' + common_args
                        print(command)
                        command_list.append({'MLPerf_command': command, 'perf_command': perf_command, 'env_vars': env_vars, 'args': {'sample': sample, 'scenario': scenario, 'threads': threads, 'img_count': count, 'base_command': base_command}})

random.shuffle(command_list)

print(command_list)

index_list = []

setup = '''
#!/bin/bash
ctl_dir=/tmp/
ctl_fifo=${ctl_dir}perf_ctl.fifo

test -p ${ctl_fifo} && unlink ${ctl_fifo}
mkfifo ${ctl_fifo}
exec {ctl_fd}<>${ctl_fifo}
'''

launch_perf = '''
perf stat -D -1 -e cpu-cycles -a -I 100       \
          --control fd:${ctl_fd} -o out_python.log \
          -- &
perf_pid=$!
echo "perf_pid:${perf_pid}"
'''.format(ctl_fd='{ctl_fd}', perf_pid='{perf_pid}')

enable_perf = '''
echo 'enable' >&${ctl_fd}
'''

disable_perf = '''
echo 'disable' >&${ctl_fd}
'''

cleanup = '''
exec {ctl_fd}>&-
unlink ${ctl_fifo}

wait -n ${perf_pid}
exit $?
'''

for entry in command_list:
    perf_output_filename = os.path.join(perf_output_dir, str(time.time_ns()))

    index_row = {'perf_output_filename': perf_output_filename}
    index_row.update(entry['args'])

    index_list.append(index_row)

    df = pd.DataFrame.from_dict(index_list)
    print(df)
    df.to_csv(index_filename)

    entry['perf_command'] = entry['perf_command'] + ' -o {}'.format(perf_output_filename)



    

    process = subprocess.Popen('/bin/bash', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    process.stdin.write(setup.encode('utf-8'))
    process.stdin.flush()
    print(setup)

    process.stdin.write(disable_perf.encode('utf-8'))
    process.stdin.flush()
    print(disable_perf)

    # entry['perf_command'] = entry['perf_command'] + ' --control fd:${ctl_fd}'

    subprocess_cmd = '{env_vars} {perf_command} -- {mlperf_command}'.format(env_vars=entry['env_vars'], perf_command=entry['perf_command'], mlperf_command=entry['MLPerf_command'])

    print(subprocess_cmd)

    # subprocess.Popen(subprocess_cmd, shell=True).wait()

    process.stdin.write(subprocess_cmd.encode('utf-8'))
    process.stdin.flush()

    a, b = process.communicate()
