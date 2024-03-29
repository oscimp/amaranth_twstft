#include <iostream>
#include <cstdio>
#include <vector>
#include <cmath>
#include <complex>
#include <algorithm>
#include <chrono>

#include <fftw3.h>
#include <matio.h>

#define DISPLAY_TIME
#undef DISPLAY_TIME

const uint32_t fs = (5e6);
const uint32_t Nint=1;
//foffset=0
//frange=8000
//freq = np.linspace(-fs/2, (fs/2), num=int(fs), dtype=float)
//k=np.nonzero((np.array(freq) < 2*(foffset+frange)) & (np.array(freq) > 2*(foffset-frange)))
//k=k[0];
//temps = np.array(range(0, int(fs))) / fs

class GoRanging {
    public:
        GoRanging(double fs, const std::string &filename, const std::string &prn_file, int remote);
        ~GoRanging();

        void compute();
        bool save(std::string filename);

    private:
        bool fill_fcode(const std::string &filename);
        std::vector<double> linspace(double start_in, double end_in, int num_in);
        template <typename T, typename A>
            int arg_max(std::vector<T, A> const& vec);
        double _fs;
        size_t _fcode_len;
        std::vector<std::complex<double>> _fcode;
        std::vector<double> _tcode;
        std::vector<double> _code;
        std::vector<double> _freq;
        std::vector<double> _temps;
        std::vector<double> _k;
        std::vector<double> _correction1;
        std::vector<double> _correction2;
        std::vector<double> _df1, _df2;
        std::vector<double> _puissance1, _puissance2;
        std::vector<double> _SNR1, _SNR2;
        std::vector<std::complex<double>> _xval1, _xval1m1, _xval1p1;
        std::vector<std::complex<double>> _xval2, _xval2m1, _xval2p1;
        std::string _filename;
                int _remote;
        FILE *_fd;
        fftw_complex * _chan1;
        fftw_complex * _result;
        fftw_plan _plan_a;
        fftw_complex * _chan_ifft;
        fftw_complex * _result_ifft;
        fftw_plan _ifft;
        int kmin, kmax;
};

GoRanging::GoRanging(double fs, const std::string &filename, const std::string &prn_file, int remote): 
                        _fs(fs), _fcode_len(0), _filename(filename), _remote(remote)
{
    _fd = fopen(filename.c_str(), "r");
    if (!_fd)
        throw std::runtime_error("Fail to open " + _filename);

#ifdef FFTW_THREADS
    if (fftw_init_threads() == 0)
        throw std::runtime_error("fftw_init_threads_failed");

    fftw_plan_with_nthreads(4);
#endif

    if (!fill_fcode(prn_file))
        throw std::runtime_error("Fail to retrieve fcode file");

    _fcode_len = _fcode.size();

    /* fft */
    _chan1 = (fftw_complex *)malloc(sizeof(fftw_complex) * _fcode_len);
    if (!_chan1) {
        throw std::runtime_error("Fail to allocate FFT input buffer");
    }
    _result =
        (fftw_complex *) fftw_malloc(sizeof(fftw_complex) * _fcode_len);
    if (!_result) {
        throw std::runtime_error("Fail to allocate FFT output buffer");
    }

    _plan_a = fftw_plan_dft_1d(_fcode_len, _chan1, _result, FFTW_FORWARD, FFTW_ESTIMATE);
    if (!_plan_a)
        throw std::runtime_error("Fail to initialize plan A");
    /* ifft */
    _chan_ifft = (fftw_complex *)malloc(sizeof(fftw_complex) * _fcode_len * (2*Nint+1));
    if (!_chan_ifft) {
        throw std::runtime_error("Fail to allocate FFT input buffer");
    }
    _result_ifft =
        (fftw_complex *) fftw_malloc(sizeof(fftw_complex) * _fcode_len * (2*Nint+1));
    for (size_t i = 0; i < _fcode_len * (2*Nint+1); i++)
        _chan_ifft[i][0] = _chan_ifft[i][1] = 0;
    _ifft = fftw_plan_dft_1d(_fcode_len * (2*Nint+1), _chan_ifft, _result_ifft, FFTW_BACKWARD, FFTW_ESTIMATE);

    _freq = linspace(-fs/2, fs/2, _fcode_len);
    _temps.resize(_fcode_len);
    double foffset = 0;
    double frange = 8000;
    for (size_t i = 0; i < _fcode_len; i++) {
        if (_freq[i] < 2 * (foffset+frange))
            kmax = i;
        if (_freq[i] <= 2*(foffset-frange))
            kmin = i;
        _temps[i] = i / fs;
    }
}

