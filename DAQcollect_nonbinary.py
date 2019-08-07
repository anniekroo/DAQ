#!/usr/bin/env python


"""
    Wrapper call demonstrated:        ai_device.a_in_scan()

    Purpose:                          Performs a continuous scan of the range
                                      of A/D input channels

    Demonstration:                    Displays the analog input data for the
                                      range of user-specified channels using
                                      the first supported range and input mode

    Steps:
    1. Call get_daq_device_inventory() to get the list of available DAQ devices
    2. Create a DaqDevice object
    3. Call daq_device.get_ai_device() to get the ai_device object for the AI subsystem
    4. Verify the ai_device object is valid
    5. Call ai_device.get_info() to get the ai_info object for the AI subsystem
    6. Verify the analog input subsystem has a hardware pacer
    7. Call daq_device.connect() to establish a UL connection to the DAQ device
    8. Call ai_device.a_in_scan() to start the scan of A/D input channels
    9. Call ai_device.get_scan_status() to check the status of the background operation
    10. Display the data for each channel
    11. Call ai_device.scan_stop() to stop the background operation
    12. Call daq_device.disconnect() and daq_device.release() before exiting the process.
"""
from __future__ import print_function
from time import sleep
import time
import subprocess as sp
from os import system
from sys import stdout
import pickle
import numpy as np
from matplotlib import pyplot as plt
from uldaq import (get_daq_device_inventory, DaqDevice, AInScanFlag, ScanStatus,
                   ScanOption, create_float_buffer, InterfaceType, AiInputMode)
import keyboard


def main():
    daq_device = None
    ai_device = None
    status = ScanStatus.IDLE

    descriptor_index = 0
    range_index = 0
    interface_type = InterfaceType.USB
    low_channel = 0
    high_channel = 0
    rate = 100000                # Samples/second/channel
    buffer_length = 200000
    f_transmit = 36000          # fundamental frequency of transmitter
    channel_num = high_channel-low_channel+1
    samples_per_channel = int(float(buffer_length)/float(channel_num))
    file_length = 2             # Seconds
    rows_of_data = (float(file_length)/((float(buffer_length)/2)/(float(rate)*float(channel_num))))*((float(buffer_length)/2)/float(channel_num))
    print("NUMBER OF ROWS IN THE OUTPUT FILE:" +str(rows_of_data))
    scan_options = ScanOption.CONTINUOUS
    flags = AInScanFlag.DEFAULT

    #CONTROL ALGORITHM PARAMETERS:
    velocity = 1    #tune speed
    beta = 0.01        #tune turning
    heading = 0
    past_freq = f_transmit
    dH = -1.0001

    try:
        # Get descriptors for all of the available DAQ devices.
        devices = get_daq_device_inventory(interface_type)
        number_of_devices = len(devices)
        if number_of_devices == 0:
            raise Exception('Error: No DAQ devices found')

        print('Found', number_of_devices, 'DAQ device(s):')
        for i in range(number_of_devices):
            print('  ', devices[i].product_name, ' (', devices[i].unique_id, ')', sep='')

        # Create the DAQ device object associated with the specified descriptor index.
        daq_device = DaqDevice(devices[descriptor_index])

        # Get the AiDevice object and verify that it is valid.
        ai_device = daq_device.get_ai_device()
        if ai_device is None:
            raise Exception('Error: The DAQ device does not support analog input')

        # Verify that the specified device supports hardware pacing for analog input.
        ai_info = ai_device.get_info()
        if not ai_info.has_pacer():
            raise Exception('\nError: The specified DAQ device does not support hardware paced analog input')

        # Establish a connection to the DAQ device.
        descriptor = daq_device.get_descriptor()
        print('\nConnecting to', descriptor.dev_string, '- please wait...')
        daq_device.connect()

        # The default input mode is SINGLE_ENDED.
        input_mode = AiInputMode.SINGLE_ENDED
        # If SINGLE_ENDED input mode is not supported, set to DIFFERENTIAL.
        if ai_info.get_num_chans_by_mode(AiInputMode.SINGLE_ENDED) <= 0:
            input_mode = AiInputMode.DIFFERENTIAL

        # Get the number of channels and validate the high channel number.
        number_of_channels = ai_info.get_num_chans_by_mode(input_mode)
        if high_channel >= number_of_channels:
            high_channel = number_of_channels - 1
        channel_count = high_channel - low_channel + 1

        # Get a list of supported ranges and validate the range index.
        ranges = ai_info.get_ranges(input_mode)
        if range_index >= len(ranges):
            range_index = len(ranges) - 1

        # Allocate a buffer to receive the data.
        data = create_float_buffer(channel_count, samples_per_channel)

        print('\n', descriptor.dev_string, ' ready', sep='')
        print('    Function demonstrated: ai_device.a_in_scan()')
        print('    Channels: ', low_channel, '-', high_channel)
        print('    Input mode: ', input_mode.name)
        print('    Range: ', ranges[range_index].name)
        print('    Samples per channel: ', samples_per_channel)
        print('    Rate: ', rate, 'Hz')
        print('    Scan options:', display_scan_options(scan_options))
        try:
            input('\nHit ENTER to continue\n')
        except (NameError, SyntaxError):
            pass
        system('clear')
        print('\nHit q to exit\n')

        threshold = (float(len(data))/2) - (float(len(data))/2)%channel_count
        # Start the acquisition.
        rate = ai_device.a_in_scan(low_channel, high_channel, input_mode, ranges[range_index], samples_per_channel,
                                   rate, scan_options, flags, data)

        start=time.time()
        f=open('./data/'+'{:.6f}'.format(start)+".txt",'a')
                # REMOVED BINARY MODE 'ab' DUE TO ERROR ON BRENDAN'S LINUX MACHINE DUE TO 'str'
        old_index=0
        working=[0] * (channel_count+1)
        past_index = -1
        while True:
            #Get the status of the background operation
            status, transfer_status = ai_device.get_scan_status()

            if time.time()-start>=file_length:
                f.close
                start=time.time()
                f=open('./data/'+'{:.6f}'.format(start)+".txt",'a')
                # REMOVED BINARY MODE 'ab' DUE TO ERROR ON BRENDAN'S LINUX MACHINE DUE TO 'str'
            index = transfer_status.current_index
            if past_index<=threshold and index>threshold:
                data_range = range(int(threshold))
                data_fft, data_dump = dump_data(f, data, data_range, channel_count)
                #find fundamental frequency within 500Hz of f_transmit
                doppler_freqs, doppler_vals = fourier_analysis(data_fft,rate,f_transmit,500)
                #new heading
                past_freq, heading, dH = heading_adjust(doppler_freqs, doppler_vals, past_freq, beta, heading, dH)
                print('HEADING: %s     FREQ: %d    dH: %d' %(str(heading), past_freq,dH))
            if past_index>index:
                data_range = range(int(threshold),len(data))
                data_fft, data_dump = dump_data(f, data, data_range, channel_count)
                #find fundamental frequency within 500Hz of f_transmit
                doppler_freqs, doppler_vals = fourier_analysis(data_fft,rate,f_transmit,500)
                #new heading
                past_freq, heading, dH = heading_adjust(doppler_freqs, doppler_vals, past_freq, beta, heading, dH)
                print('HEADING: %s     FREQ: %d    dH: %d' %(str(heading), past_freq,dH))
            past_index = index
            #Quit data collection on keyboard press q
            if keyboard.is_pressed('q'):  # if key 'q' is pressed
                print('QUITTING!')
                break

    except Exception as e:
        print('OUTTER TRY FAILURE')
        print('\n', e)

    finally:
        if daq_device:
            # Stop the acquisition if it is still running.
            if status == ScanStatus.RUNNING:
                ai_device.scan_stop()
            if daq_device.is_connected():
                daq_device.disconnect()
            daq_device.release()

