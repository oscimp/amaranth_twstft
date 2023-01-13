#include <iostream>
#include <cstdio>
#include <vector>
#include <cmath>
#include <complex>
#include <algorithm>
#include <chrono>
#include <cstring>
#include <regex>
#include <thread>

#include <fftw3.h>
#include <matio.h>
#include <semaphore.h>

#define DISPLAY_TIME
//#undef DISPLAY_TIME

const uint32_t fs = (5e6);
const uint32_t Nint = 1;
// lo = np.exp(-1j * 2 * np.pi * tmp * temps)
const std::complex<double> tlo = std::complex<double>(0,-1) * (double)2.0f * M_PI;
//foffset=0
//frange=8000
//freq = np.linspace(-fs/2, (fs/2), num=int(fs), dtype=float)
//k=np.nonzero((np.array(freq) < 2*(foffset+frange)) & (np.array(freq) > 2*(foffset-frange)))
//k=k[0];
//temps = np.array(range(0, int(fs))) / fs

class GoRanging {
 public:
	GoRanging(double fs, const std::string & filename,
		  const std::string & prn_file, int remote, float foffset);
	~GoRanging();

	void compute();
	bool save(std::string filename);

 private:
	void thread_process_d1();
	void thread_process_d2();
	void _process_method(uint8_t chan_id);
	bool fill_fcode(const std::string & filename);
	 std::vector < double >linspace(double start_in, double end_in,
					int num_in);
	 template < typename T, typename A > int arg_max(std::vector < T,
							 A > const &vec);
	double _fs;
	size_t _fcode_len;
	size_t _ifft_size;
	uint8_t _nb_chan;
	float _foffset;
	std::vector < std::complex <double >>_fcode;
	std::vector < std::complex <double>*>dx_array;
	std::vector < double >_tcode;
	std::vector < double >_code;
	std::vector < double >_freq;
	std::vector < double >_temps;
	std::vector < double >_k;
	std::vector < std::vector < double >>_correction;
	std::vector < std::vector < double >>_dfx_array;
	std::vector < std::vector < double >>_puissance;
	std::vector < std::vector < double >>_puissancecode;
	std::vector < std::vector < double >>_SNRx;
	std::vector < std::vector < std::complex <double >>>_xvalx, _xvalxm1, _xvalxp1;
	std::string _filename;
	int _remote;
	FILE *_fd;
	/* fft */
	std::vector<std::complex<double>*> _chan_dx_array;
	std::vector<std::complex<double>*> _result_dx_array;
	std::vector<fftw_plan> _plan_a_dx;
	/* ifft */
	std::vector<std::complex<double>*> _chan_ifft_dx_array;
	std::vector<std::complex<double>*> _result_ifft_dx_array;
	std::vector<fftw_plan> _ifft_dx;
	int kmin, kmax;
	bool _must_stop;
	std::complex <double >_mean1;
	std::complex <double >_mean2;
	std::vector<sem_t> _sema_dx, _sema_dx_rdy;
	std::thread *_thread_d1, *_thread_d2;
};