GoRanging::~GoRanging()
{
    fftw_free(_plan_a);
    fftw_free(_result);
    fftw_free(_chan1);
    fftw_free(_ifft);
    fftw_free(_chan_ifft);
    fftw_free(_result_ifft);
    fclose(_fd);
}

void GoRanging::compute()
{
    int16_t *data = (int16_t*) malloc(sizeof(int16_t) * _fcode_len * 4);
    std::vector<std::complex<double>> y;
    std::vector<std::complex<double>> d1;
    std::vector<std::complex<double>> d1_fft, d2_fft;
    std::vector<std::complex<double>> d2;
    std::vector<std::complex<double>> d11, d21;
    std::vector<std::complex<double>>prnmap01((2*Nint+1)*_fcode_len, 0);
    std::vector<std::complex<double>>prnmap02((2*Nint+1)*_fcode_len, 0);
    y.resize(_fcode_len);
    d1.resize(_fcode_len);
    d1_fft.resize(_fcode_len);
    d2_fft.resize(_fcode_len);
    d2.resize(_fcode_len);
    bool must_stop = false;
    std::vector<std::complex<double>> zero_vect(_fcode_len, std::complex<double>(0,0));
#ifdef DISPLAY_TIME
    std::chrono::time_point<std::chrono::high_resolution_clock> t_read;
#endif

    int p = 0;
#ifdef DISPLAY_TIME
    auto t_start = std::chrono::high_resolution_clock::now();
#endif
    while(!must_stop) {
        size_t res = fread(data, sizeof(int16_t), _fcode_len * 4, _fd);
        if (res < _fcode_len * 4) {
            printf("No more data\n");
            break;
        }

        std::complex<double> mean1(0, 0), mean2(0, 0);
        // convert to complex
        for (size_t i = 0, ii=0; i < _fcode_len; ii+=4, i++) {
            d1[i].real((double)data[ii + 0]); // d=fread(f,length(fcode)*4,'int16');  % 1 code length
                                              // d=d(1:2:end)+j*d(2:2:end);
            d1[i].imag((double)data[ii + 1]); // d1=d(1:2:end);  % measurement
            d2[i].real((double)data[ii + 2]); // d2=d(2:2:end);  % reference
            d2[i].imag((double)data[ii + 3]);
            mean1 += d1[i];
            mean2 += d2[i];
        }
        mean1 /= _fcode_len;                  
        mean2 /= _fcode_len;                  

// analysis of d1
// find frequency offset from d^2
        // fft & co for d1
        // d1_fft = np.fft.fftshift(np.abs(np.fft.fft(d1 * d1)))
        for (size_t i = 0; i < _fcode_len; i++) {
            d1[i] -= mean1;                   //  d1=d1-mean(d1);   remove mean
            d2[i] -= mean2;                   //  d2=d2-mean(d2);
            std::complex<double> tmp = d1[i] * d1[i];
            _chan1[i][0] = tmp.real();
            _chan1[i][1] = tmp.imag();
        }
        fftw_execute(_plan_a); // d1^2                         //  d22=fftshift(abs(fft(d1.^2))); % 0.1 Hz accuracy

        for (size_t i = 0; i < _fcode_len; i++) {
            size_t ii = (i < _fcode_len/2) ? i + (_fcode_len / 2) : i - (_fcode_len / 2); // fftshift
            d1_fft[ii] = (std::complex<double>(_result[i][0], _result[i][1]));            // d1_fft=fftshift(fft(d1^2))
        }
        // tmp = d1_fft[k].argmax()+k[0]
        std::vector<std::complex<double>> subvector1;
        std::copy(d1_fft.begin() + kmin, d1_fft.begin() + kmax, std::back_inserter(subvector1));
        int pos = arg_max(subvector1) + kmin;                  // [~,df1(p)]=max(d22(k));df1(p)=df1(p)+k(1)-1;df1(p)=freq(df1(p))/2;offset1=df1(p);
        _df1.push_back( _freq[pos] / 2.);

        double df1 = _freq[pos] / 2.;

        // lo = np.exp(-1j * 2 * np.pi * tmp * temps)
        std::complex<double>t = std::complex<double>(0, -1) * (double)2.0f * M_PI * df1;
        for (size_t i = 0; i < _fcode_len; i++) {
            std::complex<double> lo = std::exp(t * _temps[i]); // lo=exp(-j*2*pi*df1(p)*temps); % frequency offset
            std::complex<double> ytmp = d1[i] * lo;            // y=d1.*lo;                      % frequency transposition
            _chan1[i][0] = ytmp.real();
            _chan1[i][1] = ytmp.imag();
        }

        // multmp1 = np.fft.fftshift(np.fft.fft(y) * fcode)
        fftw_execute(_plan_a);                                 //  ffty=fft(y);
        for (size_t i = 0; i < _fcode_len * (2*Nint+1); i++)
            _chan_ifft[i][0] = _chan_ifft[i][1] = 0;
        for (size_t i = 0; i < _fcode_len; i++) {
            y[i] = std::complex<double>(_result[i][0], _result[i][1]);   // y = FFT(d1*lo)
            std::complex<double> d = y[i] * _fcode[i];
            int ii = (i < _fcode_len / 2) ? i : (i + (2*_fcode_len));
            _chan_ifft[ii][0] = d.real();
            _chan_ifft[ii][1] = d.imag();
        }

#ifdef DISPLAY_TIME
        t_read = std::chrono::high_resolution_clock::now();
#endif
        fftw_execute(_ifft);
        for (size_t i = 0; i < prnmap01.size(); i++) {
            prnmap01[i].real(_result_ifft[i][0]);         // prnmap01=fftshift(ffty.*fcode);      % xcorr
            prnmap01[i].imag(_result_ifft[i][1]);         // prnmap01=[zeros(length(y)*(Nint),1) ; prnmap01 ; zeros(length(y)*(Nint),1)]; % interpolation to 3x samp_rate
                                                          // prnmap01=(ifft(fftshift(prnmap01))); % back to time /!\ NO outer fftshift for 0-delay at left
                       }
        unsigned int indice1 = arg_max(prnmap01);         //  [~,indice1(p)]=max(abs(prnmap01));  % only one correlation peak
        double xval1   = std::abs(prnmap01[indice1]);     //  xval1(p)=prnmap01(indice1(p));
        double xval1m1 = std::abs(prnmap01[indice1-1]);   //  xval1m1(p)=prnmap01(indice1(p)-1);
        double xval1p1 = std::abs(prnmap01[indice1+1]);   //  xval1p1(p)=prnmap01(indice1(p)+1);
        double corr1 = (xval1m1 - xval1p1)/2./(xval1m1 + xval1p1-2*xval1); //  correction1_a(p)=(abs(prnmap01(indice1(p)-1))-abs(prnmap01(indice1(p)+1)))/(abs(prnmap01(indice1(p)-1))+abs(prnmap01(indice1(p)+1))-2*abs(prnmap01(indice1(p))))/2;
        _correction1.push_back(indice1 + corr1);
      
        _xval1.push_back(prnmap01[indice1]);
        _xval1m1.push_back(prnmap01[indice1-1]);
        _xval1p1.push_back(prnmap01[indice1+1]);
        printf("%d %0.12lf\t%.3f\t", p, ((double)indice1+corr1)/fs/(2*Nint+1.),df1);
//  % SNR computation
        for (size_t i = 0; i < _fcode_len * (2*Nint); i++) //  yint=zeros(length(y)*(2*Nint+1),1);
            _chan_ifft[i+_fcode_len / 2][0] = _chan_ifft[i+_fcode_len / 2][1] = 0;
        for (size_t i = 0; i < _fcode_len; i++) {           
            int ii = (i < _fcode_len / 2) ? i : (i + (2*_fcode_len));
            _chan_ifft[ii][0] = y[i].real();                 // yint(1:length(y)/2)=ffty(1:length(y)/2);
            _chan_ifft[ii][1] = y[i].imag();                 // yint(end-length(y)/2+1:end)=ffty(length(y)/2+1:end);
        }
        fftw_execute(_ifft);                                 // yint=ifft(yint);   vvv- _tcode is interpolated
        for (size_t i = 0; i < prnmap01.size(); i++) {       // codetmp=repelems(code,[[1:length(code)] ; ones(1,length(code))*(2*Nint+1)])'; % interpolate
            prnmap01[i].real(_result_ifft[i][0]);            // re-use prnmap01 for a different purpose
            prnmap01[i].imag(_result_ifft[i][1]);
           }

        std::rotate(prnmap01.begin(),prnmap01.begin()+indice1-1,prnmap01.end());
        double SNR1r(0), SNR1i(0), SNR1s(0), puissance1code(0);
        for (size_t i = 0; i < prnmap01.size(); i++) {
            double R=real(prnmap01[i]*_tcode[i]);            //  yincode=[yint(indice1(p)-1:end) ; yint(1:indice1(p)-2)].*codetmp;
            double I=imag(prnmap01[i]*_tcode[i]);
            SNR1r+=R;                                        // SNR1r(p)=mean(real(yincode))^2/var(yincode);
            SNR1i+=I;                                        // SNR1i(p)=mean(imag(yincode))^2/var(yincode);
           }
	SNR1r/=prnmap01.size();
	SNR1i/=prnmap01.size();
        puissance1code=SNR1r*SNR1r+SNR1i*SNR1i;              // puissance1code(p)=mean(real(yincode))^2+mean(imag(yincode))^2;
        for (size_t i = 0; i < prnmap01.size(); i++) {
            double R=real(prnmap01[i]*_tcode[i]);            // puissance1total(p)=var(y);
            double I=imag(prnmap01[i]*_tcode[i]);
            SNR1s+=(R-SNR1r)*(R-SNR1r)+(I-SNR1i)*(I-SNR1i);  // (v-<v>)^2
           } 
	SNR1s/=prnmap01.size();
        SNR1r=SNR1r*SNR1r/SNR1s;                             // <.>^2/var
        SNR1i=SNR1i*SNR1i/SNR1s; 
        printf("%.1lf\t%0.1lf\t", 10*log10(puissance1code),10*log10(SNR1r+SNR1i));
        _SNR1.push_back( 10*log10(SNR1r+SNR1i) );
        _puissance1.push_back( 10*log10(puissance1code) );

        if (_remote==0) {                                    // analysis of d2
            for (size_t i = 0; i < _fcode_len; i++) {
                std::complex<double> tmp = d2[i] * d2[i];
                _chan1[i][0] = tmp.real();
                _chan1[i][1] = tmp.imag();
            }
            fftw_execute(_plan_a); // d2^2
    
            for (size_t i = 0; i < _fcode_len; i++) {
                size_t ii = (i < _fcode_len/2) ? i + (_fcode_len / 2) : i - (_fcode_len / 2); // fftshift
                d2_fft[ii] = (std::complex<double>(_result[i][0], _result[i][1]));            // d2_fft=fftshift(fft(d2^2))
            }
            // tmp = d2_fft[k].argmax()+k[0]
            std::vector<std::complex<double>> subvector2;
            std::copy(d2_fft.begin() + kmin, d2_fft.begin() + kmax, std::back_inserter(subvector2));
            pos = arg_max(subvector2) + kmin;
            _df2.push_back( _freq[pos] / 2.);
    
            double df2 = _freq[pos] / 2.;
            if (abs(df2)<(_freq[1]-_freq[0])) df2=0.;     // cancel d2 if smaller than bin size
            t = std::complex<double>(0, -1) * df2 * M_PI;
            for (size_t i = 0; i < _fcode_len; i++) {
                std::complex<double> lo = std::exp(t * _temps[i]);  // lo = np.exp(-1j * 2 * np.pi * tmp * temps)
                // y = d2 * lo
                std::complex<double> ytmp = d2[i] * lo; // frequency transposition
                _chan1[i][0] = ytmp.real();
                _chan1[i][1] = ytmp.imag();
            }
            // fft(d2) + prnmap02
            fftw_execute(_plan_a);
    
            for (size_t i = 0; i < _fcode_len * (2*Nint); i++)
                _chan_ifft[i+_fcode_len / 2][0] = _chan_ifft[i+_fcode_len / 2][1] = 0;
            for (size_t i = 0; i < _fcode_len; i++) {
                y[i] = std::complex<double>(_result[i][0], _result[i][1]);
                std::complex<double> d = y[i] * _fcode[i];
                int ii = (i < _fcode_len / 2) ? i : (i + (2*_fcode_len));
                _chan_ifft[ii][0] = d.real();
                _chan_ifft[ii][1] = d.imag();
            }
    
            fftw_execute(_ifft);
            for (size_t i = 0; i < prnmap02.size(); i++) {
                prnmap02[i].real(_result_ifft[i][0]);
                prnmap02[i].imag(_result_ifft[i][1]);
            }
    
            int indice2 = arg_max(prnmap02);
            double xval2   = std::abs(prnmap02[indice2]);
            double xval2m1 = std::abs(prnmap02[indice2-1]);
            double xval2p1 = std::abs(prnmap02[indice2+1]);
    
            double corr2 = ((xval2m1 - xval2p1)/(xval2m1 + xval2p1-2*xval2)/2);
            _correction2.push_back(indice2 + corr2);
    
            _xval2.push_back(prnmap02[indice2]);
            _xval2m1.push_back(prnmap02[indice2-1]);
            _xval2p1.push_back(prnmap02[indice2+1]);

            printf(" %0.12lf\t%.3f\t", ((double)indice2+corr2)/fs/(2.*Nint+1.),df2);

//  % SNR computation
        for (size_t i = 0; i < _fcode_len * (2*Nint); i++) //  yint=zeros(length(y)*(2*Nint+1),1);
            _chan_ifft[i+_fcode_len / 2][0] = _chan_ifft[i+_fcode_len / 2][1] = 0;
        for (size_t i = 0; i < _fcode_len; i++) {
            int ii = (i < _fcode_len / 2) ? i : (i + (2*_fcode_len));
            _chan_ifft[ii][0] = y[i].real();
            _chan_ifft[ii][1] = y[i].imag();
        }
        fftw_execute(_ifft);                                 //  yint=ifft(yint);
        for (size_t i = 0; i < prnmap02.size(); i++) {
            prnmap02[i].real(_result_ifft[i][0]);            // re-use prnmap02 for a different purpose
            prnmap02[i].imag(_result_ifft[i][1]);
                       }

        std::rotate(prnmap02.begin(),prnmap02.begin()+indice2-1,prnmap02.end()); // yincode=[yint(indice1(p)-1:end) ; yint(1:indice1(p)-2)].*codetmp;
        double SNR2r(0), SNR2i(0), SNR2s(0), puissance2code(0);
        for (size_t i = 0; i < prnmap02.size(); i++) {
            double R=real(prnmap02[i]*_tcode[i]);
            double I=imag(prnmap02[i]*_tcode[i]);
            SNR2r+=R;
            SNR2i+=I;
           }
	SNR2r/=prnmap02.size();
	SNR2i/=prnmap02.size();
        puissance2code=SNR2r*SNR2r+SNR2i*SNR2i; //  puissance2code(p)=mean(real(yincode))^2+mean(imag(yincode))^2;
        for (size_t i = 0; i < prnmap02.size(); i++) {
            double R=real(prnmap02[i]*_tcode[i]);
            double I=imag(prnmap02[i]*_tcode[i]);
            SNR2s+=(R-SNR2r)*(R-SNR2r)+(I-SNR2i)*(I-SNR2i);  // (v-<v>)^2
           } 
	SNR2s/=prnmap02.size();  // <.>^2/var
        SNR2r=SNR2r*SNR2r/SNR2s; // SNR2r(p)=mean(real(yincode))^2/var(yincode);
        SNR2i=SNR2i*SNR2i/SNR2s; // SNR2i(p)=mean(imag(yincode))^2/var(yincode);

        printf("%.1lf\t%0.1lf\n", 10*log10(puissance2code), 10*log10(SNR2r+SNR2i));
        _SNR2.push_back( 10*log10(SNR2r+SNR2i) );
        _puissance2.push_back( 10*log10(puissance2code) );
        }
        else printf("\n");
        p++;
            //must_stop = true;
    }
#ifdef DISPLAY_TIME
    auto t_end = std::chrono::high_resolution_clock::now();
    double elapsed_time_ms = std::chrono::duration<double, std::milli>(t_end-t_start).count();
    printf("temps: %lf\n", elapsed_time_ms);
    elapsed_time_ms = std::chrono::duration<double, std::milli>(t_read-t_start).count();
    printf("read: %lf\n", elapsed_time_ms);
    elapsed_time_ms = std::chrono::duration<double, std::milli>(t_end - t_read).count();
    printf("end: %lf\n", elapsed_time_ms);
#endif

    free(data);
}

