// g++ -o rx rx.cpp -L/usr/local/lib -lfftw3 -lgsl -lopenblas
// ./rx data.bin

/*
 * The two-way satellite time and frequency transfer software-defined radio receiver
 * Author: Yi-Jiun Huang, J.-M Friedt
 * Usage: ./rxcomplex
 * Usage: ./rxcomplex ../result
 */
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <time.h>
#include <sys/time.h>
#include <gsl/gsl_fit.h>
#include <pthread.h>

#include <cstring>
#include <fftw3.h>
#include <cblas.h>

#include <iostream>
#include <fstream>
#include <csignal>
#include <complex>
#include <fcntl.h>
#include <unistd.h>

#define Ninterp 2 // keep power of two for FFT to remain power of 2
//
#define PI 3.141592653589793
#define MAXBUF 1
#define USRP 310
//
const int sps =  5000000*Ninterp; // NI USRP X310
const int nch_max = 120;    // maximum receiver channels
//
typedef struct _timetag
{
  int mjd;
  int year;
  int doy;
  int month;
  int day;
  int sod;  // second of day
  int hour;
  int minute;
  int second;
  double fsec; // frantional sec
} timetag;
//
typedef struct _samplebuffer
{
  bool is_tt;
  int idx;
  time_t tt, bt;
  double ft;
#if USRP == 310
  short *buf; // NI USRP X310
#elif USRP == 210
  char *buf; // NI USRP N210
#endif
} samplebuffer;
//
typedef struct _channel_info // parameters
{
  bool is_first;  // 0x1 = first track; 0x0 = not first track
  bool is_trk;    // 0x1 = being tracked; 0x0 = no signal
  bool is_sic;    // 0x1 = SIC enable; 0x0 = SIC disable
  bool is_chA;    // 0x1 = ch. A; 0x0 = ch. B
  char ch[80];    // physical channel identifier, e.g. "A" or "B" for NI USRP Basic Rx daughter board
  char code_type[10];
  int cid;        // code identifier
  int rc;         // number of chip per second (chips)
  int pt_prev;
  int pt;         // coarse code head position (samples)
  int clen;       // number of chip per code length
  int ib;         // which code is the beginning?
  double fc_init; // initial central frequency from parameter file (Hz)
  double fc_prev;
  double fc;      // carrier freq. (Hz)
  double df;
  double gd;      // code phase (ns)
  double sdgd;    // code phase standard deviation (ns)
  double dg;      // code phase rate (ns/s)
  double phi;     // carrier phase (cycle)
  double last_phi;// last carrier phase (cycle)
  double pk;      // signal power (V^2)
  double psbb;    // baseband power of locally generated code waveform (V^2)
  double px;      // received power (V^2)
  double fltmin;  // negative cut-off frequency of the low-pass filter (Hz)
  double fltmax;  // positive cut-off frequency of the low-pass filter (Hz)
  double range;   // acquisition frequency range (Hz)
  double step;    // acquisition frequency step (Hz)
  double snr_min; // minimum required SNR (ratio)
  int bps;        // number of codes per second
  double duration;  // code length (s)
  int nlag;       // maximum delay spread (+-samples)
  int nobs;       // number of samples in a code period
  int nfft;       // number of samples in a code period for acquisition
  // required host and device memories
  int *host_code;    // code sequence {-1, 0, 1}
  int *dev_code;     // code sequence {-1, 0, 1} on GPU memory
  std::complex<double> *dev_smp;   // received waveform on GPU memory, values in Volt
  double *dev_wav;   // time-domain filterd code waveform of nlag periods on GPU memory, values in Volt
  double *dev_res;   // IQ correlation results for each channel, dev_res[i] = TRANS(dev_obs) * dev_wav[i]
  double *host_cor;  // correlation result, 0.5 * (amp * Psbb)^2
  double *dev_cor;   // correlation result, 0.5 * (amp * Psbb)^2 on GPU memory
  double *host_phi;  // carrier phase
  double *dev_phi;   // carrier phase on GPU memory
  double *res;

  std::complex<double> *dev_wav_t;    // time-domain code waveform
  std::complex<double> *dev_wav_acq;  // frequency domain samples for acquisition (from double-length time-domain code waveform with zero padding)
  std::complex<double> *dev_obs_acq;
  // correlation results of each duration
  FILE *fout;
  int cnt;        // number of available signal time of arrival (TOA) measurements per second
  double *ttag_gd;  // time stamp of the TOA measurements (s)
  double *res_gd;   // TOA measurements (ns)
  int *pk_idx;
  double *ttag_phi; // time stamp of the carrier phase (s)
  double *res_phi;  // carrier phase in which fc*dt has been removed (cycle)
  double *raw_phi;  // raw carrier phase (cycle)
  double *res_amp;  // signal amplitude (V)
  int *dev_pk_idx;
  double *dev_raw_phi;  // raw carrier phase (cycle)
  double *dev_res_amp;  // signal amplitude (V)
  double *w;        // weight of each measurement, 1 = usable; 0 = useless
  double *ps;       // pass-band signal power, 0.5 * amp^2 * Psbb (V^2)
} channel_info;
//
typedef struct _system_info
{
  int nch_max;  // maximum number of receiver channels
  int nch;      // number of channels
  int dec;      // decimation factor
  int dec_a;    // additional decimation factor at ACQ stage
  int sps;      // number of samples per second after decimation
  double fs;    // sampling frequency after decimation (Hz)
} system_info;
//
// function prototypes
int SDRcode(channel_info *);
double average(int, double *, double *);
double kth_smallest(double *, int, int);
void current_time(int, int *, int *, int *, int *, int *, int *, int *, int *);
void date2doy(int , int, int, int *);
void doy2date(int, int, int *, int *);
int date2mjd(int, int, int);
void mjd2date(int, int *, int *, int *);
int doy2mjd(int, int);
void mjd2doy(int, int *, int *);
double v2todBm(double);
void *sampling(void *);
int is_sync_NTP(void);
//

