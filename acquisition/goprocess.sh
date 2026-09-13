#!/bin/bash

cd /data
gzip *mat
mkdir -p donetw
rm -f /data/donetw/*.bin  # processed data were moved to /data/donetw

# OP setup
export OP=0
echo $OP

# local
export remote=0
export ranging=0
export codenum=1     # LTFB -> LTFB loopback ; codenum starts at 1
echo $code
octave-cli -q /data/new/claudio_aligned_code_separate.m &

# remote OP1
export remote=1
export ranging=0
export codenum=2     # OP1 -> LTFB remote
octave-cli -q /data/new/claudio_aligned_code_separate.m &

# remote OP2
export remote=1
export ranging=0
export codenum=3     # OP2 -> LTFB remote
octave-cli -q /data/new/claudio_aligned_code_separate.m &

# ranging
export remote=1
export ranging=1
export codenum=1     # LTFB -> LTFB ranging
octave-cli -q /data/new/claudio_aligned_code_separate.m &