bool GoRanging::save(std::string filename)
{
    /* all buffers must have the same size */
    size_t array_length = _xval1.size();
    if (array_length == 0) {
        printf("Nothing to save\n");
        return true;
    }

    /* matio file descriptor */
    mat_t *matfp = Mat_CreateVer(filename.c_str(), NULL, MAT_FT_DEFAULT);
    if (matfp == NULL) {
        printf("mat file creation: FAIL\n");
        return false;
    }
    size_t dim[2] = {array_length, 1};
    matvar_t *mat_var;
    
    /* correction1 */    // eval(['save -mat ',datalocation,'/remote',nom,' xv* corr* df1 indic* SNR* code puissa*']);
    mat_var = Mat_VarCreate("correction1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_correction1[0], 0); // indice+corr
    Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE); //or MAT_COMPRESSION_ZLIB
    Mat_VarFree(mat_var);
    /* correction2 */
    mat_var = Mat_VarCreate("correction2", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_correction2[0], 0);
    Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE); //or MAT_COMPRESSION_ZLIB
    Mat_VarFree(mat_var);
    /* SNR1 */
    mat_var = Mat_VarCreate("SNR1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_SNR1[0], 0);
    Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE); //or MAT_COMPRESSION_ZLIB
    Mat_VarFree(mat_var);
    /* SNR2 */
    mat_var = Mat_VarCreate("SNR2", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_SNR2[0], 0);
    Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE); //or MAT_COMPRESSION_ZLIB
    Mat_VarFree(mat_var);
    /* df1 */
    mat_var = Mat_VarCreate("df1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_df1[0], 0);
    Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE); //or MAT_COMPRESSION_ZLIB
    Mat_VarFree(mat_var);
    /* df2 */
    mat_var = Mat_VarCreate("df2", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_df2[0], 0);
    Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE); //or MAT_COMPRESSION_ZLIB
    Mat_VarFree(mat_var);
    /* puissance1 */
    mat_var = Mat_VarCreate("puissance1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_puissance1[0], 0);
    Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE); //or MAT_COMPRESSION_ZLIB
    Mat_VarFree(mat_var);
    /* puissance2 */
    mat_var = Mat_VarCreate("puissance2", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_puissance2[0], 0);
    Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE); //or MAT_COMPRESSION_ZLIB
    Mat_VarFree(mat_var);
    /* code */
    //mat_var = Mat_VarCreate("code", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_code[0], 0);
    //Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE); //or MAT_COMPRESSION_ZLIB
    //Mat_VarFree(mat_var);
    
    /* xvalx */
    double xval1_r[array_length], xval1_i[array_length];
    double xval2_r[array_length], xval2_i[array_length];
    double xval1m1_r[array_length], xval1m1_i[array_length];
    double xval1p1_r[array_length], xval1p1_i[array_length];
    double xval2m1_r[array_length], xval2m1_i[array_length];
    double xval2p1_r[array_length], xval2p1_i[array_length];
    for (size_t i = 0; i < array_length; i++) {
        xval1_r[i] = _xval1[i].real();
        xval1_i[i] = _xval1[i].imag();
        xval2_r[i] = _xval2[i].real();
        xval2_i[i] = _xval2[i].imag();
        xval1m1_r[i] = _xval1m1[i].real();
        xval1m1_i[i] = _xval1m1[i].imag();
        xval1p1_r[i] = _xval1p1[i].real();
        xval1p1_i[i] = _xval1p1[i].imag();

        xval2m1_r[i] = _xval2m1[i].real();
        xval2m1_i[i] = _xval2m1[i].imag();
        xval2p1_r[i] = _xval2p1[i].real();
        xval2p1_i[i] = _xval2p1[i].imag();
    }
    mat_complex_split_t mat_cplx_xval1   = {xval1_r,   xval1_i};
    mat_complex_split_t mat_cplx_xval2   = {xval2_r,   xval2_i};
    mat_complex_split_t mat_cplx_xval1m1 = {xval1m1_r, xval1m1_i};
    mat_complex_split_t mat_cplx_xval1p1 = {xval1p1_r, xval1p1_i};
    mat_complex_split_t mat_cplx_xval2m1 = {xval2m1_r, xval2m1_i};
    mat_complex_split_t mat_cplx_xval2p1 = {xval2p1_r, xval2p1_i};

    mat_var = Mat_VarCreate("xval1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &mat_cplx_xval1, MAT_F_COMPLEX);
    if (mat_var == NULL) {
        printf("init error");
    }
    Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE); //or MAT_COMPRESSION_ZLIB
    Mat_VarFree(mat_var);

    mat_var = Mat_VarCreate("xval2", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &mat_cplx_xval2, MAT_F_COMPLEX);
    Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE); //or MAT_COMPRESSION_ZLIB
    Mat_VarFree(mat_var);
    mat_var = Mat_VarCreate("xval1m1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &mat_cplx_xval1m1, MAT_F_COMPLEX);
    Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE); //or MAT_COMPRESSION_ZLIB
    Mat_VarFree(mat_var);
    mat_var = Mat_VarCreate("xval1p1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &mat_cplx_xval1p1, MAT_F_COMPLEX);
    Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE); //or MAT_COMPRESSION_ZLIB
    Mat_VarFree(mat_var);
    mat_var = Mat_VarCreate("xval2m1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &mat_cplx_xval2m1, MAT_F_COMPLEX);
    Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE); //or MAT_COMPRESSION_ZLIB
    Mat_VarFree(mat_var);
    mat_var = Mat_VarCreate("xval2p1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &mat_cplx_xval2p1, MAT_F_COMPLEX);
    Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE); //or MAT_COMPRESSION_ZLIB
    Mat_VarFree(mat_var);
    
    Mat_Close(matfp);

    return true;
}