void memcpy_acq(int, std::complex<double> *, std::complex<double> *, int);
void char2double(int, int, char *, std::complex<double>*, std::complex<double>*);
void short2double(int, int, short *, std::complex<double>*, std::complex<double>*);
void PRN_sampling(int, int *, std::complex<double> *, int, double, int, double);
void PRN_mapping(int, int, int, std::complex<double> *, double *);
void downconv_acq(int, double, double, std::complex<double> *, std::complex<double> *, int);
void downconv_trk(int, int, double, double, std::complex<double> *, double *);
void get_cor_and_phi(int, int, double *, double *, double *);
void cross_spectrum(int, std::complex<double> *, std::complex<double> *, double, double, double, std::complex<double> *);
void lowpass(int, std::complex<double> *, double, double, double);
void MAI_up(int, int, int, double *, std::complex<double> *, int *, double, double *, double *);
void MAI_out(int, double *, double *); // JMF MAI = Multiple Access Interference
//
int main(int argc, char *argv[])
{
  // check input arguments
  if (argc!=1 && argc != 2 && argc != 3)
  {
    printf("usage:\n");
    printf("%s out_path param_file\n",argv[0]);
    return 1;
  }
  // variables
  FILE *fparam, *flog;
  system_info si;
  channel_info *ci;
  fftw_plan plan1, plan2, plan3, plan4, plan5;
  char str[200], str2[200], filename[80], paramfile[80]="sdr.param", ch[2], id[2], *pch;
  double c0, c1, stddev, pk, c00, c01, c11;
  double fcc, frange, fstep, flow, fhigh, phi;
  int i, k, p, pk_idx, kjmf;
  int ii, idx, pn, kcps;
  double snr_min, fc_init, fltkhz;
  bool is_chA, is_sic;
  double alpha, beta = 0.0;
  std::complex<double> pwr_A, pwr_B;
  double *dev_obs;
  std::complex<double> *dev_smp_A, *dev_smp_B; // JMF: float* -> complex*
//  double *dev_smp_MAI_free; 
  // gsl_matrix_view A, B, C;
  char datafilename[256]; // 
#if USRP == 310
  short *dev_samples; // NI USRP X310
#elif USRP == 210
  char *dev_samples; // NI USRP N210
#endif

  //
  if (argc > 1)
     sprintf(datafilename,"%s",argv[1]);
  else
     sprintf(datafilename,"./data.bin");
  printf("%s\n",datafilename);

  if (argc > 2)
     sprintf(paramfile,"%s",argv[2]);
  if ((fparam = fopen(paramfile, "r")) == NULL)
  {
    printf("no such parameter file : %s\n", paramfile);
    return 1;
  }
  else
    fclose(fparam);
  // assign system parameters
#if USRP == 310
  //si.dec = 4;   // speed down overall, e.g. 200 Msps / 4 = 50 Msps
  //si.dec_a = 2; // speed down for ACQ, e.g.  50 Msps / 2 = 25 Msps
  si.dec = 1;  
  si.dec_a = 1;
#elif USRP == 210
  si.dec = 1;
  si.dec_a = 2;
#endif
  si.nch_max = nch_max;
  ci = (channel_info *)malloc(sizeof(channel_info) * si.nch_max);
  for (i = 0; i < si.nch_max; i++)
    ci[i].nobs = 0;
  si.sps = sps / si.dec;
  si.nch = -1;
  si.fs = (double)(sps / si.dec);
  // random pick-up for ACQ
  srand(time(NULL));
  // initialize the buffer of samples
#if USRP == 310
  dev_samples=(short*)malloc(sizeof(short) * sps * 4); // NI USRP X310 JMF 2 for complex 2 for interleaved chans
#elif USRP == 210
  dev_samples=(char*)malloc(sizeof(char) * sps * 4); // NI USRP N210
#endif
  dev_obs=(double*)malloc(sizeof(double) * si.sps * 2);   // JMF : real and imag
  dev_smp_A=(std::complex<double>*)malloc(sizeof(std::complex<double>) * si.sps);
  dev_smp_B=(std::complex<double>*)malloc(sizeof(std::complex<double>) * si.sps);
//  dev_smp_MAI_free=(double*)malloc(sizeof(double) * si.sps);

  FILE *fd;
  int datares;                 // JMFfile
  fd=fopen(datafilename,"rb"); // JMFfile
  if (fd==NULL) {printf("Data filename error\n");return(1);}

  // Start: set new parameters
  if (si.nch == -1)
  {
    if ((fparam = fopen(paramfile, "r")) != NULL)
    {
      i = 0;
      while (fgets(str, 200, fparam))
      {
        if (str[0] == '#')
          continue;
        strcpy(str2, str);
        k = 0;
			    pch = (char *)strtok(str2, " ;\r\n");
			    if (pch != NULL) k++;
			    while ((pch = (char *)strtok(NULL, " ;\r\n")) != NULL) k++;
        if ((str[0] == 'A' || str[0] == 'B') && (str[2] == 'N' || str[2] == 'S') && k == 9)
        {
          if (str[0] == 'A') is_chA = 0x1; // physical channel A of USRP
          else               is_chA = 0x0; // physical channel B of USRP
          if (str[2] == 'S') is_sic = 0x1; // enable SIC
          else               is_sic = 0x0; // normal tracking
          sscanf(str, "%s %s %d %lf %d %lf %lf %lf %lf", ch, id, &pn, &fc_init, &kcps, &fltkhz, &frange, &fstep, &snr_min);
          if (ci[i].is_chA == is_chA && ci[i].is_sic == is_sic && ci[i].cid == pn && ci[i].fc_init == fc_init && ci[i].rc == kcps * 1000 && ci[i].range >= frange && ci[i].range < frange * 2.0 && ci[i].step >= fstep && ci[i].step < fstep * 2.0 && fabs(ci[i].snr_min - pow(10.0, snr_min / 10.0)) < 0.1 * ci[i].snr_min)
          {
            i++;
            if (i < si.nch_max) continue;
            else break;
          }
          else if (pn >= 0 && ((pn <= 131 && kcps == 2500)) && fc_init >= -200000. && fc_init < 200000. && frange >= 0.0 && frange < 200000. && frange > fstep && snr_min > -100.0)
          {
            ci[i].is_chA = is_chA;
            ci[i].is_sic = is_sic;
            // assign channel-dependent parameters
            if (is_chA == 0x1) sprintf(ci[i].ch, "%s", "A");
            else               sprintf(ci[i].ch, "%s", "B");
            //
            ci[i].rc = kcps * 1000;
            ci[i].nlag = 8; // it should depends on SNR ...
            sprintf(ci[i].code_type, "SDR"); // it can be assigned from the parameter file ...
            // obtain code length
            if (strcmp(ci[i].code_type, "SDR") == 0)
            {
              if (ci[i].rc == 2500000)
              {
               if (pn<100) {
                ci[i].clen = 10000;
                ci[i].duration = 0.004; // 250 bits per second, 4 ms bit duration
                ci[i].nlag = 14;
               }
               else // SDR JMF
               {
                ci[i].clen = 100000;
                ci[i].duration = 0.04; // 25 bits per second, 40 ms bit duration
                ci[i].nlag = 28; // lag search JMF
               }
              }
              else
              {
                printf("code rate error: %d\n", ci[i].rc);
                i++;
                if (i < si.nch_max) continue;
                else break;
              }
            }
             else
             {
              printf("code type error: %s", ci[i].code_type);
              i++;
              if (i < si.nch_max) continue;
              else break;
             }
            // free the memory if previously allocated
            if (ci[i].nobs != 0)
            {
              free(ci[i].host_cor);
              free(ci[i].host_phi);
              free(ci[i].host_code);
              free(ci[i].res_gd);
              free(ci[i].ttag_gd);
              free(ci[i].pk_idx);
              free(ci[i].res_phi);
              free(ci[i].raw_phi);
              free(ci[i].res_amp);
              free(ci[i].ttag_phi);
              free(ci[i].ps);
              free(ci[i].w);
              free(ci[i].res);

              free(ci[i].dev_res);
              free(ci[i].dev_cor);
              free(ci[i].dev_phi);
              free(ci[i].dev_wav_t);
              free(ci[i].dev_wav_acq);
              free(ci[i].dev_obs_acq);
              free(ci[i].dev_wav);
              free(ci[i].dev_code);
              free(ci[i].dev_pk_idx);
              free(ci[i].dev_raw_phi);
              free(ci[i].dev_res_amp);

            }
            // assign new values
            ci[i].bps = ci[i].rc / ci[i].clen;
            ci[i].nobs = si.sps / ci[i].bps;
            ci[i].cid = pn;
            ci[i].fc_init = fc_init;
            ci[i].fltmax = (double)ci[i].rc;
            ci[i].fltmin = -ci[i].fltmax;
            ci[i].nfft = 1;
            while (1)
            {
              ci[i].nfft *= 2;
              if (ci[i].nfft > ci[i].nobs * 2 / si.dec_a) break;
            }
            ci[i].range = 1.0;
            while (ci[i].range < frange) ci[i].range *= 2.0;
            ci[i].step = 1.0;
            while (ci[i].step < fstep) ci[i].step *= 2.0;
            ci[i].snr_min = pow(10.0, snr_min / 10.0); // convert dB to ratio
            // Start: reset flags
            ci[i].is_trk = 0x0;
            ci[i].is_first = 0x0;
            ci[i].df = 0.0;
            ci[i].last_phi = 0.0;
            // End: reset flags
            // allocate memories
            ci[i].host_cor = (double *)malloc(sizeof(double) * (ci[i].nlag * 2 + 1) * (ci[i].bps - 1));
            ci[i].host_phi = (double *)malloc(sizeof(double) * (ci[i].nlag * 2 + 1) * (ci[i].bps - 1));

            ci[i].dev_wav=(double*)malloc( sizeof(double) * (ci[i].nlag * 2 + 1) * ci[i].nobs);
            ci[i].dev_res=(double*)malloc( sizeof(double) * (ci[i].nlag * 2 + 1) * (ci[i].bps - 1) * 2);
            ci[i].dev_cor=(double*)malloc( sizeof(double) * (ci[i].nlag * 2 + 1) * (ci[i].bps - 1));
            ci[i].dev_phi=(double*)malloc( sizeof(double) * (ci[i].nlag * 2 + 1) * (ci[i].bps - 1));
            ci[i].dev_res_amp=(double*)malloc( sizeof(double) * ci[i].bps);
            ci[i].dev_raw_phi=(double*)malloc(sizeof(double) * ci[i].bps);
            ci[i].dev_pk_idx=(int*)malloc(sizeof(int) * ci[i].bps);

            ci[i].host_code = (int *)malloc(sizeof(int) * ci[i].clen);
            ci[i].dev_code=(int*)malloc( sizeof(int) * ci[i].clen);
            ci[i].dev_wav_t=(std::complex<double>*)malloc(sizeof(std::complex<double>) * ci[i].nobs);
            ci[i].dev_wav_acq=(std::complex<double>*)malloc( sizeof(std::complex<double>) * ci[i].nfft);
            ci[i].dev_obs_acq=(std::complex<double>*)malloc( sizeof(std::complex<double>) * ci[i].nfft);
            ci[i].res_gd   = (double *)malloc(sizeof(double) * ci[i].bps);
            ci[i].res_phi  = (double *)malloc(sizeof(double) * ci[i].bps);
            ci[i].raw_phi  = (double *)malloc(sizeof(double) * ci[i].bps);
            ci[i].res_amp  = (double *)malloc(sizeof(double) * ci[i].bps);
            ci[i].ttag_phi = (double *)malloc(sizeof(double) * ci[i].bps);
            ci[i].ps       = (double *)malloc(sizeof(double) * ci[i].bps);
            ci[i].w        = (double *)malloc(sizeof(double) * ci[i].bps);
            ci[i].res      = (double *)malloc(sizeof(double) * ci[i].bps);
            ci[i].pk_idx = (int *)malloc(sizeof(int) * ci[i].bps);
            ci[i].ttag_gd  = (double *)malloc(sizeof(double) * ci[i].bps);
            // assign time stamps for code phases
            for (p = 0; p < ci[i].bps; p++)
              ci[i].ttag_gd[p]  = (double)p * ci[i].duration;
            // generate code sequence
            SDRcode(&ci[i]);
            memcpy(ci[i].dev_code, ci[i].host_code, sizeof(int) * ci[i].clen );
            // sample the code sequence as the waveform
            PRN_sampling(ci[i].nobs, ci[i].dev_code, ci[i].dev_wav_t, ci[i].rc, si.fs, ci[i].clen, 0.0); // dev_wav_t[i].x = {1 , 0, -1}; dev_wav_t[i].y = 0
            // fill the values in dev_wav_acq for ACQ
            for (kjmf=0;kjmf<ci[i].nfft;kjmf++) {ci[i].dev_wav_acq[kjmf].real(0.);ci[i].dev_wav_acq[kjmf].imag(0.);}
//              memset(ci[i].dev_wav_acq, 0x0, sizeof(std::complex<double>) * ci[i].nfft);
            memcpy_acq(ci[i].nobs / si.dec_a, ci[i].dev_wav_t, ci[i].dev_wav_acq, si.dec_a);
            // filter the waveform
            plan1 = fftw_plan_dft_1d(ci[i].nobs, reinterpret_cast<fftw_complex*>(ci[i].dev_wav_t),reinterpret_cast<fftw_complex*>(ci[i].dev_wav_t),
                                      FFTW_FORWARD, FFTW_ESTIMATE);
            fftw_execute(plan1);
            lowpass(ci[i].nobs, ci[i].dev_wav_t, si.fs / (double)ci[i].nobs, ci[i].fltmax, ci[i].fltmin);
            plan2 = fftw_plan_dft_1d(ci[i].nobs, reinterpret_cast<fftw_complex*>(ci[i].dev_wav_t),reinterpret_cast<fftw_complex*>(ci[i].dev_wav_t),
                                      FFTW_BACKWARD, FFTW_ESTIMATE);
            fftw_execute(plan2);
            // fill the values in dev_wav for TRK
            PRN_mapping(ci[i].nobs * (ci[i].nlag * 2 + 1), ci[i].nobs, ci[i].nlag, ci[i].dev_wav_t, ci[i].dev_wav);
            // compute reference signal power in <V^2>
            ci[i].psbb=cblas_dznrm2(ci[i].nobs, ci[i].dev_wav_t, 1);
            ci[i].psbb = ci[i].psbb * ci[i].psbb / (double)ci[i].nobs;
            // convert to frequency domain for acquisition procedure
            plan3 = fftw_plan_dft_1d(ci[i].nfft, reinterpret_cast<fftw_complex*>(ci[i].dev_wav_acq),reinterpret_cast<fftw_complex*>(ci[i].dev_wav_acq),
                                      FFTW_FORWARD, FFTW_ESTIMATE);
            fftw_execute(plan3);
            // Start: LOG
            sprintf(filename, "rxcomplex.log");
            flog = fopen(filename, "a");
            fprintf(flog, "set param   : Ch. %s, PRN#%2d, %8.0lf %4d %5.0lf %5.0lf %5.0lf %3.0lf\n", ci[i].ch, (ci[i].is_sic == 0x0) ? ci[i].cid : ci[i].cid + 50, ci[i].fc_init, ci[i].rc / 1000, ci[i].fltmax * 1.0e-3, ci[i].range, ci[i].step, ci[i].snr_min);
            fclose(flog);
            // End: LOG
            i++;
            if (i < si.nch_max) continue;
            else break;
          }
        }
      }
      fclose(fparam);
      si.nch = i;
    }
    else
      printf("no such parameter file : %s\n", paramfile);
  }
  // End: set new parameters and refresh every 20 seconds

#ifdef FFTW_THREADS
        if (fftw_init_threads() == 0)
                throw std::runtime_error("fftw_init_threads_failed");

        fftw_plan_with_nthreads(FFTW_THREADS);
#endif

  // Start: infinite measurement
  do
  {
#if USRP == 310
    datares=fread(dev_samples, sizeof(short), sps*4/Ninterp, fd); // JMFfile: *2 for reference and measurement
#elif USRP == 210
    datares=fread(dev_samples, sizeof(char), sps*4/Ninterp, fd);  // JMFfile
#endif
    printf("read %d samples\n",datares);
    // Get samples from buffer
    // Compute received signal power of each sampler channel
#if USRP == 310
    short2double(si.sps, si.dec, dev_samples, dev_smp_A, dev_smp_B); // NI USRP X310 dev_samp_X complex + outputs Ninterp times input items
#elif USRP == 210
    char2double(si.sps, si.dec, dev_samples, dev_smp_A, dev_smp_B); // NI USRP N210
#endif
    pwr_A=cblas_zdotc(si.sps / si.dec_a, dev_smp_A, si.dec_a, dev_smp_A, si.dec_a);
    // pwr_A=gsl_blas_ddot( dev_smp_A, si.dec_a, dev_smp_A, si.dec_a); TODO
//    printf("pwr_A %lf %lf",pwr_A.real(),pwr_A.imag());fflush(stdout);
    pwr_A /= (si.fs / (double)si.dec_a); // ch. A received power in <V^2>
//    printf("pwr_A/fs %lf %lf\n",pwr_A.real(),pwr_A.imag());fflush(stdout);
    pwr_B=cblas_zdotc(si.sps / si.dec_a, dev_smp_B, si.dec_a, dev_smp_B, si.dec_a);
//    printf("pwr_B %lf %lf",pwr_B.real(),pwr_B.imag());fflush(stdout);
    pwr_B /= (si.fs / (double)si.dec_a); // ch. B received power in <V^2>
//    printf("pwr_B/fs %lf %lf\n",pwr_B.real(),pwr_B.imag());fflush(stdout);
    // Start: DSP
    for (i = 0; i < si.nch; i++)
    {
      // Start: assign channel-dependent parameters
      if (ci[i].is_chA == 0x1)
      {
        ci[i].dev_smp = dev_smp_A;
        ci[i].px = real(pwr_A);
      }
      else
      {
        ci[i].dev_smp = dev_smp_B;
        ci[i].px = real(pwr_B);
      }
      // End: assign channel-dependent parameters
      // Start: SIC
      if (ci[i].is_sic == 0x1)
      {
{printf("JMF ERROR: commented block\n");fflush(stdout);}
/*
        memset(dev_smp_MAI_free, 0x0, sizeof(double) * si.sps);
        for (k = 0; k < i; k++)
          if (ci[i].is_chA == ci[k].is_chA && ci[i].cid != ci[k].cid && ci[k].is_sic == 0x0 && ci[k].is_trk == 0x1 && ci[k].is_first == 0x0)
            MAI_up(si.sps, ci[k].nobs, ci[k].pt_prev, ci[k].dev_res_amp, ci[k].dev_wav_t, ci[k].dev_pk_idx, (ci[k].fc + ci[k].df) / si.fs, ci[k].dev_raw_phi, dev_smp_MAI_free);
        MAI_out(si.sps, ci[i].dev_smp, dev_smp_MAI_free);
        // EVALUATION: performance down?
        ci[i].px=cblas_zdotc(si.sps / si.dec_a, dev_smp_MAI_free, si.dec_a, dev_smp_MAI_free, si.dec_a);
        ci[i].px /= (si.fs / (double)si.dec_a); // received power in <V^2>
        // EVALUATION: performance down?
*/
      }
      // End: SIC
      // Start: acquisition
      if (ci[i].is_trk == 0x0)
      {
        ci[i].pk = 0.0;
        ci[i].fc = ci[i].fc_init;
        frange   = ci[i].range;
        fstep    = ci[i].step;
        idx      =  (rand() % ((si.sps - ci[i].nfft * si.dec_a) / ci[i].nobs)) * ci[i].nobs;
        while (1)
        {
          flow  = ci[i].fc - frange;
          fhigh = ci[i].fc + frange;
          for (fcc = flow; fcc <= fhigh; fcc += fstep)
          {
            // down conversion
            if (ci[i].is_sic == 0x1)
{printf("JMF ERROR: commented block\n");fflush(stdout);}
/*
              downconv_acq(ci[i].nfft, fcc / (si.fs / (double)si.dec_a), 0.0, dev_smp_MAI_free + idx, ci[i].dev_obs_acq, si.dec_a);
*/
            else
              downconv_acq(ci[i].nfft, fcc / (si.fs / (double)si.dec_a), 0.0, ci[i].dev_smp + idx, ci[i].dev_obs_acq, si.dec_a);
            plan4 = fftw_plan_dft_1d(ci[i].nfft, reinterpret_cast<fftw_complex*>(ci[i].dev_obs_acq),reinterpret_cast<fftw_complex*>(ci[i].dev_obs_acq),
                                        FFTW_FORWARD, FFTW_ESTIMATE);
            fftw_execute(plan4);
            // perform cross correlation
            cross_spectrum(ci[i].nfft, ci[i].dev_obs_acq, ci[i].dev_wav_acq, (si.fs / (double)si.dec_a) / (double)ci[i].nfft, ci[i].fltmax, ci[i].fltmin, ci[i].dev_obs_acq);
            plan5 = fftw_plan_dft_1d(ci[i].nfft, reinterpret_cast<fftw_complex*>(ci[i].dev_obs_acq),reinterpret_cast<fftw_complex*>(ci[i].dev_obs_acq),
                                        FFTW_BACKWARD, FFTW_ESTIMATE);
            fftw_execute(plan5);
            // find peak
            pk_idx=cblas_izamax(ci[i].nfft, ci[i].dev_obs_acq, 1);
            pk=cblas_dznrm2(1, ci[i].dev_obs_acq + (pk_idx ), 1);   // indice +1 semble coherent
            // find the highest peak value
            if (pk > ci[i].pk)
            {
// printf("max?: pk=%lf ci[i].pk=%lf %lf %lf %lf %lf %lf\n", pk, ci[i].pk, abs(*(ci[i].dev_obs_acq+pk_idx-2)), abs(*(ci[i].dev_obs_acq+pk_idx-1)),abs(*(ci[i].dev_obs_acq+pk_idx)),abs(*(ci[i].dev_obs_acq+pk_idx+1)), abs(*(ci[i].dev_obs_acq+pk_idx+2))); JMF check that *(ci[i].dev_obs_acq+pk_idx is indeed the max
              ci[i].fc = fcc;
              ci[i].pk = pk;
              ci[i].pt = (pk_idx ) % (ci[i].nobs / si.dec_a); // cublasIzamax() returns [1:nfft], but we want [0:nfft-1] mod nobs  JMF remove -1 from pk_idx - 1
            }
          }
          // update to a finer frequency for searching signal
          fstep = fstep / 2.0;
          frange = fstep;
          if (fstep < 1.0) break;
        }
        fftw_destroy_plan(plan5);   // cufftDestroy(plan);
        // get peak signal power in <V^2>
        ci[i].pk = 8.0 * ci[i].pk * ci[i].pk / ci[i].psbb;
        // say signal exists if SNR > SNR_min
        if ((1.0 + ci[i].snr_min) * ci[i].pk > ci[i].snr_min * ci[i].px)
        {
          ci[i].pt = ci[i].pt * si.dec_a;
          ci[i].gd = (double)ci[i].pt * 1.0e+9 / si.fs;
          ci[i].is_trk = 0x1;
          ci[i].is_first = 0x1;
          // Start: LOG
          sprintf(filename, "rxcomplex.log");
          flog = fopen(filename, "a");
          fprintf(flog, "acquisition : Ch. %s, PRN#%2d, %3d %8.0lf %7.0lf %6d %8.3lf %8.3lf\n", ci[i].ch, (ci[i].is_sic == 0x0) ? ci[i].cid : ci[i].cid + 50, idx / 2 / ci[i].nobs, ci[i].fc, ci[i].gd, ci[i].pt, v2todBm(ci[i].pk), v2todBm(ci[i].px));
          fclose(flog);
          // End: LOG
        }
      }
      // End: acquisition
      // Start: Tracking
      else
      {
        // Start: correlation
        alpha = 1.0 / (double)ci[i].nobs;
        phi = fmod((double)ci[i].pt * ci[i].fc / si.fs, 1.0);
        if (ci[i].is_sic == 0x1)
{printf("JMF ERROR: commented block\n");fflush(stdout);}
/*
          downconv_trk(ci[i].nobs * (ci[i].bps - 1), ci[i].nobs, ci[i].fc / si.fs, phi, dev_smp_MAI_free + ci[i].pt, dev_obs);
*/
        else
          downconv_trk(ci[i].nobs * (ci[i].bps - 1), ci[i].nobs, ci[i].fc / si.fs, phi, ci[i].dev_smp + ci[i].pt, dev_obs);
//        cublasDgemm(handle, CUBLAS_OP_T, CUBLAS_OP_N,      ci[i].nlag * 2 + 1, (ci[i].bps - 1) * 2, ci[i].nobs, &alpha, ci[i].dev_wav, ci[i].nobs, dev_obs, ci[i].nobs, &beta, ci[i].dev_res, ci[i].nlag * 2 + 1);
      
// ** On entry to DGEMM  parameter number 13 had an illegal value
// last arg ci[i].nlag * 2 + 1 < ci[i].nlag * 2 + 1 first after CUBLAS_OP_N
       cblas_dgemm(CblasColMajor, CblasTrans, CblasNoTrans, ci[i].nlag * 2 + 1, (ci[i].bps - 1) * 2, ci[i].nobs, alpha, ci[i].dev_wav, ci[i].nobs, dev_obs, ci[i].nobs, beta, ci[i].dev_res, ci[i].nlag * 2 + 1); // CblasRowMajor ou CblasColMajor ? row-major (C) or column-major (Fortran) data ordering

/*
        A = gsl_matrix_view_array(ci[i].dev_wav, ci[i].nobs, ci[i].nlag * 2 + 1);
        B = gsl_matrix_view_array(dev_obs, ci[i].nobs, (ci[i].bps - 1) * 2);
        C = gsl_matrix_view_array(ci[i].dev_res, ci[i].nlag * 2 + 1,(ci[i].bps - 1) * 2 );
        gsl_blas_dgemm(CblasTrans, CblasNoTrans, alpha, &A.matrix, &B.matrix, beta, &C.matrix);
*/

        get_cor_and_phi((ci[i].nlag * 2 + 1) * (ci[i].bps - 1), ci[i].nlag * 2 + 1, ci[i].dev_res, ci[i].dev_cor, ci[i].dev_phi);
        memcpy(ci[i].host_cor, ci[i].dev_cor, sizeof(double) * (ci[i].nlag * 2 + 1) * (ci[i].bps - 1) );
        memcpy(ci[i].host_phi, ci[i].dev_phi, sizeof(double) * (ci[i].nlag * 2 + 1) * (ci[i].bps - 1) );
        // Start: initialize measurement records
        memset(ci[i].res_gd  , 0x0, sizeof(double) * ci[i].bps);
        memset(ci[i].pk_idx  , 0x0, sizeof(int) * ci[i].bps);
        memset(ci[i].res_phi , 0x0, sizeof(double) * ci[i].bps);
        memset(ci[i].raw_phi , 0x0, sizeof(double) * ci[i].bps);
        memset(ci[i].res_amp , 0x0, sizeof(double) * ci[i].bps);
        memset(ci[i].ttag_phi, 0x0, sizeof(double) * ci[i].bps);
        memset(ci[i].ps      , 0x0, sizeof(double) * ci[i].bps);
        memset(ci[i].w       , 0x0, sizeof(double) * ci[i].bps);
        ci[i].cnt = 0;
        // End: initialize measurement records
        for (p = 0; p < ci[i].bps - 1; p++)
        {
          pk_idx=cblas_idamax(ci[i].nlag * 2 + 1, ci[i].dev_cor + p * (ci[i].nlag * 2 + 1), 1); 
          // pk_idx -= 1; // JMF remove Fortran indexing since cblas returns C indexing
          ci[i].ttag_phi[p] = (double)p * ci[i].duration + (double)ci[i].pt / si.fs;
          ci[i].ps[p]       = ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx] / ci[i].psbb; // passband signal power in <V^2>
          if (pk_idx - 2 >= 0 && pk_idx + 2 < ci[i].nlag * 2 + 1)// && (1.0 + ci[i].snr_min) * ci[i].ps[p] > ci[i].snr_min * ci[i].px)
          {
            // allocate results
            ci[i].pk_idx[p]  = pk_idx - ci[i].nlag; // -nlag ~ +nlag
            ci[i].res_phi[p] = ci[i].host_phi[p * (ci[i].nlag * 2 + 1) + pk_idx]; // carrier phase in which fc*dt has been removed (cycle)
            ci[i].res_amp[p] = sqrt(2.0 * ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx]) / ci[i].psbb; // amplitude in V
            // perform Narrow Correlator
            //ci[i].res_gd[p]  = ((      ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx - 1]
            //                   -       ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx + 1])
            //                   / (     ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx - 1]
            //                   - 2.0 * ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx + 0]
            //                   +       ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx + 1])
            //                   / 2.0
            //                   + (double)(ci[i].pt + pk_idx - ci[i].nlag)) * 1.0e+9 / si.fs;
            // perform High Resolution Correlator
            ci[i].res_gd[p]  = ((      ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx - 1]
                               -       ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx + 1])
                               / (     ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx - 1]
                               - 2.0 * ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx + 0]
                               +       ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx + 1])
                               - (     ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx - 2]
                               -       ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx + 2])
                               / (     ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx - 2]
                               - 2.0 * ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx + 0]
                               +       ci[i].host_cor[p * (ci[i].nlag * 2 + 1) + pk_idx + 2])
                               + (double)(ci[i].pt + pk_idx - ci[i].nlag)) * 1.0e+9 / si.fs;
            ci[i].w[p]       = 1.0;
            ci[i].cnt++;
          }
        }
        // End: correlation
        // Start: Reporting
        if (ci[i].cnt * 2 > ci[i].bps)
        {
          // for constructing interference
          memcpy(ci[i].raw_phi, ci[i].res_phi, sizeof(double) * ci[i].bps);
          memcpy(ci[i].dev_pk_idx , ci[i].pk_idx , sizeof(int)    * ci[i].bps );
          memcpy(ci[i].dev_res_amp, ci[i].res_amp, sizeof(double) * ci[i].bps );
          // find the beginning of the SATRE code
          ci[i].ib = 0;
          if (ci[i].is_first == 0x0)
          {
            memset(ci[i].res, 0x0, sizeof(double) * ci[i].bps);
            if (strcmp(ci[i].code_type, "SDR") == 0)
            {
              if ((ci[i].rc == 2500000) && (ci[i].cid>=100)) // for 2.5Mcps SDR code
              { // ADDED jmf
               for (p = 0; p < ci[i].bps - 1; p++)
               { 
                 ci[i].res[p] = ci[i].res_phi[p] - ci[i].res_phi[p + 1];
               }
              }
            }
          }
          // filter out the obs larger than 3 sigma
          ii = 0;
          memset(ci[i].res, 0x0, sizeof(double) * ci[i].bps);
          for (p = 0; p < ci[i].bps; p++)
          {
            if (ci[i].w[p] > 0.0)
            {
              ci[i].res[ii] = ci[i].res_gd[p];
              ii++;
            }
          }
          c0 = kth_smallest(ci[i].res, ii, ii / 2);
          stddev = (kth_smallest(ci[i].res, ii, ii * 3 / 4) - kth_smallest(ci[i].res, ii, ii / 4)) / 1.349;
          ci[i].cnt = 0;
          // Start: BPSK phase adjustment
          for (p = 0; p < ci[i].bps - 1; p++)
          {
            if (ci[i].w[p] != 0.0)
            {
              if (fabs(ci[i].res_gd[p] - c0) < 3.0 * stddev)
              {
                ci[i].cnt++;
                while (fabs(ci[i].res_phi[p] - ci[i].last_phi) > 0.25)
                {
                  if (ci[i].res_phi[p] > ci[i].last_phi) ci[i].res_phi[p] -= 0.5;
                  else ci[i].res_phi[p] += 0.5;
                }
                ci[i].last_phi = ci[i].res_phi[p];
              }
              else ci[i].w[p] = 0.0;
            }
          }
          // End: BPSK phase adjustment
          // Start: update and record
          if (ci[i].is_first == 0x0)
          {
            sprintf(filename, "ch%s.pn%02d.%dkcps.dat", ci[i].ch, (ci[i].is_sic == 0x0) ? ci[i].cid : ci[i].cid + 50, ci[i].rc / 1000);
            ci[i].fout = fopen(filename, "a");
          }
          // apply linear fit, and then update fc and pt
          gsl_fit_wlinear(ci[i].ttag_phi, 1, ci[i].w, 1, ci[i].res_phi, 1, ci[i].bps, &c0, &c1, &c00, &c01, &c11, &stddev);
          ci[i].fc_prev = ci[i].fc;
          ci[i].fc += round(c1);
          ci[i].df = c1 - round(c1);
          ci[i].phi = fmod(c0 + 1000.0, 1.0);
          // output frequency in Hz and phase in cycle
          if (ci[i].is_first == 0x0)
          {
            fprintf(ci[i].fout, "%14.6lf %11.8lf ", ci[i].fc + ci[i].df, ci[i].phi);
          }
          // output code phase in ns
          gsl_fit_wlinear(ci[i].ttag_gd, 1, ci[i].w, 1, ci[i].res_gd, 1, ci[i].bps, &c0, &c1, &c00, &c01, &c11, &ci[i].sdgd);
          ci[i].sdgd = sqrt(ci[i].sdgd / (double)ci[i].cnt);
          ci[i].gd = c0 + 0.5 * c1;
          ci[i].dg = c1;
          ci[i].pt_prev = ci[i].pt;
          ci[i].pt = (int)round((c0 + c1) * si.fs / 1.0e+9);
          if (ci[i].is_first == 0x0)
          {
            fprintf(ci[i].fout, "%3d %5.3lf %14.6lf %11.6lf %8.4lf ", ci[i].cnt, (double)ci[i].ib * ci[i].duration, ci[i].gd, ci[i].dg, ci[i].sdgd);
          }
          // average signal power value in V2; output value in dBm
          ci[i].pk = average(ci[i].bps, ci[i].ps, ci[i].w);
          if (ci[i].is_first == 0x0)
          {
            fprintf(ci[i].fout, "%7.3lf %7.3lf\n", v2todBm(ci[i].pk), v2todBm(ci[i].px - ci[i].pk));
            fclose(ci[i].fout); // close output file
          }
          else
          {
            // Start: LOG
            sprintf(filename, "rxcomplex.log");
            flog = fopen(filename, "a");
            fprintf(flog, "code lock   : Ch. %s, PRN#%2d, count = %d / %d\n", ci[i].ch, (ci[i].is_sic == 0x0) ? ci[i].cid : ci[i].cid + 50, ci[i].cnt, ci[i].bps);
            fclose(flog);
            // End: LOG
            // reset flag when lock is success: is_first == 0x0 and is_trk == 0x1
            ci[i].is_first = 0x0;
          }
          // End: update and record
          // recover carrier phase for constructing interference
          for (p = 0; p < ci[i].bps - 1; p++)
{            ci[i].res_phi[p] = ci[i].raw_phi[p] - (ci[i].fc + ci[i].df - ci[i].fc_prev) * (double)((p + 1) * ci[i].nobs + ci[i].pt_prev) / si.fs;
printf("phases: %d %lf\n",i,ci[i].res_phi[p]);
}
          memcpy(ci[i].dev_raw_phi, ci[i].res_phi, sizeof(double) * ci[i].bps );
        }
        else
        {
          if (ci[i].is_first == 0x1)
          {
            // Start: LOG
            sprintf(filename, "rxcomplex.log");
            flog = fopen(filename, "a");
            fprintf(flog, "acq failed  : Ch. %s, PRN#%2d, count = %d / %d\n", ci[i].ch, (ci[i].is_sic == 0x0) ? ci[i].cid : ci[i].cid + 50, ci[i].cnt, ci[i].bps);
            fclose(flog);
            // End: LOG
          }
          else
          {
            // Start: LOG
            sprintf(filename, "rxcomplex.log");
            flog = fopen(filename, "a");
            fprintf(flog, "lock lost   : Ch. %s, PRN#%2d, count = %d / %d\n", ci[i].ch, (ci[i].is_sic == 0x0) ? ci[i].cid : ci[i].cid + 50, ci[i].cnt, ci[i].bps);
            fclose(flog);
            // End: LOG
          }
          // Start: reset flags
          ci[i].is_trk = 0x0;
          ci[i].last_phi = 0.0;
          // End: reset flags
        }
        // End: Reporting
      }
      // End: Tracking
    }
    // 2018-11-19 print out
    printf("\nPWR A: %6.2lf dBm , PWR B: %6.2lf dBm\n\n", v2todBm(abs(pwr_A)), v2todBm(abs(pwr_B)));
    for (i = 0; i < si.nch; i++)
    {
      if (ci[i].is_trk == 0x0)
      {
        if (ci[i].px <= ci[i].pk)
          printf("%s: #%02d %4.1lf Mcps SNR       Low      , no signal\n", ci[i].ch, (ci[i].is_sic == 0x0) ? ci[i].cid : ci[i].cid + 50, (double)ci[i].rc * 1.0e-6);
        else
{
          printf("%s: %lf %lf ", ci[i].ch, ci[i].pk , (ci[i].px) );
          printf("%s: #%02d %4.1lf Mcps SNR %6.2lf < %6.2lf, no signal\n", ci[i].ch, (ci[i].is_sic == 0x0) ? ci[i].cid : ci[i].cid + 50, (double)ci[i].rc * 1.0e-6, 10.0 * log10(ci[i].pk / (ci[i].px - ci[i].pk)), 10.0 * log10(ci[i].snr_min));
}
      }
      else
      {
        if (ci[i].is_first == 0x1)
         {
          printf("%s: %lf %lf ", ci[i].ch, ci[i].pk , (ci[i].px) );
          printf("%s: #%02d %4.1lf Mcps SNR %6.2lf > %6.2lf, analyzing\n", ci[i].ch, (ci[i].is_sic == 0x0) ? ci[i].cid : ci[i].cid + 50, (double)ci[i].rc * 1.0e-6, 10.0 * log10(ci[i].pk / (ci[i].px - ci[i].pk)), 10.0 * log10(ci[i].snr_min));
         }
        else
        {
          printf("%s: #%02d %4.1lf Mcps %12.3lf Hz ", ci[i].ch, (ci[i].is_sic == 0x0) ? ci[i].cid : ci[i].cid + 50, (double)ci[i].rc * 1.0e-6, ci[i].fc + ci[i].df);
          printf("%13.3lf (%6.3lf) ns ", ci[i].gd + ci[i].ib * ci[i].duration * 1.0e+9, ci[i].sdgd / sqrt((double)ci[i].cnt));
          printf("SNR %6.2lf dB\n", v2todBm(ci[i].pk) - v2todBm(ci[i].px - ci[i].pk)); // show SNR on the screen
        }
      }
    }
    // 2018-11-19 print out
    //End: DSP
  } while (datares==sps*4/Ninterp);
  // End: infinite measurement
  return 0;
}

