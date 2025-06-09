#!/bin/bash

cd /data
gzip *mat
rm -f /data/donetw/*.bin
# scp -r *mat.gz 65.21.30.42:/tmp/ltfb
# octave -q /data/claudio_aligned_code_re.m &
octave -q /data/claudio_aligned_code_ranging_separate.m &
octave -q /data/claudio_aligned_code_lo_separate.m &
octave -q /data/claudio_aligned_code_re_separate.m &
