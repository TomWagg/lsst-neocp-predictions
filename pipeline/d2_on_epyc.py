from multiprocessing import Pool
import subprocess
import sys
sys.path.append("../src")
import digest2

def create_bash_script(night, out_path="neo/",
                       digest2_path="/data/epyc/projects/hybrid-sso-catalogs/digest2/", cpu_count=32):
    bash = f"NIGHT={night:04d}\n"
    bash += 'echo "Now running night $NIGHT through digest2..."\n'
    bash += f"time {digest2_path}digest2 -p {digest2_path} -c {digest2_path}MPC.config --cpu {cpu_count}"
    bash += f" {out_path}night_$NIGHT.obs > {out_path}night_$NIGHT.dat" + "\n"
    bash += f"grep -a -v tracklet {out_path}night_$NIGHT.dat > {out_path}night_$NIGHT.filtered.dat \n"
    return bash

def run(night):
    in_path = '/epyc/projects/neocp-predictions/output/synthetic_obs/'
    out_path = '/epyc/projects/neocp-predictions/output/digest2_output/'
    digest2_path = '/epyc/projects/neocp-predictions/digest2/'
    digest2.create_digest2_input(night=night, in_path=in_path, out_path=out_path)

    script = create_bash_script(out_path=out_path, night=night,
                                digest2_path=digest2_path, cpu_count=1)
    subprocess.call(script, shell=True)

if __name__ == "__main__":
    nights = range(366)
    # nights = np.load("/epyc/projects/neocp-predictions/output/ten_year_target_nights.npy", allow_pickle=True)

    with Pool(30) as p:
        p.map(run, nights)
