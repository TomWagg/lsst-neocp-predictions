#!/bin/bash
#SBATCH --job-name=digest2
#SBATCH --account=astro-ckpt
#SBATCH --partition=ckpt
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=28
#SBATCH --time=0:10:00
#SBATCH --mem=10G
#SBATCH -o /gscratch/dirac/tomwagg/neocp-predictions/slurm/digest_logs_%a_%A.out
#SBATCH --chdir=/gscratch/dirac/tomwagg/neocp-predictions/pipeline/
#SBATCH --mail-type=ALL
#SBATCH --mail-user=tomwagg@uw.edu
#SBATCH --export=all

source ~/.bashrc
conda activate /gscratch/dirac/tomwagg/anaconda3/envs/neocp-fixed

SCRIPT_PATH=/gscratch/dirac/tomwagg/neocp-predictions/pipeline/run_digest2.py
IN_PATH=/gscratch/dirac/tomwagg/neocp-predictions/output/synthetic_obs/
OUT_PATH=/gscratch/dirac/tomwagg/neocp-predictions/output/digest2_output/
DIGEST2_PATH=/gscratch/dirac/tomwagg/hybrid_sso_catalogue/digest2/

python $SCRIPT_PATH -i $IN_PATH -o $OUT_PATH -d $DIGEST2_PATH -c 28 -n $SLURM_ARRAY_TASK_ID