double kth_smallest(double *a, int n, int k) // find the k-th smallest value in the array a[]
{
  int i, j, l, m;
  double x, *b, t;
  b = (double *)malloc(sizeof(double) * n);
  memcpy(b, a, sizeof(double) * n);
  l = 0; m = n - 1;
  while (l < m)
  {
    x = b[k]; i = l; j = m;
    do
    {
      while (b[i] < x) i++;
      while (b[j] > x) j--;
      if (i <= j)
      {
        t = b[i]; b[i] = b[j]; b[j] = t;
        i++; j--;
      }
    } while (i <= j);
    if (j < k) l = i;
    if (k < i) m = j;
  }
  x = b[k];
  free(b);
  return x;
}

int SDRcode(channel_info *c)
{
  FILE *fd;
  int k,datares;                 // JMFfile
  char codefilename[255];
  char *tmp;
  tmp=(char*)malloc(sizeof(char)*c->clen);
  if (c->cid >= 100) // SDR JMF
  { sprintf(codefilename,"%d.bin",c->cid-100); // assume LTFB code in file 0.bin and OP in file 1.bin
    fd=fopen(codefilename,"rb"); // JMFfile
    if (fd==NULL) {printf("Code filename error %s\n",codefilename);exit(-1);}
    datares=fread(tmp, sizeof(char), c->clen, fd);
    for (k=0;k<c->clen;k++) {c->host_code[k]=(1-2*(int)tmp[k]);if (k<48) printf("%d",c->host_code[k]);}
    if (datares==c->clen) printf(" %d SDR code success: %s\n",c->clen,codefilename);
  }
  free(tmp);
  return 0;
}

