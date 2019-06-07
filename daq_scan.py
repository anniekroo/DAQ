from __future__ import print_function
from time import sleep
from os import system
from sys import stdout
import array as arr
import csv
import time

from uldaq import (get_daq_device_inventory, DaqDevice, AInScanFlag, ScanStatus,
                   ScanOption, create_float_buffer, InterfaceType, AiInputMode)


def main():
    daq_device = None
    ai_device = None
    status = ScanStatus.IDLE

    descriptor_index = 0
    range_index = 1
    interface_type = InterfaceType.USB
    low_channel = 0
    high_channel = 0
    samples_per_channel = 1000
    rate = 1000
    scan_options = ScanOption.CONTINUOUS
    flags = AInScanFlag.DEFAULT

    devices = get_daq_device_inventory(interface_type)
    daq_device = DaqDevice(devices[descriptor_index])
    ai_device = daq_device.get_ai_device()
    if ai_device is None:
        raise Exception('Error: The DAQ device does not support analog input')
    daq_device.connect()
    
    ai_info = ai_device.get_info()
    input_mode = AiInputMode.SINGLE_ENDED
    ranges = ai_info.get_ranges(input_mode)
    
    # Allocate a buffer to receive the data.
    data = create_float_buffer(high_channel-low_channel+1, samples_per_channel)
    errors = 0
    csvname = 'daq_'+str(int(rate))+'Hz_'+str(high_channel-low_channel+1)+'Ch.csv'
    with open(csvname, mode = 'a') as daq_file:
        daq_writer = csv.writer(daq_file)
        
        rate = ai_device.a_in_scan(low_channel, high_channel, input_mode, ranges[range_index], samples_per_channel, rate, scan_options, flags, data)
        timeout = time.time()+samples_per_channel/rate
        
        last_index = -1;
        while time.time()<timeout:
            status, transfer_status = ai_device.get_scan_status()
            current_index = transfer_status.current_index;
            if last_index == current_index: continue
            daq_writer.writerow([data[current_index]])
            #print('Current Index:'+str(current_index)+' ,      Current Data:'+str(data[current_index]))
            if last_index!=current_index-1: errors = errors+1; print('Can NOT keep up')
            last_index = current_index
    daq_file.close()
    
    print(errors)

    if daq_device:
        # Stop the acquisition if it is still running.
        if status == ScanStatus.RUNNING:
            ai_device.scan_stop()
        if daq_device.is_connected():
            daq_device.disconnect()
        daq_device.release()

if __name__ == '__main__':
    main()
