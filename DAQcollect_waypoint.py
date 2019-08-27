#!/usr/bin/env py
"""
    To Run:                           'python DAQcollect.py' (for regular write mode) or
                                      'python DAQcollect.py b' (for binary write mode)

    Authors:                          Brendan O'Neill, Anne Kroo, and Chris Dolan
                                      July 2019
                                      SciBotics Lab
                                      Woods Hole Oceanographic Institute

    Code Derived From:                uldaq sample code 'a_in_scan()'

    Purpose:                          Performs a continuous scan of the range
                                      of A/D input channels, dumps the data to a
                                      .txt file in the subdirectory data,
                                      performs fourier analysis on the data
                                      and creates/updates a heading to maximize
                                      the doppler shift.

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
    10. Wait until the buffer has filled half or entirely full
    11. Dump the availible half of the buffer into a .txt file whos name is the unix time
    12. Take the fourier transform and identify a max frequency within a range
    13. Use the max frequency to update a desired heading state
    14. Call ai_device.scan_stop() to stop the background operation upon q keypress
    15. Call daq_device.disconnect() and daq_device.release() before exiting the process.
"""
from __future__ import print_function
from time import sleep
import time
import subprocess as sp
from os import system
from sys import (stdout,argv)
import numpy as np
import math
from uldaq import (get_daq_device_inventory, DaqDevice, AInScanFlag, ScanStatus,
                   ScanOption, create_float_buffer, InterfaceType, AiInputMode)

def main(data_write_mode = ''):
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
        print("    Output File Rows:" +str(rows_of_data))

        try:
            input('\nHit ENTER to continue\n')
        except (NameError, SyntaxError):
            pass
        system('clear')
        print('\nHit ^C to exit\n')

        #Set up threshold for where the dumps should occur in the buffer
        #Currently configured for dumping half of the buffer
        threshold = (float(len(data))/2) - (float(len(data))/2)%channel_count
        data_range = [range(int(threshold)),range(int(threshold),len(data))]

        #Setting up whether or not to write in binary mode
        write_mode = 'w'+data_write_mode

        # Start the acquisition.
        rate = ai_device.a_in_scan(low_channel, high_channel, input_mode, ranges[range_index], samples_per_channel,
                                   rate, scan_options, flags, data)
        #open first text file
        start=time.time()
        f=open('./data/'+'{:.6f}'.format(start)+".txt",write_mode)

        try:
            past_index = -1         #Initiated at -1 to because index is -1 until buffer is written to
            while True:
                #Get the status of the background operation
                status, transfer_status = ai_device.get_scan_status()

                #Make new file after fixed amount of time set by 'file_length'
                if time.time()-start>=file_length:
                    f.close
                    start=time.time()
                    f=open('./data/'+'{:.6f}'.format(start)+".txt",write_mode)

                #get current index in filling the buffer to know when to clear it
                index = transfer_status.current_index

                #write half buffer to txt file, find max freq, and update heading if buffer fills past halfway point
                if past_index<=threshold and index>threshold:
                    #dumps data
                    data_fft, data_dump = dump_data(f, data, data_range[0], channel_count)
                    #find fundamental frequency within 500Hz of f_transmit
                    freq = fourier_analysis(data_fft,rate,f_transmit,500)
                    #new heading
                    past_freq, heading, dH = heading_adjust(freq, past_freq, beta, heading, dH)
                    print('HEADING: %s     FREQ: %d    dH: %d' %(str(heading), past_freq,dH))

                    nav_solution(dH,heading)

                #write half buffer to txt file, find max freq, and update heading if buffer filled to end and is overwriting first half
                if past_index>index:
                    #dumps data
                    data_fft, data_dump = dump_data(f, data, data_range[1], channel_count)
                    #find fundamental frequency within 500Hz of f_transmit
                    freq = fourier_analysis(data_fft,rate,f_transmit,500)
                    #new heading
                    past_freq, heading, dH = heading_adjust(freq, past_freq, beta, heading, dH)
                    print('HEADING: %s     FREQ: %d    dH: %d' %(str(heading), past_freq,dH))

                    nav_solution(dH,heading)

                past_index = index

        except KeyboardInterrupt:
            pass

    except Exception as e:
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
    data_dump = []      #initiate variable to store lists of all channel values for each timestep
    data_fft = []       #initiate variable to store lowest channel values
    #restructure data to be meaningful
    for i in data_range:
        if i%channel_count == 0:
            row_data = str(data[i:i+channel_count])
            data_fft.append(data[i])
            data_dump.append(row_data[1:-1])
    s = "\n"
    #makes one big csv formatted text file from all channel data
    f.write(s.join(data_dump)+'\n')
    return data_fft, data_dump