double average(int nobs, double *x, double *w)
{
	int i, cnt = 0;
	double res = 0.0;
	if (nobs == 0)
	  return 0.0;
	for (i = 0; i < nobs; i++)
	{
		if (w[i] > 0.0)
		{
			res += x[i];
			cnt++;
		}
	}
	return res / (double)cnt;
}

void char2double(int nobs, int dec, char *smp, double *smpA, double *smpB)
{
  int i;
  for (i=0;i < nobs;i++)
  {
    smpA[i] = (double)smp[2 * i * dec] / 128.0;
    smpB[i] = (double)smp[2 * i * dec + 1] / 128.0;
  }
}

void short2double(int nobs, int dec, short *smp, std::complex<double> *smpA, std::complex<double> *smpB)
{
  int i;
  fftw_plan plan1, plan2;
  
  std::complex<double> *tmpA, *tmpB;
  tmpA=(std::complex<double>*)malloc(sizeof(std::complex<double>) * nobs);
  tmpB=(std::complex<double>*)malloc(sizeof(std::complex<double>) * nobs);

  for (i=0;i<nobs;i++) {tmpA[i].real(0.);tmpA[i].imag(0.); tmpB[i].real(0.);tmpB[i].imag(0.);}
  for (i=0;i < nobs/Ninterp; i++)
  {
    tmpA[i].real( (double)smp[4 * i * dec] / 32768.0);
    tmpA[i].imag( (double)smp[4 * i * dec + 1] / 32768.0);
    tmpB[i].real( (double)smp[4 * i * dec + 2] / 32768.0);
    tmpB[i].imag( (double)smp[4 * i * dec + 3] / 32768.0);
  }

// interpolate A
  plan1 = fftw_plan_dft_1d(nobs/Ninterp, reinterpret_cast<fftw_complex*>(tmpA),reinterpret_cast<fftw_complex*>(tmpA),
                                      FFTW_FORWARD, FFTW_ESTIMATE);
  fftw_execute(plan1);
  for (i=0;i< nobs/Ninterp/2;i++) 
     {tmpA[nobs-i-1].real(real(tmpA[nobs/Ninterp-i-1])/(float)(nobs/Ninterp));
      tmpA[nobs-i-1].imag(imag(tmpA[nobs/Ninterp-i-1])/(float)(nobs/Ninterp));
      tmpA[nobs/Ninterp-i-1].real(0.);
      tmpA[nobs/Ninterp-i-1].imag(0.);
     }
  plan2 = fftw_plan_dft_1d(nobs, reinterpret_cast<fftw_complex*>(tmpA),reinterpret_cast<fftw_complex*>(tmpA),
                                      FFTW_BACKWARD, FFTW_ESTIMATE);
  fftw_execute(plan2);
// finished for A, now interpolate B
  plan1 = fftw_plan_dft_1d(nobs/Ninterp, reinterpret_cast<fftw_complex*>(tmpB),reinterpret_cast<fftw_complex*>(tmpB),
                                      FFTW_FORWARD, FFTW_ESTIMATE);
  fftw_execute(plan1);
  for (i=0;i< nobs/Ninterp/2;i++) 
     {tmpB[nobs-i-1].real(real(tmpB[nobs/Ninterp-i-1])/(float)(nobs/Ninterp));
      tmpB[nobs-i-1].imag(imag(tmpB[nobs/Ninterp-i-1])/(float)(nobs/Ninterp));
      tmpB[nobs/Ninterp-i-1].real(0.);
      tmpB[nobs/Ninterp-i-1].imag(0.);
     }
  plan2 = fftw_plan_dft_1d(nobs, reinterpret_cast<fftw_complex*>(tmpB),reinterpret_cast<fftw_complex*>(tmpB),
                                      FFTW_BACKWARD, FFTW_ESTIMATE);
  fftw_execute(plan2);
  for (i=0;i < nobs; i++) { smpA[i].real(real(tmpA[i])/(float)nobs); smpB[i].real(real(tmpB[i])/(float)nobs);
                            smpA[i].imag(imag(tmpA[i])/(float)nobs); smpB[i].imag(imag(tmpB[i])/(float)nobs);
                          }
  free(tmpA);
  free(tmpB);
}

