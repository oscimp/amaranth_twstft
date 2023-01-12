mat files: recording hour followed by interpolation factor Nint (sample rate fs=5MHz oversampled to (2xNint+1))

UME = SATRE code 19 (Turkey)

OP  = SATRE code 0 (France OP)

SDR = Zynq/X310 custom emission

process_OP.m: processes raw .bin file (2 channels, interleaved short integers) to .mat file

analysis.m: analysis .mat files. Uncomment UME, OP or SDR in the beginning to select which dataset to process
