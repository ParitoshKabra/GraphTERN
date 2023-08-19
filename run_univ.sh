#!/bin/bash
#SBATCH -N 2
#SBATCH --ntasks-per-node=1
#SBATCH --error=univ.err
#SBATCH --output=univ.out
#SBATCH --time=24:00:00
#SBATCH --partition=gpu
#SBATCH --gres=gpu:2
activate(){
source /home/paritosh_k.iitr/lbp8/bin/activate
}
activate
module load DL-CondaPy/3.7
module load gcc/10.2.0
# ./scripts/train.sh -d "eth hotel zara1 zara2 univ"
./scripts/train1.sh -d "univ" -i "0"