GoRanging::GoRanging(double fs, const std::string & filename,
			 const std::string & prn_file, int remote, float foffset):_fs(fs),
	_fcode_len(0), _ifft_size(0), _nb_chan(remote==0?2:1), _foffset(foffset),
	_filename(filename), _remote(remote), _must_stop(false)
{
	_fd = fopen(filename.c_str(), "r");
	if (!_fd)
		throw std::runtime_error("Fail to open " + _filename);

#ifdef FFTW_THREADS
	if (fftw_init_threads() == 0)
		throw std::runtime_error("fftw_init_threads_failed");

	fftw_plan_with_nthreads(FFTW_THREADS);
#endif

	if (!fill_fcode(prn_file))
		throw std::runtime_error("Fail to retrieve fcode file");

	_fcode_len = _fcode.size();
	_ifft_size = _fcode_len * (2 * Nint + 1);

	printf("%ld %ld\n", _fcode_len, _ifft_size);

	dx_array.resize(2);
	dx_array[0] = new std::complex<double>[_fcode_len];
	dx_array[1] = new std::complex<double>[_fcode_len];
	_dfx_array.resize(2);

	_correction.resize(_nb_chan);
	_puissance.resize(_nb_chan);
	_puissancecode.resize(_nb_chan);
	_SNRx.resize(_nb_chan);
	_sema_dx.resize(_nb_chan);
	_sema_dx_rdy.resize(_nb_chan);
	_xvalx.resize(_nb_chan);
	_xvalxp1.resize(_nb_chan);
	_xvalxm1.resize(_nb_chan);

	/* fft */
	_chan_dx_array.resize(_nb_chan);
	_result_dx_array.resize(_nb_chan);
	_plan_a_dx.resize(_nb_chan);
	for (int i = 0; i < _nb_chan; i++) {
		_chan_dx_array[i] = new std::complex<double>[_fcode_len];
		if (!_chan_dx_array[i])
			throw std::runtime_error("Fail to allocate FFT input buffer");
		for (size_t ii = 0; ii < _fcode_len; ii++)
			_chan_dx_array[i][ii] = 0;
		_result_dx_array[i] = new std::complex<double>[_fcode_len];
		if (!_result_dx_array[i])
			throw std::runtime_error("Fail to allocate FFT output buffer");

		_plan_a_dx[i] = fftw_plan_dft_1d(_fcode_len,
					reinterpret_cast<fftw_complex*>(&_chan_dx_array[i][0]),
					reinterpret_cast<fftw_complex*>(&_result_dx_array[i][0]),
					FFTW_FORWARD, FFTW_ESTIMATE);
		if (!_plan_a_dx[i]) {
			throw std::runtime_error("Fail to initialize FFT plan A");
		}
	}
	/* ifft */
	_chan_ifft_dx_array.resize(_nb_chan);
	_result_ifft_dx_array.resize(_nb_chan);
	_ifft_dx.resize(_nb_chan);
	for (int i = 0; i < _nb_chan; i++) {
		_chan_ifft_dx_array[i] = new std::complex<double>[_ifft_size];
		if (!_chan_ifft_dx_array[i])
			throw std::runtime_error("Fail to allocate iFFT input buffer");
		_result_ifft_dx_array[i] = new std::complex<double>[_ifft_size];
		_ifft_dx[i] = fftw_plan_dft_1d(_ifft_size,
					reinterpret_cast<fftw_complex*>(&_chan_ifft_dx_array[i][0]),
					reinterpret_cast<fftw_complex*>(&_result_ifft_dx_array[i][0]),
					FFTW_BACKWARD, FFTW_ESTIMATE);
	}

	_freq = linspace(-fs / 2, fs / 2, _fcode_len);
	_temps.resize(_fcode_len);
	double frange = 8000;
	for (size_t i = 0; i < _fcode_len; i++) {
		if (_freq[i] < 2 * (_foffset + frange))
			kmax = i;
		if (_freq[i] <= 2 * (_foffset - frange))
			kmin = i;
		_temps[i] = i / fs;
	}

	sem_init(&_sema_dx[0], 0, 0);
	sem_init(&_sema_dx_rdy[0], 0, 0);
	_thread_d1 = new std::thread(&GoRanging::thread_process_d1, this);
	if (remote == 0) {
		sem_init(&_sema_dx[1], 0, 0);
		sem_init(&_sema_dx_rdy[1], 0, 0);
		_thread_d2 = new std::thread(&GoRanging::thread_process_d2, this);
	}

}

GoRanging::~GoRanging()
{
	_must_stop = true;
	sem_post(&_sema_dx[0]);
	_thread_d1->join();
	delete _thread_d1;
	if (_remote == 0) {
		sem_post(&_sema_dx[1]);
		_thread_d2->join();
		delete _thread_d2;
	}
	for (int i = 0; i < _nb_chan; i++) {
		fftw_free(_plan_a_dx[i]);
		delete _chan_dx_array[i];
		delete _result_dx_array[i];
		fftw_free(_ifft_dx[i]);
		delete _chan_ifft_dx_array[i];
		delete _result_ifft_dx_array[i];
	}
	fclose(_fd);
}

// analysis of d1
void GoRanging::thread_process_d1()
{
	_process_method(0);
}
// analysis of d2
void GoRanging::thread_process_d2()
{
	_process_method(1);
}

