Very important in the Python file generated from GNU Radio Companion: make sure IQ imbalance correction is OFF
```
self.uhd_usrp_source_0.set_auto_iq_balance(False, 0)
self.uhd_usrp_source_0.set_auto_iq_balance(False, 1)
```
since the AD9361 seems to hate the signal it receives directly (following SAW bandpass filtering and attenuation)
from the FPGA and [continuoulsy adjusts IQ imbalance correction](https://lists.ettus.com/empathy/thread/6OYN6FHX77AGOCEUIXH4ZMLGPAQMY6PW)
otherwise.
