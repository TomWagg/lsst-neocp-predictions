#!/bin/bash
## Job Name
#SBATCH --job-name=self_follow_up
#SBATCH --account=astro-ckpt
#SBATCH --partition=ckpt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=28
#SBATCH --time=0:20:00
#SBATCH --mem=50G
#SBATCH -o /gscratch/dirac/tomwagg/neocp-predictions/slurm/logs/sfu_logs_%a_%A.out
#SBATCH -e /gscratch/dirac/tomwagg/neocp-predictions/slurm/logs/sfu_logs_%a_%A.err
#SBATCH --chdir=/gscratch/dirac/tomwagg/neocp-predictions/pipeline
#SBATCH --mail-type=ALL
#SBATCH --mail-user=tomwagg@uw.edu
#SBATCH --export=all

source ~/.bashrc
conda activate neocp-fixed

SCRIPT_PATH=/gscratch/dirac/tomwagg/neocp-predictions/pipeline/mitigation.py
IN_PATH=/gscratch/dirac/tomwagg/neocp-predictions/output/synthetic_obs
OUT_PATH=/gscratch/dirac/tomwagg/neocp-predictions/output/mitigation_results
FOV_PATH=/gscratch/dirac/tomwagg/fov_map.npz

python $SCRIPT_PATH -s $SLURM_ARRAY_TASK_ID -i $IN_PATH -o $OUT_PATH -f $FOV_PATH -p 28 -S