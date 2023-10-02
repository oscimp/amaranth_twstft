all: rx rxcomplex

FFTW_THREADS?=0
ifneq ($(FFTW_THREADS), 0)
        CXXFLAGS += -DFFTW_THREADS=$(FFTW_THREADS)
        LDFLAGS += -lfftw3_threads
endif

rx: rx.cpp
	g++ $(CXXFLAGS) -Wall -o rx rx.cpp -L/usr/local/lib -lfftw3 -lgsl -lopenblas $(LDFLAGS)
	# clang++ -S -emit-llvm rx.cpp -o - | /usr/lib/llvm-16/bin/opt -analyze -dot-callgraph

rxcomplex: rxcomplex.cpp
	g++ $(CXXFLAGS) -Wall -o rxcomplex rxcomplex.cpp -L/usr/local/lib -lfftw3 -lgsl -lopenblas $(LDFLAGS)

run:
	./rx ./data.bin

clean:
	rm rx rxcomplex