void PRN_sampling(int nobs, int *code, std::complex<double> *prn, int rc, double fs, int clen, double delay)
{
  int i,idx;
  for (i=0 ; i< nobs;i++)
  {
    idx = (int)floor(fmod(((double)i / fs - delay * 1.0e-9) * (double)rc, (double)clen));
    if (idx < 0)
      idx += clen;
    else if (idx >= clen)
      idx -= clen;
    prn[i].real( (double)code[idx]);
    prn[i].imag( 0.0 );
  }
}

void memcpy_acq(int nobs, std::complex<double> *wav, std::complex<double> *wav_acq, int dec)
{
  int i;
  for(i=0;i < nobs;i++)
  {
    wav_acq[i].real( wav[i * dec].real());
  }
}

void PRN_mapping(int nobs, int snobs, int knobs, std::complex<double> *prn, double *pn)
{
  int i,idx;
  for (i=0;i < nobs;i++)
  {
    idx = (i % snobs) - (i / snobs - knobs);
    if (idx >= snobs) idx -= snobs;
    if (idx < 0) idx += snobs;
    pn[i] = prn[idx].real();
  }
}

void cross_spectrum(int nobs, std::complex<double> *obs, std::complex<double> *prn, double df, double fmax, double fmin, std::complex<double> *robs)
{
  int i,idx;
  for (i=0;i < nobs;i++)
  {
    idx = (i >= nobs / 2) ? i - nobs : i;
    if ((double)idx * df < fmax && (double)idx * df > fmin && idx != 0)
    {
      robs[i].real( (obs[i].real() * prn[i].real() + obs[i].imag() * prn[i].imag()) / (double)nobs / (double)nobs);
      robs[i].imag( (obs[i].imag() * prn[i].real() - obs[i].real() * prn[i].imag()) / (double)nobs / (double)nobs);
    }
    else
    {
      robs[i].real( 0.0 );
      robs[i].imag( 0.0 );
    }
  }
}