bool GoRanging::fill_fcode(const std::string &filename)
{
    FILE *prn_fd = fopen(filename.c_str(), "r");
    if (!prn_fd)
        return false;
    /* get size from file */
    fseek(prn_fd, 0, SEEK_END);
    size_t file_size = ftell(prn_fd);
    fseek(prn_fd, 0, SEEK_SET);

    /* FFT buffer length */
    size_t fft_size = 2 * file_size;
    _tcode.resize((2*Nint+1)*file_size*2);

    uint8_t *raw_prn = (uint8_t *)malloc(sizeof(uint8_t) * file_size);
    size_t ret = fread(raw_prn, sizeof(uint8_t), file_size, prn_fd);
    fclose(prn_fd);
    if (ret != file_size) {
        printf("fcode read: FAIL\n");
        return false;
    }

    _chan1 = (fftw_complex *)malloc(sizeof(fftw_complex) * fft_size);
    if (!_chan1) {
        printf("FFT chan1 alloc: FAIL\n");
        return false;
    }

    _result =
        (fftw_complex *) fftw_malloc(sizeof(fftw_complex) * fft_size);
    if (!_result) {
        printf("FFT result alloc: FAIL\n");
        return false;
    }

    _plan_a = fftw_plan_dft_1d(fft_size, _chan1, _result, FFTW_FORWARD, FFTW_ESTIMATE);

    std::vector<std::complex<double>> raw(fft_size, 0);
    for (size_t i = 0, ii=0; i < file_size; i++, ii+=2) {
        raw[ii].real((double)raw_prn[i]*2.-1.);   // interpolation = fs/fchip = 5 MHz/2.5 MHz
        raw[ii].imag(0);
        raw[ii+1].real((double)raw_prn[i]*2.-1.);
        raw[ii+1].imag(0);
    }
    for (size_t i = 0; i < fft_size; i++) {
        _chan1[i][0] = raw[i].real();
        _chan1[i][1] = raw[i].imag();
    }

    // fftw
    fftw_execute(_plan_a);

    // store conj
    for (size_t i = 0; i < 2 * file_size; i++)
        _fcode.push_back(std::conj(std::complex<double>(_result[i][0], _result[i][1])));
    printf("file size : %ld %ld\n", 2 * file_size, _fcode.size());

    for (size_t i = 0; i < raw.size(); i++) {
        _tcode[(Nint*2+1)*i]=real(raw[i]);
        _tcode[(Nint*2+1)*i+1]=real(raw[i]);
        _tcode[(Nint*2+1)*i+2]=real(raw[i]);
       }

    fftw_free(_chan1);
    fftw_free(_result);
    fftw_destroy_plan(_plan_a);
    free(raw_prn);
    return true;
}

