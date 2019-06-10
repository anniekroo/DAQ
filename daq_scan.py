from __future__ import print_function
from time import sleep
from os import system
from sys import stdout
import array as arr
import csv
import time
import multiprocessing as mp

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
    samples_per_channel = 10000
    rate = 10000
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
    csvname = 'daq_'+str(int(rate))+'Hz_'+str(high_channel-low_channel+1)+'Ch.csv'
    data_queue = mp.Queue(maxsize = samples_per_channel)
    
    with open(csvname,mode='a') as daq_file:
        daq_writer = csv.writer(daq_file)
        rate = ai_device.a_in_scan(low_channel, high_channel, input_mode, ranges[range_index], samples_per_channel, rate, scan_options, flags, data)
        i = 0
        while i <len(data):
            if data[i]!=0:
                data_queue.put(data[i])
                i+=1
            if not data_queue.empty():
                daq_writer.writerow([data_queue.get()])
        sleep(0.01)
        while not data_queue.empty():
            daq_writer.writerow([data_queue.get()])
    daq_file.close()
    
    if daq_device:
        # Stop the acquisition if it is still running.
        if status == ScanStatus.RUNNING:
            ai_device.scan_stop()
        if daq_device.is_connected():
            daq_device.disconnect()
        daq_device.release()
        
'''
FUNCTIONS FOR MULTITHREAD PIPELINING PROCESS:
    this shows a failed attempt likely due to core management

def save_csv(csvname,timeout,data_queue):
    with open(csvname, mode = 'a') as daq_file:
        daq_writer = csv.writer(daq_file)
        sleep(1.1)
        while not data_queue.empty():
            if not data_queue.empty():
                daq_writer.writerow([data_queue.get()])
        daq_file.close()

def queue_writer(data,data_queue):
    sleep(1)
    for i in range(len(data)):
        data_queue.put(data[i])
'''
        
if __name__ == '__main__':
    main()