def fourier_analysis(data_fft, rate, f_transmit, doppler_range):
    '''
        Function that takes data from a single channel (data_fft) and takes the fourier
        transform. It then finds the maximum intensity within +- doppler_range from
        the transmit frequency (f_transmit).
    '''
    frequency_domain = np.fft.fftshift(abs(np.fft.fft(np.array(data_fft))))     #takes the real part of the fourier transform
    freqs = np.fft.fftshift(np.fft.fftfreq(len(data_fft),1/float(rate)))        #defines frequencies coorisponding to fourier transform values
    doppler_freqs = freqs[np.where(np.logical_and(freqs>=f_transmit-doppler_range, freqs<=f_transmit+doppler_range))]   #pulls section of fourier values
    doppler_vals = frequency_domain[np.where(np.logical_and(freqs>=f_transmit-doppler_range, freqs<=f_transmit+doppler_range))] #pulls section of coorisponding frequency values
    freq = doppler_freqs[np.argmax(doppler_vals)]       #finds the frequency with the max intensity within doppler range
    return freq

def heading_adjust(freq,past_freq,beta,heading,dH):
    '''
        Control loop that takes in frequency values and compares it to past frequencies
        to decide what heading to turn to. Saves heading values to log.txt
    '''
    dH = (freq-past_freq)*np.sign(dH)*beta  #finds the desired change in heading
    heading = heading + dH                  #establishes new heading
    return_val = sp.call("echo %s >> log.txt &"% str(heading), shell=True)      #echos heading into log.txt file for jetyak to interact with
    return freq, heading, dH

def display_scan_options(bit_mask):
    '''
        Function to display setup options
    '''
    options = []
    if bit_mask == ScanOption.DEFAULTIO:
        options.append(ScanOption.DEFAULTIO.name)
    for so in ScanOption:
        if so & bit_mask:
            options.append(so.name)
    return ', '.join(options)

def nav_solution(dH,heading):
    '''
    Function to display a target waypoint based off a desired heading
    The target waypoint is based off an assumed lat/long of 0/0
    This can be adjusted to take in a known position based on vehicle sensors or
    can reset to 0/0 every iteration

    '''

    R = 6378100 #radius of the R_earth_meters

    desired_heading = math.radians(dH + heading) # desired heading in radians
    current_lat = 0
    current_lon = 0
    d = 1000 # distance of projected waypoint in offset_meters

    current_radian_lat = math.radians(current_lat) #current latitude in radians
    current_radian_long = math.radians(current_lon) #current longitude in radians

    waypoint_lat = math.degrees(math.asin(math.sin(current_radian_lat)*math.cos(d/R)) + math.cos(current_radian_lat)*math.sin(d/R)*math.cos(desired_heading))
    waypoint_long = math.degrees(current_radian_long +math.atan2(math.sin(desired_heading)*math.sin(d/R)*math.cos(current_radian_lat), math.cos(d/R)-math.sin(current_radian_lat*math.sin(waypoint_lat))))

    print('TGT WAYPOINT: LAT %f LONG %f' %(waypoint_lat, waypoint_long))


if __name__ == '__main__':
    #Write in regular mode if no argument of b given, if b given, write in binary mode
    if len(argv)<2:
        main()
    elif argv[1]=='b':
        main(argv[1])
    else:
        print('\nINVALID ARGUMENT FOR WRITE MODE.')
        print('Please use:')
        print('     "python DAQcollect.py b" for binary mode or')
        print('     "python DAQcollect.py" for regular write mode.')