std::vector<double> GoRanging::linspace(double start_in, double end_in, int num_in)
{ // https://gist.github.com/lorenzoriano/5414671

    std::vector<double> linspaced;

    double start = static_cast<double>(start_in);
    double end = static_cast<double>(end_in);
    double num = static_cast<double>(num_in);

    if (num == 0)
        return linspaced;
    if (num == 1)  {
        linspaced.push_back(start);
        return linspaced;
    }

    double delta = (end - start) / (num - 1);

    for(int i=0; i < num-1; ++i)
        linspaced.push_back(start + delta * i);

    linspaced.push_back(end);
    return linspaced;
}
    
template <typename T, typename A>
int GoRanging::arg_max(std::vector<T, A> const& vec) {
    return static_cast<int>(std::distance(vec.begin(), max_element(vec.begin(), vec.end(), 
        [] (std::complex<double> a, std::complex<double> b)
        {
            return (std::abs(a) < std::abs(b));
        })));
}

int main(int argc, char **argv) {
        int remote=0;
        if (argc>=4) remote=atoi(argv[3]); else printf("%s data.bin code.bin [remote=0]\n",argv[0]);
    GoRanging ranging(5e6, argv[1], argv[2], remote);
    ranging.compute();
    ranging.save("myfile.mat");

    return EXIT_SUCCESS;
}
