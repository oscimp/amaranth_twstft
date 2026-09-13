#!/bin/bash

cd /data
gzip *mat
mkdir -p donetw
rm -f /data/donetw/*.bin  # processed data were moved to /data/donetw

# OP setup
export OP=1
echo $OP

# local
export remote=0
export ranging=0
export codenum=2     # OP -> OP loopback
echo $code
octave-cli -q /data/new/claudio_aligned_code_separate.m &

# remote
export remote=1
export ranging=0
export codenum=1     # LTFB -> OP remote
octave-cli -q /data/new/claudio_aligned_code_separate.m &

# ranging
export remote=1
export ranging=1
export codenum=2     # OP -> OP ranging
octave-cli -q /data/new/claudio_aligned_code_separate.m &
