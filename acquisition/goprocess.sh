#!/bin/bash

rep='/data/'

cd ${rep}
gzip *mat
rm -f ${rep}/donetw/*.bin
# scp -r *mat.gz 65.21.30.42:/tmp/ltfb
# octave -q ${rep}/claudio_aligned_code_re.m &
octave -q ${rep}/claudio_aligned_code_ranging_separate.m &
octave -q ${rep}/claudio_aligned_code_lo_separate.m &
octave -q ${rep}/claudio_aligned_code_re_separate.m &