void lowpass(int nobs, std::complex<double> *obs, double df, double fmax, double fmin)
{
  int i,idx; //  = blockIdx.x * blockDim.x + threadIdx.x, idx;
  for (i=0;i < nobs;i++)
  {
    idx = (i >= nobs / 2) ? i - nobs : i;
    if ((double)idx * df < fmax && (double)idx * df > fmin && idx != 0)
    {
      obs[i].real( real(obs[i]) / (double)nobs);
      obs[i].imag( imag(obs[i]) / (double)nobs);
    }
    else
    {
      obs[i].real( 0.0 );
      obs[i].imag( 0.0 );
    }
  }
}

void downconv_acq(int nobs, double ff, double phi, std::complex<double>*smp, std::complex<double> *res, int dec)
{
  int i; //  = blockIdx.x * blockDim.x + threadIdx.x;
  for (i=0;i<nobs;i++)
  {
    // ff: discrete-time frequency
    // phi: initial phase
    res[i].real(1.4142135624 * (real(smp[i * dec]) * cos(-1.0 * 2.0 * PI * (ff * (double)i + phi))- imag(smp[i * dec]) * sin(-1.0 * 2.0 * PI * (ff * (double)i + phi))));
    res[i].imag(1.4142135624 * (real(smp[i * dec]) * sin(-1.0 * 2.0 * PI * (ff * (double)i + phi))+ imag(smp[i * dec]) * cos(-1.0 * 2.0 * PI * (ff * (double)i + phi))));
  }
}

