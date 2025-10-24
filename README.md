# HIL2 Tester for PER

Hardware in the loop firmware, test engine, and test scripts for Purdue Electric Racing ([docs](https://lelserslasers.github.io/PER-HIL2/)).

## Folders

- `./TestBench`: the Teensy code
- `./hil2`: the main HIL "engine"
- `./mk_assert`: a simple and low magic test framework
- `./device_configs`: the device configuration files
- `./tests`: the test scripts and configuration files

## Python libraries

To install the required Python libraries, run:

```bash
python3 -m pip install -r requirements.txt
```

- `pyserial` for serial communication
- `cantools` for CAN DBC encoding/decoding
- `colorama` for cross platform colored terminal output
