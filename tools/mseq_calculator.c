// compile with
// gcc -Wall -o mseq_calculator mseq_calculator.c
// run with
// for i in `seq 0 100`; do ./mseq_calculator 17 $i;done | grep OK
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

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
    uint32_t seed, taps;
    int max_length;

    if (argc>1) bits=atoi(argv[1]); else bits=17;
    if (argc>1) taps=atoi(argv[2]); else taps=9;
    seed=1;

    uint32_t lfsr=seed,n=0;
    max_length = (1 << bits) - 1;
    while (1) {
        // print_bits(lfsr, bits);
        lfsr = lfsr_next(lfsr, taps, bits);
        n++;
        if ((lfsr==seed)||(lfsr==0))  break;
    }
    printf("%d %d\t-> %d/%d",bits,taps,n,max_length);
    if (n==max_length) printf(" OK\n"); else printf("\n");

    return 0;
}