void GoRanging::_process_method(uint8_t chan_id)
{
	std::vector < std::complex <double >>y(_fcode_len, 0);
	std::vector < std::complex <double >>dx_fft(_fcode_len, 0);
	std::vector < std::complex <double >>dx1;
	std::vector < std::complex <double >>prnmap0x(_ifft_size, 0);
	int p = 0;
	std::complex<double>*mean = (chan_id == 0) ? &_mean1 : &_mean2; 
	std::complex<double> *dx = dx_array[chan_id];
	std::vector<double> *dfx = &_dfx_array[chan_id];
	/* fft */
	std::complex<double> *chan_dx = _chan_dx_array[chan_id];
	std::complex<double> *result_dx = _result_dx_array[chan_id];
	/* ifft */
	std::complex<double> *chan_ifft_dx = _chan_ifft_dx_array[chan_id];
	std::complex<double> *result_ifft_dx = _result_ifft_dx_array[chan_id];
	while (1) {
		sem_wait(&_sema_dx[chan_id]);
		if (_must_stop) {
			printf("fin\n");
			break;
		}
		// find frequency offset from d^2
		// fft & co for d1
		// dx_fft = np.fft.fftshift(np.abs(np.fft.fft(d1 * d1)))
		for (size_t i = 0; i < _fcode_len; i++) {
			dx[i] -= *mean;	//  d1=d1-mean(d1);   remove mean
			chan_dx[i] = dx[i] * dx[i];
		}
		fftw_execute(_plan_a_dx[chan_id]);	// d1^2  //  d22=fftshift(abs(fft(d1.^2))); % 0.1 Hz accuracy

		for (size_t i = 0; i < _fcode_len/2; i++) {
			// dx_fft=fftshift(fft(d1^2))
			dx_fft[i] = result_dx[i+_fcode_len/2];
			dx_fft[i+_fcode_len/2] = result_dx[i];
		}

		// tmp = dx_fft[k].argmax()+k[0]
		std::vector < std::complex <double >>subvector1;
		std::copy(dx_fft.begin() + kmin, dx_fft.begin() + kmax,
			  std::back_inserter(subvector1));
		int pos = arg_max(subvector1) + kmin;	// [~,df1(p)]=max(d22(k));df1(p)=df1(p)+k(1)-1;df1(p)=freq(df1(p))/2;offset1=df1(p);
		double df1 = _freq[pos] / 2.;
		dfx->push_back(df1);


		// lo = np.exp(-1j * 2 * np.pi * tmp * temps)
		std::complex <double >t = tlo * df1;
		for (size_t i = 0; i < _fcode_len; i++) {
			// lo=exp(-j*2*pi*df1(p)*temps); % frequency offset
			// y=d1.*lo;                     % frequency transposition
			chan_dx[i] = dx[i] * std::exp(t * _temps[i]);
		}

		// multmp1 = np.fft.fftshift(np.fft.fft(y) * fcode)
		double puissance = 0;
		fftw_execute(_plan_a_dx[chan_id]);	//  ffty=fft(y);
		for (size_t i = _fcode_len; i < _ifft_size - _fcode_len; i++)
			chan_ifft_dx[i] = 0;
		for (size_t i = 0; i < _fcode_len; i++) {
			y[i] = result_dx[i];	// y = FFT(d1*lo)
			int ii = (i < _fcode_len / 2) ? i : (i + (2 * _fcode_len));
			chan_ifft_dx[ii] = y[i] * _fcode[i];
			puissance += std::norm(y[i]);
		}

#ifdef DISPLAY_TIME
		//t_read = std::chrono::high_resolution_clock::now();
#endif
		fftw_execute(_ifft_dx[chan_id]);
		// prnmap0x=fftshift(ffty.*fcode);      % xcorr
		// prnmap0x=[zeros(length(y)*(Nint),1) ; prnmap0x ; zeros(length(y)*(Nint),1)]; % interpolation to 3x samp_rate
		memcpy(&prnmap0x[0], result_ifft_dx, sizeof(std::complex<double>) * _ifft_size);
		unsigned int indice1 = arg_max(prnmap0x);	//  [~,indice1(p)]=max(abs(prnmap0x));  % only one correlation peak
		double xval1 = std::abs(prnmap0x[indice1]);	//  xval1(p)=prnmap0x(indice1(p));
		double xval1m1 = std::abs(prnmap0x[indice1 - 1]);	//  xval1m1(p)=prnmap0x(indice1(p)-1);
		double xval1p1 = std::abs(prnmap0x[indice1 + 1]);	//  xval1p1(p)=prnmap0x(indice1(p)+1);
		double corr1 = (xval1m1 - xval1p1) / 2. / (xval1m1 + xval1p1 - 2 * xval1);	//  correction1_a(p)=(abs(prnmap0x(indice1(p)-1))-abs(prnmap0x(indice1(p)+1)))/(abs(prnmap0x(indice1(p)-1))+abs(prnmap0x(indice1(p)+1))-2*abs(prnmap0x(indice1(p))))/2;
		_correction[chan_id].push_back(indice1 + corr1);

		_xvalx[chan_id].push_back(prnmap0x[indice1]);
		_xvalxm1[chan_id].push_back(prnmap0x[indice1 - 1]);
		_xvalxp1[chan_id].push_back(prnmap0x[indice1 + 1]);
		printf("%d/%d %0.12lf\t%.3f\t", p, chan_id,
			   ((double)indice1 + corr1) / fs / (2 * Nint + 1.), df1);
//  % SNR computation
		//  yint=zeros(length(y)*(2*Nint+1),1);
		for (size_t i = _fcode_len; i < _ifft_size - _fcode_len; i++)
			chan_ifft_dx[i] = 0;
		for (size_t i = 0; i < _fcode_len; i++) {
			int ii =
				(i < _fcode_len / 2) ? i : (i + (2 * _fcode_len));
			chan_ifft_dx[ii] = y[i]; // yint(1:length(y)/2)=ffty(1:length(y)/2);
					                  // yint(end-length(y)/2+1:end)=ffty(length(y)/2+1:end);
		}
		fftw_execute(_ifft_dx[chan_id]);	// yint=ifft(yint);   vvv- _tcode is interpolated
		// codetmp=repelems(code,[[1:length(code)] ; ones(1,length(code))*(2*Nint+1)])'; % interpolate
		// re-use prnmap0x for a different purpose
		memcpy(&prnmap0x[0], result_ifft_dx, sizeof(std::complex<double>) * _ifft_size);

		std::rotate(prnmap0x.begin(), prnmap0x.begin() + indice1 - 1,
				prnmap0x.end());
		double SNR1r(0), SNR1i(0), SNR1s(0), puissance1code(0);
		std::complex<double> SNR1(0);
		for (size_t i = 0; i < _ifft_size; i++) {
			// yincode=[yint(indice1(p)-1:end) ; yint(1:indice1(p)-2)].*codetmp;
			prnmap0x[i] *= _tcode[i];
			SNR1 += prnmap0x[i];
		}
		SNR1 /= _ifft_size;
		// puissance1code(p)=mean(real(yincode))^2+mean(imag(yincode))^2;
		puissance1code = 10*log10(std::norm(SNR1));
		for (auto pm: prnmap0x) {
			//double R = real(prnmap0x[i] * _tcode[i]);	// puissance1total(p)=var(y);
			//double I = imag(prnmap0x[i] * _tcode[i]);
			//SNR1s += (R - SNR1r) * (R - SNR1r) + (I - SNR1i) * (I - SNR1i);	// (v-<v>)^2
			SNR1s += std::norm(pm - SNR1);
		}
		SNR1s /= _ifft_size;
		SNR1r = SNR1.real() * SNR1.real() / SNR1s;	// <.>^2/var
		SNR1i = SNR1.imag() * SNR1.imag() / SNR1s;
		printf("%.1lf\t%0.1lf\t", puissance,
			   10 * log10(SNR1r + SNR1i));
		_SNRx[chan_id].push_back(10 * log10(SNR1r + SNR1i));
		_puissancecode[chan_id].push_back(puissance1code);
		_puissance[chan_id].push_back(puissance);
		p++;
		sem_post(&_sema_dx_rdy[chan_id]);
	}
}

