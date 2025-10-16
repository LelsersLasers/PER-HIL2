# HIL2 Tester for PER

Rewritting HIL 2 from scratch because I have nothing but time and other things I do not want to do

## Folders

- `./TestBench`: the Teensy code
- `./hil2`: the main HIL "engine"
- `./mk_assert`: a simple and low magic test framework
- `./device_configs`: the device configuration files
- `./tests`: the test scripts and configuration files

## Python libraries

To install the required Python libraries, run:

```bash
pip install -r requirements.txt
```

- `pyserial` for serial communication
- `cantools` for CAN DBC encoding/decoding
- `colorama` for cross platform colored terminal output