void downconv_trk(int nobs, int ld, double ff, double phi, std::complex<double>*smp, double *res)
{
  int i,idx; // = blockIdx.x * blockDim.x + threadIdx.x;
  for (i=0;i < nobs;i++)
  {
    // ld: leading dimension
    idx = (i / ld) * 2 * ld + i % ld;
    res[idx +  0] = 1.4142135624 * (real(smp[i]) * cos(-1.0 * 2.0 * PI * (ff * (double)i + phi))-imag(smp[i]) * sin(-1.0 * 2.0 * PI * (ff * (double)i + phi)));
    res[idx + ld] = 1.4142135624 * (real(smp[i]) * sin(-1.0 * 2.0 * PI * (ff * (double)i + phi))+imag(smp[i]) * cos(-1.0 * 2.0 * PI * (ff * (double)i + phi)));
  }
}

void get_cor_and_phi(int nobs, int ld, double *res, double *cor, double *phi)
{
  int i,idx; // = blockIdx.x * blockDim.x + threadIdx.x;
  for (i=0;i < nobs;i++)
  {
    idx = (i / ld) * 2 * ld + i % ld;
    cor[i] = res[idx] * res[idx] + res[idx + ld] * res[idx + ld];
    phi[i] = atan2(res[idx + ld], res[idx]) / 2.0 / PI;
  }
}