void GoRanging::compute()
{
	int16_t *data = (int16_t *) malloc(sizeof(int16_t) * _fcode_len * 4);
	std::vector < std::complex <double >>zero_vect(_fcode_len,
							   std::complex <double >(0, 0));
#ifdef DISPLAY_TIME
	//std::chrono::time_point < std::chrono::high_resolution_clock > t_read;
#endif

	int p = 0;
#ifdef DISPLAY_TIME
	auto t_start = std::chrono::high_resolution_clock::now();
#endif
	size_t res = fread(data, sizeof(int16_t), _fcode_len * 4, _fd);
	while (!_must_stop) {
		if (res < _fcode_len * 4) {
			printf("No more data\n");
			break;
		}

		_mean1 = std::complex<double>(0,0);
		_mean2 = std::complex<double>(0,0);
		// convert to complex
		for (size_t i = 0, ii = 0; i < _fcode_len; ii += 4, i++) {
			dx_array[0][i].real((double)data[ii + 0]);	// d=fread(f,length(fcode)*4,'int16');  % 1 code length
			                                    // d=d(1:2:end)+j*d(2:2:end);
			dx_array[0][i].imag((double)data[ii + 1]);	// d1=d(1:2:end);  % measurement
			dx_array[1][i].real((double)data[ii + 2]);	// d2=d(2:2:end);  % reference
			dx_array[1][i].imag((double)data[ii + 3]);
			_mean1 += dx_array[0][i];
			_mean2 += dx_array[1][i];
		}
		_mean1 /= _fcode_len;
		_mean2 /= _fcode_len;

		// thread process d1
		sem_post(&_sema_dx[0]);

		if (_remote == 0) {	// analysis of d2
			sem_post(&_sema_dx[1]);
			//sem_wait(&_sema_dx_rdy[1]);
		} 
		res = fread(data, sizeof(int16_t), _fcode_len * 4, _fd);
		if (_remote == 0)
			sem_wait(&_sema_dx_rdy[1]);
		sem_wait(&_sema_dx_rdy[0]);
		printf("\n");
		p++;
		//must_stop = true;
	}
#ifdef DISPLAY_TIME
	auto t_end = std::chrono::high_resolution_clock::now();
	double elapsed_time_ms =
		std::chrono::duration < double,
		std::milli > (t_end - t_start).count();
	printf("temps: %lf\n", elapsed_time_ms);
	/*elapsed_time_ms =
		std::chrono::duration < double,
		std::milli > (t_read - t_start).count();
	printf("read: %lf\n", elapsed_time_ms);
	elapsed_time_ms =
		std::chrono::duration < double,
		std::milli > (t_end - t_read).count();
	printf("end: %lf\n", elapsed_time_ms);*/
#endif

	free(data);
}

