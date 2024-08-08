import ctypes
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok

# Determine the base directory where the app is running
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define the paths to the necessary dynamic libraries
libiomp5_path = os.path.join(base_dir, "libiomp5.dylib")
libpicoipp_path = os.path.join(base_dir,  "libpicoipp.dylib")
libps4000_path = os.path.join(base_dir,  "libps4000.dylib")
print('base dir is ', base_dir)
# Check if the libraries exist
for lib_path in [libiomp5_path, libpicoipp_path, libps4000_path]:
    if not os.path.exists(lib_path):
        sys.exit(f"Library not found at {lib_path}")

# Load the necessary libraries
ctypes.CDLL(libiomp5_path)
ctypes.CDLL(libpicoipp_path)
ps = ctypes.CDLL(libps4000_path)

# Your existing code to use the PicoSDK library...

# Create chandle and status ready for use
chandle = ctypes.c_int16()
status = {}
print('so far so good')

def calculate_fft():
    try:
        # Open 4000 series PicoScope
        status["openunit"] = ps.ps4000OpenUnit(ctypes.byref(chandle))
        assert_pico_ok(status["openunit"])

        # Set up channels (A and B for demonstration)
        status["setChA"] = ps.ps4000SetChannel(chandle, 0, 1, 1, 7)  # Assuming channel A and 2V range
        assert_pico_ok(status["setChA"])
        status["setChB"] = ps.ps4000SetChannel(chandle, 1, 1, 1, 7)  # Assuming channel B and 2V range
        assert_pico_ok(status["setChB"])

        # Set up single trigger (if needed)
        status["trigger"] = ps.ps4000SetSimpleTrigger(chandle, 1, 0, 1024, 2, 0, 1000)
        assert_pico_ok(status["trigger"])

        # Set number of pre and post trigger samples to be collected
        preTriggerSamples = 0
        postTriggerSamples = 2500
        maxSamples = preTriggerSamples + postTriggerSamples

        # Get timebase information
        timebase = 8
        timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int32()
        oversample = ctypes.c_int16(1)
        status["getTimebase2"] = ps.ps4000GetTimebase2(chandle, timebase, maxSamples, ctypes.byref(timeIntervalns), oversample, ctypes.byref(returnedMaxSamples), 0)
        assert_pico_ok(status["getTimebase2"])

        # Allocate buffers
        bufferAMax = (ctypes.c_int16 * maxSamples)()
        bufferAMin = (ctypes.c_int16 * maxSamples)()  # Used for downsampling, not required here
        bufferBMax = (ctypes.c_int16 * maxSamples)()
        bufferBMin = (ctypes.c_int16 * maxSamples)()

        # Set data buffer location
        status["setDataBuffersA"] = ps.ps4000SetDataBuffers(chandle, 0, ctypes.byref(bufferAMax), ctypes.byref(bufferAMin), maxSamples)
        assert_pico_ok(status["setDataBuffersA"])
        status["setDataBuffersB"] = ps.ps4000SetDataBuffers(chandle, 1, ctypes.byref(bufferBMax), ctypes.byref(bufferBMin), maxSamples)
        assert_pico_ok(status["setDataBuffersB"])

        # Number of FFT averages
        numAverages = 10
        fft_accumulated = np.zeros(maxSamples//2, dtype=float)

        for _ in range(numAverages):
            # Run block capture
            status["runBlock"] = ps.ps4000RunBlock(chandle, preTriggerSamples, postTriggerSamples, timebase, oversample, None, 0, None, None)
            assert_pico_ok(status["runBlock"])

            # Wait for data collection to finish
            ready = ctypes.c_int16(0)
            check = ctypes.c_int16(0)
            while ready.value == check.value:
                status["isReady"] = ps.ps4000IsReady(chandle, ctypes.byref(ready))

            # Retrieve data
            cmaxSamples = ctypes.c_int32(maxSamples)
            overflow = ctypes.c_int16()
            status["getValues"] = ps.ps4000GetValues(chandle, 0, ctypes.byref(cmaxSamples), 0, 0, 0, ctypes.byref(overflow))
            assert_pico_ok(status["getValues"])

            # Convert data to mV
            maxADC = ctypes.c_int16(32767)
            adc2mVChAMax = adc2mV(bufferAMax, 7, maxADC)  # Assuming 2V range for mV conversion

            # Perform FFT
            fft_data = np.fft.fft(adc2mVChAMax)
            fft_data = np.abs(fft_data[:len(fft_data)//2])  # Keep only positive frequencies

            # Accumulate FFT results
            fft_accumulated += fft_data

        # Average the FFT results
        fft_averaged = fft_accumulated / numAverages

        # Create frequency data
        freq = np.fft.fftfreq(maxSamples, d=timeIntervalns.value * 1e-9)[:maxSamples//2]

        # Plot the averaged FFT
        plt.plot(freq, fft_averaged)
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Amplitude')
        plt.title('Averaged FFT')
        plt.show()

        # Stop the scope
        status["stop"] = ps.ps4000Stop(chandle)
        assert_pico_ok(status["stop"])

        # Close unit
        status["close"] = ps.ps4000CloseUnit(chandle)
        assert_pico_ok(status["close"])

        # Display status returns
        print(status)
        return status
    except Exception as e:
        print(e)
        return e
# calculate_fft()