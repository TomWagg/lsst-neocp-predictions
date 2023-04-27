#!/bin/bash
## Job Name
#SBATCH --job-name=self_follow_up
#SBATCH --account=astro-ckpt
#SBATCH --partition=ckpt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=6:00:00
#SBATCH --mem=50G
#SBATCH -o /gscratch/dirac/tomwagg/difi_slurm/logs/sfu_logs_%a_%A.out
#SBATCH --chdir=/gscratch/dirac/tomwagg/the-sky-is-falling/mitigation_algorithm
#SBATCH --mail-type=ALL
#SBATCH --mail-user=tomwagg@uw.edu
#SBATCH --export=all

source ~/.bashrc
conda activate /gscratch/dirac/tomwagg/neocp-fixed

SCRIPT_PATH=/gscratch/dirac/tomwagg/the-sky-is-falling/mitigation_algorithm/detection_probability.py
IN_PATH=/gscratch/dirac/tomwagg/the-sky-is-falling/current_criteria
OUT_PATH=/gscratch/dirac/tomwagg/the-sky-is-falling/mitigation_algorithm/latest_runs
FOV_PATH=/gscratch/dirac/tomwagg/fov_map.npz

python $SCRIPT_PATH -s $SLURM_ARRAY_TASK_ID -i $IN_PATH -o $OUT_PATH -f $FOV_PATH -p 28 -t mba -S