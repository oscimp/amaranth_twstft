#include <uhd/usrp/multi_usrp.hpp>
#include <uhd/utils/safe_main.hpp>
#include <uhd/utils/thread.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/format.hpp>
#include <boost/program_options.hpp>
#include <chrono>
#include <complex>
#include <iostream>
#include <thread>

#include <fstream>
#include <csignal>
#include <complex>
#include <thread>

namespace po = boost::program_options;

int UHD_SAFE_MAIN(int argc, char* argv[])
{
    // variables to be set by po
    std::string args, sync, subdev, channel_list;
    double seconds_in_future;
    size_t total_num_samps;
    double rate, freq, gain, lo_offset;

    // setup the program options
    po::options_description desc("Allowed options");
    // clang-format off
    desc.add_options()
        ("help", "help message")
        ("args", po::value<std::string>(&args)->default_value(""), "single uhd device address args")
        ("secs", po::value<double>(&seconds_in_future)->default_value(1.5), "number of seconds in the future to receive")
        ("nsamps", po::value<size_t>(&total_num_samps)->default_value(5e6*60*5.5*2), "total number of samples to receive")
        ("rate", po::value<double>(&rate)->default_value(5e6), "rate of incoming samples")
        ("freq", po::value<double>(&freq)->default_value(70e6), "center frequency")
        ("lo_offset", po::value<double>(&lo_offset)->default_value(0), "frequency offset")
        ("sync", po::value<std::string>(&sync)->default_value("pps"), "synchronization method: now, pps, mimo")
        ("gain", po::value<double>(&gain)->default_value(70), "gain for the RF chain")
        ("subdev", po::value<std::string>(&subdev)->default_value("A:0 B:0"), "subdev spec (homogeneous across motherboards)")
        ("channels", po::value<std::string>(&channel_list)->default_value("0,1"), "which channel(s) to use (specify \"0\", \"1\", \"0,1\", etc)")
    ;
    // clang-format on
    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);
    po::notify(vm);

    // print the help message
    if (vm.count("help")) {
        std::cout << boost::format("UHD RX Multi Samples %s") % desc << std::endl;
        std::cout
            << "    This is a demonstration of how to receive aligned data from multiple "
               "channels.\n"
               "    This example can receive from multiple DSPs, multiple motherboards, "
               "or both.\n"
               "    The MIMO cable or PPS can be used to synchronize the configuration. "
               "See --sync\n"
               "\n"
               "    Specify --subdev to select multiple channels per motherboard.\n"
               "      Ex: --subdev=\"0:A 0:B\" to get 2 channels on a Basic RX.\n"
               "\n"
               "    Specify --args to select multiple motherboards in a configuration.\n"
               "      Ex: --args=\"addr0=192.168.10.2, addr1=192.168.10.3\"\n"
            << std::endl;
        return ~0;
    }

    // create a usrp device
    std::cout << std::endl;
    std::cout << boost::format("Creating the usrp device with: %s...") % args
              << std::endl;
    uhd::usrp::multi_usrp::sptr usrp = uhd::usrp::multi_usrp::make(args);

    // always select the subdevice first, the channel mapping affects the other settings
    if (vm.count("subdev"))
        usrp->set_rx_subdev_spec(subdev); // sets across all mboards

    std::cout << boost::format("Using Device: %s") % usrp->get_pp_string() << std::endl;

    // set the rx sample rate (sets across all channels)
    std::cout << boost::format("Setting RX Rate: %f Msps...") % (rate / 1e6) << std::endl;
    usrp->set_rx_rate(rate);
    std::cout << boost::format("Actual RX Rate: %f Msps...") % (usrp->get_rx_rate() / 1e6)
              << std::endl
              << std::endl;

    // set the center frequency
    std::cout << boost::format("Setting RX Freq: %f MHz...") % (freq / 1e6)
                  << std::endl;
    std::cout << boost::format("Setting RX LO Offset: %f MHz...") % (lo_offset / 1e6)
                  << std::endl;
    uhd::tune_request_t tune_request(freq, lo_offset);
    usrp->set_rx_freq(tune_request, 0);
    usrp->set_rx_freq(tune_request, 1);
        std::cout << boost::format("Actual RX Freq: %f MHz...")
                         % (usrp->get_rx_freq(0) / 1e6)
                  << std::endl
                  << std::endl;

    // set the rf gain
    std::cout << boost::format("Setting RX Gain: %f dB...") % gain << std::endl;
    usrp->set_rx_gain(gain, 0);
    usrp->set_rx_gain(gain, 1);
    std::cout << boost::format("Actual RX Gain: %f dB...")
                         % usrp->get_rx_gain(0)
                  << std::endl
                  << std::endl;

    // set the antenna
