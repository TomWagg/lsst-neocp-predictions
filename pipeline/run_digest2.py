import argparse
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


def main():
    parser = argparse.ArgumentParser(description='Run digest2 on LSST mock observations')
    parser.add_argument('-i', '--in-path', default="", type=str,
                        help='Path to the folder containing mock observations')
    parser.add_argument('-o', '--out-path', default="neo/", type=str,
                        help='Path to folder in which to place output')
    parser.add_argument('-d', '--digest2-path', default="/data/epyc/projects/hybrid-sso-catalogs/digest2/",
                        type=str, help='Path to digest2 folder')
    parser.add_argument('-n', '--night', default=0, type=int,
                        help='Night to run through digest2')
    parser.add_argument('-c', '--cpu-count', default=32, type=int,
                        help='How many CPUs to use for the digest2 calculations')
    args = parser.parse_args()

    print(f"Creating digest2 files for night {args.night} in {args.out_path}")

    digest2.create_digest2_input(night=args.night, in_path=args.in_path, out_path=args.out_path)

    script = create_bash_script(in_path=args.in_path, out_path=args.out_path, night=args.night,
                                digest2_path=args.digest2_path, cpu_count=args.cpu_count)
    subprocess.call(script, shell=True)
    print("Hurrah!")


if __name__ == "__main__":
    main()
