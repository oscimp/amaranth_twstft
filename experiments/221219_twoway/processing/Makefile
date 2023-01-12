ifneq ($(BR_DIR),)
BIN_PATH = $(BR_DIR)/output/host/bin/
CXX      = $(BIN_PATH)$(CROSS_COMPILE)g++
else
CXX ?= g++
endif

PKG_CONFIG ?= $(BIN_PATH)pkg-config
CXXFLAGS = $(shell $(PKG_CONFIG) --cflags fftw3 matio) -std=c++11
LDFLAGS  = $(shell $(PKG_CONFIG) --libs fftw3 matio) -std=c++11

FFTW_THREADS?=0
ifeq ($(FFTW_THREADS), 1)
	CXXFLAGS += -DFFTW_THREADS=1
	LDFLAGS += -lfftw3_threads
endif

CXXFLAGS += -O3 -Wall
LDFLAGS  += -O3 -Wall
CXXFLAGS += -g
LDFLAGS  += -g
SRC=main.cpp
OBJS=$(SRC:.cpp=.o)
DEST=app

all: $(DEST)

$(DEST): $(OBJS)
	$(CXX) -o $@ $^ $(LDFLAGS)

%.o:%.cpp
	$(CXX) $(CXXFLAGS) -o $@ -c $<
clean:
	@rm -rf $(DEST) *.o
