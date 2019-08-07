# DAQ
Using the MCC DAQ devices to do aid navigation and save the raw data as a .txt file for post processing. This repo was designed to be used on a linux platform as it is based on the uldaq library.

This script has the following dependencies:

## Dependencies
### Default Libraries
These libraries are standard python stdlib libraries. No install should be required.
- future
- time
- subprocess
- os
- sys

### Numpy
```
pip install numpy
```

### uldaq
To install the uldaq python library, one must first install the C++ Library. The following instructions on this process were found here: https://github.com/mccdaq/uldaq/blob/master/README.md

## MCC DAQ Library Install
**Info:** Contains a library to access and control supported Measurement Computing [DAQ devices](https://www.mccdaq.com/PDFs/Manuals/Linux-hw.pdf) over the Linux and macOS platforms. The UL for Linux binary name is libuldaq.

**Author:** Measurement Computing

### About
The **uldaq** package contains programming libraries and components for developing applications using C/C++ on Linux and macOS Operating Systems. An API (Application Programming Interface) for interacting with the library in Python is available as an additional installation. This package was created and is supported by MCC. 

#### Prerequisites:
---------------
Building the **uldaq** package requires C/C++ compilers, make tool, and the development package for libusb. The following describes how these prerequisites can be installed on different Linux distributions and macOS.
  
  - Debian-based Linux distributions such as Ubuntu, Raspbian
  
  ```
     $ sudo apt-get install gcc g++ make
     $ sudo apt-get install libusb-1.0-0-dev
  ```
  - Arch-based Linux distributions such as Manjaro, Antergos
  
  ```
     $ sudo pacman -S gcc make
     $ sudo pacman -S libusb
  ```
  - Red Hat-based Linux distributions such as Fedora, CentOS
  
  ```
     $ sudo yum install gcc gcc-c++ make
     $ sudo yum install libusbx-devel
  ``` 
  - OpenSUSE 
  
  ```
     $ sudo zypper install gcc gcc-c++ make
     $ sudo zypper install libusb-devel
  ```
  - macOS (Version 10.11 or later recommended)
  
  ```
     $ xcode-select --install
     $ ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
     $ brew install libusb
  ```

#### Build Instructions
---------------------

1. Download the latest version of **uldaq**:

```
  Linux
     $ wget https://github.com/mccdaq/uldaq/releases/download/v1.1.1/libuldaq-1.1.1.tar.bz2

  macOS
     $ curl -L -O https://github.com/mccdaq/uldaq/releases/download/v1.1.1/libuldaq-1.1.1.tar.bz2
``` 
2. Extract the tar file:
 
```
  $ tar -xvjf libuldaq-1.1.1.tar.bz2
```
  
3. Run the following commands to build and install the library:

```
  $ cd libuldaq-1.1.1
  $ ./configure && make
  $ sudo make install
```

Once you have successfully built this C library, you will need to download the uldaq python library. This can be done by installing it using pip:
```
$ pip install uldaq
```

More resources about this library can be found here: https://pypi.org/project/uldaq/.