void MAI_up(int nobs, int ld, int pt, double *amp, std::complex<double> *c_wav, int *pidx, double ff, double *pmod, double *wav)
{
  int i,k,p; //  = blockIdx.x * blockDim.x + threadIdx.x, k, p;
  for (i=pt;i<nobs;i++) // if (i < nobs && i >= pt)
  {
    p = (i - pt) / ld;
    k = (i - pidx[p] - pt + ld) % ld;
    wav[i] += 0.5 * amp[p] * c_wav[k].real() * cos(2.0 * PI * (ff * (double)i + pmod[p]));
  }
}

void MAI_out(int nobs, double *in, double *out)
{
  int i; // = blockIdx.x * blockDim.x + threadIdx.x;
  for (i=0;i<nobs;i++)
    out[i] = in[i] - out[i];
}

/*
	computer current time (UTC + 0)
*/
void current_time(int offset, int *mjd, int *year, int *month, int *day, int *doy, int *hour, int *minute, int *second)
{
	time_t sec;
	sec = (int)time(NULL) + offset;
	*mjd = 40587 + sec / 86400;
	*hour = (sec % 86400) / 3600;
	*minute = (sec % 3600) / 60;
	*second = sec % 60;
	mjd2doy(*mjd, year, doy);
	mjd2date(*mjd, year, month, day);
//	return 40587.0 + (double)time(NULL) / 86400.0;
	return;
}

void date2doy(int year, int month, int day, int *doy)
{

	int i, mday[13] = {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
	if ((year % 4 == 0 && year % 100 != 0 ) || year % 400 == 0)
		mday[2] = 29;
  *doy = day;
  for (i = 1; i < month; i++) *doy += mday[i];
  return;
}

void doy2date(int year, int doy, int *month, int *day)
{
 int mday[13] = {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
 if ((year % 4 == 0 && year % 100 != 0 ) || year % 400 == 0)
	mday[2] = 29;
 *month = 1;
 *day = doy;
 while (*day > mday[*month])
  {
    *day -= mday[*month];
    (*month)++;
  }
 return;
}

/*
  date to MJD
*/
int date2mjd(int year, int month, int day)
{
  int mday[13] = {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
  int i, leap_days;
  leap_days = (year - 1) / 4 - (year - 1) / 100 + (year - 1) / 400;
  if ((year % 4 == 0 && year % 100 != 0 ) || year % 400 == 0)
    mday[2] = 29;
  for (i = 1; i < month; i++)
    day = day + mday[i];
  return (year - 1) * 365 + day + leap_days - 678576;
}
/*
  MJD to date
*/
void mjd2date(int mjd, int *year, int *month, int *day)
{
  int mday [13] = {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
  // 400 years = 146097 days, 100 years = 36524 days, 4 years = 1461 days, 3 normal years = 1095
  *year = 1; *month = 1;
  *day = mjd + 678576; //total days from 0001/01/01
  *year += *day / 146097 * 400; *day = *day % 146097;
  *year += *day /  36524 * 100; *day = *day %  36524;
  *year += *day /   1461 *   4; *day = *day %   1461;

  if (*day <= 1095)
  {
  	*year += *day / 365;
  	*day = *day % 365;
  }
  else
  {
  	*year += 3;
  	*day -= 1095;
  }

  if (*day == 0)
  {
  	(*year)--;
  	*month = 12;
  	*day = 31;
  	return;
  }

  if (( *year % 4 == 0 && *year % 100 != 0 ) || *year % 400 == 0)
  	mday[2] = 29;


  while (*day > mday[*month])
  {
    *day -= mday[*month];
    (*month)++;
  }
  return;
}
/*
  DOY (day of year) to MJD
*/
int doy2mjd(int year, int doy)
{
  int leap_days;
  leap_days = (year - 1) / 4 - (year - 1) / 100 + (year - 1) / 400;
  return (year - 1) * 365 + doy + leap_days - 678576;
}
/*
  MJD to DOY (day of year)
*/
void mjd2doy(int mjd, int *year, int *doy)
{
	// 400 years = 146097 days, 100 years = 36524 days, 4 years = 1461 days
	*year = 1;
	*doy = mjd + 678576;
	*year += *doy / 146097 * 400; *doy = *doy % 146097;
	*year += *doy /  36524 * 100; *doy = *doy %  36524;
	*year += *doy /   1461 *   4; *doy = *doy %   1461;

	if (*doy <= 1095)
  {
  	*year += *doy / 365;
  	*doy = *doy % 365;
  }
  else
  {
  	*year += 3;
  	*doy -= 1095;
  }

	if (*doy == 0)
	{
		(*year)--;
		if (( *year % 4 == 0 && *year % 100 != 0 ) || *year % 400 == 0)
			*doy = 366;
		else
			*doy = 365;
	}

	return;
}

double v2todBm(double v2)
{
  if (v2 > 0.0) return 10.0 * log10(v2 * 1000.0 / 25.0);
  else return 0.0;
}