def dump_data(f, data, data_range, channel_count):
    '''
    Function to take data buffer and save the buffer in the range specified by
    data_range to a text file in the format of a csv. This will have as many
    columns as there are channels. It will also create a variable data_fft
    that contains all of the values of the first channel specified for more
    processing.
    '''
    data_dump = []
    data_fft = []
    for i in data_range:
        if i%channel_count == 0:
            row_data = str(data[i:i+channel_count])
            data_fft.append(data[i])
            data_dump.append(row_data[1:-1])
    s = "\n"
    f.write(s.join(data_dump)+'\n')
    return data_fft, data_dump

def fourier_analysis(data_fft, rate, f_transmit, doppler_range):
    '''
    Function that takes data from a single channel (data_fft) and takes the fourier
    transform. It then finds the maximum intensity within +- doppler_range from
    the transmit frequency (f_transmit).
    '''
    frequency_domain = np.fft.fftshift(abs(np.fft.fft(np.array(data_fft))))
    freqs = np.fft.fftshift(np.fft.fftfreq(len(data_fft),1/float(rate)))
    doppler_freqs = freqs[np.where(np.logical_and(freqs>=f_transmit-doppler_range, freqs<=f_transmit+doppler_range))]
    doppler_vals = frequency_domain[np.where(np.logical_and(freqs>=f_transmit-doppler_range, freqs<=f_transmit+doppler_range))]
    return doppler_freqs, doppler_vals

def heading_adjust(doppler_freqs,doppler_vals,past_freq,beta,heading,dH):
    '''
    Control loop that takes in frequency values and compares it to past frequencies
    to decide what heading to turn to.
    '''
    freq = doppler_freqs[np.argmax(doppler_vals)]
    dH = (freq-past_freq)*np.sign(dH)*beta
    heading = heading + dH
    return_val = sp.call("echo %s >> log.txt &"% str(heading), shell=True)
    return freq, heading, dH

def display_scan_options(bit_mask):
    options = []
    if bit_mask == ScanOption.DEFAULTIO:
        options.append(ScanOption.DEFAULTIO.name)
    for so in ScanOption:
        if so & bit_mask:
            options.append(so.name)
    return ', '.join(options)


def reset_cursor():
    stdout.write('\033[1;1H')


def clear_eol():
    stdout.write('\x1b[2K')



if __name__ == '__main__':
    main()