//   if (vm.count("ant"))
//        usrp->set_rx_antenna(ant, channel);

    std::cout << boost::format("Setting device timestamp to 0...") << std::endl;
    if (sync == "now") {
        // This is not a true time lock, the devices will be off by a few RTT.
        // Rather, this is just to allow for demonstration of the code below.
        usrp->set_time_now(uhd::time_spec_t(0.0));
    } else if (sync == "pps") {
        usrp->set_clock_source("external"); // JMF: external frequency source
        usrp->set_time_source("external");
        usrp->set_time_unknown_pps(uhd::time_spec_t(0.0));
        std::this_thread::sleep_for(std::chrono::seconds(1)); // wait for pps sync pulse
    } else if (sync == "mimo") {
        UHD_ASSERT_THROW(usrp->get_num_mboards() == 2);

        // make mboard 1 a slave over the MIMO Cable
        usrp->set_clock_source("mimo", 1);
        usrp->set_time_source("mimo", 1);

        // set time on the master (mboard 0)
        usrp->set_time_now(uhd::time_spec_t(0.0), 0);

        // sleep a bit while the slave locks its time to the master
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    // detect which channels to use
    std::vector<std::string> channel_strings;
    std::vector<size_t> channel_nums;
    boost::split(channel_strings, channel_list, boost::is_any_of("\"',"));
    for (size_t ch = 0; ch < channel_strings.size(); ch++) {
        size_t chan = std::stoi(channel_strings[ch]);
        if (chan >= usrp->get_rx_num_channels()) {
            throw std::runtime_error("Invalid channel(s) specified.");
        } else
            channel_nums.push_back(std::stoi(channel_strings[ch]));
    }

    // create a receive streamer
    // linearly map channels (index0 = channel0, index1 = channel1, ...)
    uhd::stream_args_t stream_args("sc8","sc8"); // JMF
    stream_args.channels             = channel_nums;
    uhd::rx_streamer::sptr rx_stream = usrp->get_rx_stream(stream_args);

    // setup streaming
    std::cout << std::endl;
    std::cout << boost::format("Begin streaming %u samples, %f seconds in the future...")
                     % total_num_samps % seconds_in_future
              << std::endl;
    uhd::stream_cmd_t stream_cmd(uhd::stream_cmd_t::STREAM_MODE_START_CONTINUOUS); // STREAM_MODE_NUM_SAMPS_AND_DONE);
    stream_cmd.num_samps  = total_num_samps;
    stream_cmd.stream_now = false;
    stream_cmd.time_spec  = uhd::time_spec_t(seconds_in_future);
    rx_stream->issue_stream_cmd(stream_cmd); // tells all channels to stream

    // meta-data will be filled in by recv()
    uhd::rx_metadata_t md;

    // allocate buffers to receive with samples (one buffer per channel)
    const size_t samps_per_buff = rx_stream->get_max_num_samps();
    std::vector<std::vector<std::complex<char>>> buffs(
        usrp->get_rx_num_channels(), std::vector<std::complex<char>>(samps_per_buff));

    // create a vector of pointers to point to each of the channel buffers
    std::vector<std::complex<char>*> buff_ptrs;
    for (size_t i = 0; i < buffs.size(); i++)
        buff_ptrs.push_back(&buffs[i].front());

    // the first call to recv() will block this many seconds before receiving
    double timeout = seconds_in_future + 0.1; // timeout (delay before receive + padding)

    std::ofstream outfile1, outfile2;
    outfile1.open("/data/file1.bin", std::ofstream::binary);
    outfile2.open("/data/file2.bin", std::ofstream::binary);

    size_t num_acc_samps = 0; // number of accumulated samples
//for (int jmf=0;jmf<6;jmf++)   // 8 GB RPi4
   {num_acc_samps = 0; // number of accumulated samples
    while (num_acc_samps < total_num_samps) {
        // receive a single packet
        size_t num_rx_samps = rx_stream->recv(buff_ptrs, samps_per_buff, md, timeout);
        if (num_rx_samps!=samps_per_buff) {printf("!");fflush(stdout);}

        // use a small timeout for subsequent packets
        timeout = 0.1;

        // handle the error code
        if (md.error_code == uhd::rx_metadata_t::ERROR_CODE_TIMEOUT)
            break;
        if (md.error_code != uhd::rx_metadata_t::ERROR_CODE_NONE) {
            throw std::runtime_error(
                str(boost::format("Receiver error %s") % md.strerror()));
        }
        if (md.error_code == uhd::rx_metadata_t::ERROR_CODE_OVERFLOW){
            std::cerr << "overflow\n" << std::endl;
            }
        outfile1.write( (const char*)&buffs[0].front(), samps_per_buff*sizeof(std::complex<char>));
        outfile2.write( (const char*)&buffs[1].front(), samps_per_buff*sizeof(std::complex<char>));
        num_acc_samps += num_rx_samps;
    }
  }

        if (num_acc_samps < total_num_samps)
           std::cerr << "Receive timeout before all samples received..." << std::endl;

    // finished
    stream_cmd.stream_mode = uhd::stream_cmd_t::STREAM_MODE_STOP_CONTINUOUS;
    rx_stream->issue_stream_cmd(stream_cmd);

    std::cout << std::endl << "Done!" << std::endl << std::endl;
    if (outfile1.is_open()) { outfile1.close(); }
    if (outfile2.is_open()) { outfile2.close(); }
    return EXIT_SUCCESS;
}
