import os
import subprocess
import random

dataset_folder = 'data'
models_folder = 'models'

perf_sw_events = 'task-clock,context-switches,cpu-migrations,page-faults'

perf_hw_event_sets = [
    'cycles,cache-references,cache-misses',
    'instructions,branches,branch-misses',
    'L1-dcache-loads,L1-dcache-load-misses,dTLB-load-misses,dtlb_load_misses.miss_causes_a_walk'
]

base_commands = [
    './run_local.sh onnxruntime resnet50 cpu --dataset-path data/imagenet/'.format(os.path.join(dataset_folder, 'imagenet')),
    './run_local.sh cpu --profile ssd-mobilenet-onnxruntime --dataset coco-300 --dataset-path {dataset_path} \
--model models/ssd_mobilenet_v1_coco_2018_01_28.onnx'.format(dataset_path=os.path.join(dataset_folder, 'coco-300')),
    './run_local.sh onnxruntime ssd-resnet34 cpu --dataset-path {dataset_path}'.format(dataset_path=os.path.join(dataset_folder, 'coco-1200'))
]

command_list = []

# scenarios = ['Offline', 'SingleStream', 'MultiStream', 'Server'];
scenarios = ['Offline']

# thread_counts = [1, 2, 4, 12]
thread_counts = [1]

# img_counts = [1, 2, 4, 8]
img_counts = [8]

num_samples = 4

for perf_hw_event_set in perf_hw_event_sets:
    perf_event_str = perf_hw_event_set + ',' + perf_sw_events
    for sample in range(num_samples):
        for scenario in scenarios:
            for threads in thread_counts:
                for count in img_counts:
                    for base_command in base_commands:
                        common_args = '--scenario {scenario} --threads {threads} --count {count} --perf-events \
{perf_event_str}'.format(scenario=scenario, threads=threads, count=count, perf_event_str=perf_event_str)
                        command = base_command + ' ' + common_args
                        print(command)
                        command_list.append(command)

random.shuffle(command_list)

for command in command_list:

    subprocess.Popen(args=[command], shell=True).wait()