bool GoRanging::save(std::string filename)
{
#if 1
	/* all buffers must have the same size */
	size_t array_length = _xvalx[0].size();
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
	size_t dim[2] = { array_length, 1 };
	matvar_t *mat_var;

	/* correction1 */// eval(['save -mat ',datalocation,'/remote',nom,' xv* corr* df1 indic* SNR* code puissa*']);
	mat_var = Mat_VarCreate("correction1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_correction[0][0], 0);	// indice+corr
	Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE);	//or MAT_COMPRESSION_ZLIB
	Mat_VarFree(mat_var);
	/* SNR1 */
	mat_var = Mat_VarCreate("SNR1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_SNRx[0][0], 0);
	Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE);	//or MAT_COMPRESSION_ZLIB
	Mat_VarFree(mat_var);
	/* df1 */
	mat_var = Mat_VarCreate("df1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_dfx_array[0][0], 0);
	Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE);	//or MAT_COMPRESSION_ZLIB
	Mat_VarFree(mat_var);
	/* puissance1 */
	mat_var = Mat_VarCreate("puissance1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_puissance[0][0], 0);
	Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE);	//or MAT_COMPRESSION_ZLIB
	Mat_VarFree(mat_var);
	/* puissance1cpde */
	mat_var = Mat_VarCreate("puissance1code", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_puissancecode[0][0], 0);
	Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE);	//or MAT_COMPRESSION_ZLIB
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
		xval1_r[i] = _xvalx[0][i].real();
		xval1_i[i] = _xvalx[0][i].imag();
		xval1m1_r[i] = _xvalxm1[0][i].real();
		xval1m1_i[i] = _xvalxm1[0][i].imag();
		xval1p1_r[i] = _xvalxp1[0][i].real();
		xval1p1_i[i] = _xvalxp1[0][i].imag();

		if (_remote == 0) {
			xval2_r[i] = _xvalx[1][i].real();
			xval2_i[i] = _xvalx[1][i].imag();
			xval2m1_r[i] = _xvalxm1[1][i].real();
			xval2m1_i[i] = _xvalxm1[1][i].imag();
			xval2p1_r[i] = _xvalxp1[1][i].real();
			xval2p1_i[i] = _xvalxp1[1][i].imag();
		}
	}
	mat_complex_split_t mat_cplx_xval1 = { xval1_r, xval1_i };
	mat_complex_split_t mat_cplx_xval1m1 = { xval1m1_r, xval1m1_i };
	mat_complex_split_t mat_cplx_xval1p1 = { xval1p1_r, xval1p1_i };
	mat_complex_split_t mat_cplx_xval2 = { xval2_r, xval2_i };
	mat_complex_split_t mat_cplx_xval2m1 = { xval2m1_r, xval2m1_i };
	mat_complex_split_t mat_cplx_xval2p1 = { xval2p1_r, xval2p1_i };

	mat_var =
		Mat_VarCreate("xval1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim,
			  &mat_cplx_xval1, MAT_F_COMPLEX);
	if (mat_var == NULL) {
		printf("init error");
	}
	Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE);	//or MAT_COMPRESSION_ZLIB
	Mat_VarFree(mat_var);

	mat_var =
		Mat_VarCreate("xval1m1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim,
			  &mat_cplx_xval1m1, MAT_F_COMPLEX);
	Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE);	//or MAT_COMPRESSION_ZLIB
	Mat_VarFree(mat_var);
	mat_var =
		Mat_VarCreate("xval1p1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim,
			  &mat_cplx_xval1p1, MAT_F_COMPLEX);
	Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE);	//or MAT_COMPRESSION_ZLIB
	Mat_VarFree(mat_var);
	if (_remote == 0) {
		/* correction2 */
		mat_var = Mat_VarCreate("correction2", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_correction[1][0], 0);
		Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE);	//or MAT_COMPRESSION_ZLIB
		Mat_VarFree(mat_var);
		/* SNR2 */
		mat_var = Mat_VarCreate("SNR2", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_SNRx[1][0], 0);
		Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE);	//or MAT_COMPRESSION_ZLIB
		Mat_VarFree(mat_var);
		/* df2 */
		mat_var = Mat_VarCreate("df2", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_dfx_array[1][0], 0);
		Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE);	//or MAT_COMPRESSION_ZLIB
		Mat_VarFree(mat_var);
		/* puissance2 */
		mat_var = Mat_VarCreate("puissance2", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_puissance[1][0], 0);
		Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE);	//or MAT_COMPRESSION_ZLIB
		Mat_VarFree(mat_var);
		/* puissance2code */
		mat_var = Mat_VarCreate("puissance2code", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim, &_puissancecode[1][0], 0);
		Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE);	//or MAT_COMPRESSION_ZLIB
		Mat_VarFree(mat_var);
		mat_var =
			Mat_VarCreate("xval2", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim,
				  &mat_cplx_xval2, MAT_F_COMPLEX);
		Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE);	//or MAT_COMPRESSION_ZLIB
		Mat_VarFree(mat_var);
		mat_var =
			Mat_VarCreate("xval2m1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim,
				  &mat_cplx_xval2m1, MAT_F_COMPLEX);
		Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE);	//or MAT_COMPRESSION_ZLIB
		Mat_VarFree(mat_var);
		mat_var =
			Mat_VarCreate("xval2p1", MAT_C_DOUBLE, MAT_T_DOUBLE, 2, dim,
				  &mat_cplx_xval2p1, MAT_F_COMPLEX);
		Mat_VarWrite(matfp, mat_var, MAT_COMPRESSION_NONE);	//or MAT_COMPRESSION_ZLIB
		Mat_VarFree(mat_var);
	}

	Mat_Close(matfp);
