// compile with
// gcc -Wall -o mseq_calculator mseq_calculator.c
// run with
// for i in `seq 0 100`; do ./mseq_calculator 17 $i;done | grep OK
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>

uint32_t lfsr_next(uint32_t lfsr, uint32_t taps, int bits) {
    uint32_t bit = 0;
    uint32_t masked = lfsr & taps;

    for (int i = 0; i < bits; i++) { // XOR all tapped bits
        bit ^= (masked >> i) & 1;
    }
    lfsr = (lfsr >> 1) | (bit << (bits - 1));
    return lfsr;
}

int main(int argc, char **argv) {
    int bits;
    uint32_t seed, taps, length;
    int max_length, filewrite=0, f;
    char *sequence, name[256];

    if (argc>1) bits=atoi(argv[1]); else bits=17;
    if (argc>2) taps=atoi(argv[2]); else taps=9;
    if (argc>3) length=atoi(argv[3]); else length=100000;
    if (argc>4) filewrite=1;
    seed=1;

    sequence=(char*)malloc(length);
    uint32_t lfsr=seed,n=0;
    max_length = (1 << bits) - 1;
    while (1) {
        // print_bits(lfsr, bits);
	if (n<length) sequence[n]=(lfsr & 1);
        lfsr = lfsr_next(lfsr, taps, bits);
        n++;
        if ((lfsr==seed)||(lfsr==0))  break;
    }
    printf("%d %d\t-> %d/%d",bits,taps,n,max_length);
    if (n==max_length) printf(" OK\n"); else printf("\n");
    if (filewrite==1)
       {sprintf(name,"noiselen%d_bitlen%d_taps%d.bin", length, bits, taps);
        f=open(name, O_WRONLY | O_CREAT | O_EXCL, S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH);
        write(f,sequence,length);
        close(f);
       }
    return 0;
}

