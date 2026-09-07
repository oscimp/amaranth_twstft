#!/bin/bash

rep=${processing_dir:='/data/'}  # assign if processing_dir is defined, default otherwise

cd ${rep}
mkdir -p donetw                         # create storage dir if not existing
gzip *mat
rm -f ${rep}/donetw/*.bin               # remove data processed during previous call
octave -q ${rep}/claudio_aligned_code_lo_separate.m &
# remotechannel=1 implicitly, 2 for loopback ^^
OP=1 sic=0 codenum=2 octave -q ${rep}/claudio_aligned_code_re_separate.m & # ranging
OP=1 sic=0 codenum=1 octave -q ${rep}/claudio_aligned_code_re_separate.m & # LTFB
