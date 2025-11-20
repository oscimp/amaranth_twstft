#!/bin/bash

rep=${processing_dir:='/data/'}  # assign if processing_dir is defined, default otherwise

cd ${rep}
mkdir -p donetw                         # create storage dir if not existing
gzip *mat
rm -f ${rep}/donetw/*.bin               # remove data processed during previous call
octave -q ${rep}/claudio_aligned_code_ranging_separate.m &
octave -q ${rep}/claudio_aligned_code_lo_separate.m &
octave -q ${rep}/claudio_aligned_code_re_separate.m &