#endif
	return true;
}

bool GoRanging::fill_fcode(const std::string & filename)
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
	_tcode.resize((2 * Nint + 1) * file_size * 2);

	uint8_t *raw_prn = (uint8_t *) malloc(sizeof(uint8_t) * file_size);
	size_t ret = fread(raw_prn, sizeof(uint8_t), file_size, prn_fd);
	fclose(prn_fd);
	if (ret != file_size) {
		printf("fcode read: FAIL\n");
		return false;
	}

	fftw_complex *_chan_d2 = (fftw_complex *) malloc(sizeof(fftw_complex) * fft_size);
	if (!_chan_d2) {
		printf("FFT chan1 alloc: FAIL\n");
		return false;
	}

	fftw_complex *_result_d2 = (fftw_complex *) fftw_malloc(sizeof(fftw_complex) * fft_size);
	if (!_result_d2) {
		printf("FFT result alloc: FAIL\n");
		return false;
	}

	fftw_plan _plan_a_d1 =
		fftw_plan_dft_1d(fft_size, _chan_d2, _result_d2, FFTW_FORWARD,
				 FFTW_ESTIMATE);

	std::vector < std::complex <double >>raw(fft_size, 0);
	for (size_t i = 0, ii = 0; i < file_size; i++, ii += 2) {
		raw[ii].real((double)raw_prn[i] * 2. - 1.);	// interpolation = fs/fchip = 5 MHz/2.5 MHz
		raw[ii].imag(0);
		raw[ii + 1].real((double)raw_prn[i] * 2. - 1.);
		raw[ii + 1].imag(0);
	}
	for (size_t i = 0; i < fft_size; i++) {
		_chan_d2[i][0] = raw[i].real();
		_chan_d2[i][1] = raw[i].imag();
	}

	// fftw
	fftw_execute(_plan_a_d1);

	// store conj
	for (size_t i = 0; i < 2 * file_size; i++)
		_fcode.push_back(std::conj(std::complex <double >(_result_d2[i][0],
							 _result_d2[i][1])));
	printf("file size : %ld %ld\n", 2 * file_size, _fcode.size());

	for (size_t i = 0; i < raw.size(); i++) {
		_tcode[(Nint * 2 + 1) * i] = real(raw[i]);
		_tcode[(Nint * 2 + 1) * i + 1] = real(raw[i]);
		_tcode[(Nint * 2 + 1) * i + 2] = real(raw[i]);
	}

	fftw_free(_chan_d2);
	fftw_free(_result_d2);
	fftw_destroy_plan(_plan_a_d1);
	free(raw_prn);
	return true;
}

std::vector < double >GoRanging::linspace(double start_in, double end_in,
					  int num_in)
{				// https://gist.github.com/lorenzoriano/5414671

	std::vector < double >linspaced;

	double start = static_cast < double >(start_in);
	double end = static_cast < double >(end_in);
	double num = static_cast < double >(num_in);

	if (num == 0)
		return linspaced;
	if (num == 1) {
		linspaced.push_back(start);
		return linspaced;
	}

	double delta = (end - start) / (num - 1);

	for (int i = 0; i < num - 1; ++i)
		linspaced.push_back(start + delta * i);

	linspaced.push_back(end);
	return linspaced;
}

template < typename T, typename A >
	int GoRanging::arg_max(std::vector < T, A > const &vec)
{
	return static_cast <
		int >(std::
		  distance(vec.begin(),
				max_element(vec.begin(), vec.end(),
				[](std::complex <double >a,
				std::complex <double >b) {
				return (std::abs(a) < std::abs(b));}
			   )));
}

int main(int argc, char **argv)
{
	int remote = 0;
	float foffset=0.;
	printf("%s data.bin code.bin [remote=0] [foffset=0.]\n", argv[0]);
	if (argc >= 4)
		remote = atoi(argv[3]);
	if (argc >= 5)
		foffset = atof(argv[4]); // 2 * (_foffset + frange) with frange=8 kHz
	std::string filename = argv[1];
	std::regex e ("([^ ]*)(.bin)");   // matches words beginning by "sub"
	std::string matname = std::regex_replace (filename,e,"$1.mat");
	GoRanging ranging(5e6, filename, argv[2], remote, foffset);
	ranging.compute();
	ranging.save(matname);

	return EXIT_SUCCESS;
}
