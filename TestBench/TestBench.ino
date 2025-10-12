#include <Arduino.h>
#include <Wire.h>
#include <FlexCAN_T4.h>

#include "Adafruit_MCP4706.h"
#include "SW_MCP4017.h"
//----------------------------------------------------------------------------//


const int TESTER_ID = 1;


// Serial conf ---------------------------------------------------------------//
#define SERIAL_BAUDRATE 115200
#define SERIAL_CON Serial
//----------------------------------------------------------------------------//

// DAC conf ------------------------------------------------------------------//
#define NUM_DACS 8
#define DAC_WIRE Wire2
#define DAC_BASE_ADDR 0x60
//----------------------------------------------------------------------------//

// Digipot conf --------------------------------------------------------------//
#define NUM_DIGIPOTS 2

#define DIGIPOT_0_WIRE Wire1
#define DIGIPOT_1_WIRE Wire

const uint8_t DIGIPOT_MAX_STEPS = 128;
const float DIGIPOT_MAX_OHMS = 10000;
//----------------------------------------------------------------------------//

// CAN conf ------------------------------------------------------------------//
#define CAN_BAUDRATE 500000
#define CAN_RX RX_SIZE_256
#define CAN_TX TX_SIZE_16

#define VCAN_BUS 1
#define MCAN_BUS 2
//----------------------------------------------------------------------------//


// Global peripherals --------------------------------------------------------//
Adafruit_MCP4706 dacs[NUM_DACS];
bool dac_power_down[NUM_DACS];

MCP4017 digipots[NUM_DIGIPOTS] = {
  MCP4017(DIGIPOT_MAX_STEPS, DIGIPOT_MAX_OHMS),
  MCP4017(DIGIPOT_MAX_STEPS, DIGIPOT_MAX_OHMS) 
};

FlexCAN_T4<CAN2, CAN_RX, CAN_TX> vCan; // bus: 1
FlexCAN_T4<CAN3, CAN_RX, CAN_TX> mCan; // bus: 2
CAN_message_t recv_msg = { 0 };
//----------------------------------------------------------------------------//


// Serial commands -----------------------------------------------------------//
enum SerialCommand : uint8_t {
    READ_ID    = 0,  // command                    -> READ_ID, id
    WRITE_GPIO = 1,  // command, pin, value        -> []
    HIZ_GPIO   = 2,  // command, pin               -> []
    READ_GPIO  = 3,  // command, pin               -> READ_GPIO, value
    WRITE_DAC  = 4,  // command, pin/offset, value -> []
    HIZ_DAC    = 5,  // command, pin/offset        -> []
    READ_ADC   = 6,  // command, pin               -> READ_ADC, value high, value low
    WRITE_POT  = 7,  // command, pin/offset, value -> []
    SEND_CAN   = 8,  // command, bus, signal bytes: 3-0, length, data (8 bytes) -> []
    RECV_CAN   = 9,  // <async>                    -> CAN_MESSAGE, bus, signal bytes: 3-0, length, data (length bytes)
    ERROR      = 10, // <async/any>                -> ERROR, command
};

size_t TO_READ[] = { // Parrallel to SerialCommand
    1,  // READ_ID
    3,  // WRITE_GPIO
    2,  // HIZ_GPIO
    2,  // READ_GPIO
    3,  // WRITE_DAC
    2,  // HIZ_DAC
    2,  // READ_ADC
    3,  // WRITE_POT
    15, // SEND_CAN
};

// 13 = max(TO_READ)
uint8_t g_serial_data[13] = { 0 };
size_t g_data_idx = 0;
bool g_data_ready = false;
//----------------------------------------------------------------------------//


// Setup ---------------------------------------------------------------------//
void setup() {
    // Serial setup
    SERIAL_CON.begin(SERIAL_BAUDRATE);

    // DAC setup
    for (int i = 0; i < NUM_DACS; i++) {
        uint8_t addr = DAC_BASE_ADDR + i;
        dacs[i].begin(addr, DAC_WIRE);

        dacs[i].setMode(MCP4706_PWRDN_500K);
        dac_power_down[i] = true; // start with power down
    }
    DAC_WIRE.begin();

    // Digipot setup
    digipots[0].begin(MCP4017ADDRESS, DIGIPOT_0_WIRE);
    DIGIPOT_0_WIRE.begin();

    digipots[1].begin(MCP4017ADDRESS, DIGIPOT_1_WIRE);
    DIGIPOT_1_WIRE.begin();

    // CAN setup
    vCan.begin();
    vCan.setBaudRate(CAN_BAUDRATE);

    mCan.begin();
    mCan.setBaudRate(CAN_BAUDRATE);
}
//----------------------------------------------------------------------------//

// Error handling ------------------------------------------------------------//
void send_error(uint8_t command) {
    SERIAL_CON.write(SerialCommand::ERROR);
    SERIAL_CON.write(command);
}
//----------------------------------------------------------------------------//

// CAN -----------------------------------------------------------------------//
void send_can(uint8_t bus) {
    SERIAL_CON.write(RECV_CAN);                   // cmd
    SERIAL_CON.write(bus);                        // bus 
    SERIAL_CON.write((recv_msg.id >> 24) & 0xFF); // signal byte 3
    SERIAL_CON.write((recv_msg.id >> 16) & 0xFF); // signal byte 2
    SERIAL_CON.write((recv_msg.id >> 8) & 0xFF);  // signal byte 1
    SERIAL_CON.write(recv_msg.id & 0xFF);         // signal byte 0
    SERIAL_CON.write(recv_msg.len);               // length
    SERIAL_CON.write(recv_msg.buf, recv_msg.len); // data
}
//----------------------------------------------------------------------------//


// Loop ----------------------------------------------------------------------//
void loop() {
    if (g_data_ready) {
        g_data_ready = false;
        g_data_idx = 0;

        SerialCommand command = (SerialCommand) g_serial_data[0];

        switch (command) {
        case SerialCommand::READ_ID: {
            SERIAL_CON.write(SerialCommand::READ_ID);
            SERIAL_CON.write(TESTER_ID);
            break;
        }
        case SerialCommand::WRITE_GPIO: {
            uint8_t pin = g_serial_data[1];
            uint8_t value = g_serial_data[2];
            pinMode(pin, OUTPUT);
            digitalWrite(pin, value);
            break;
        }
        case SerialCommand::HIZ_GPIO: {
            uint8_t pin = g_serial_data[1];
            pinMode(pin, INPUT);
            break;
        }
        case SerialCommand::READ_GPIO: {
            uint8_t pin = g_serial_data[1];
            pinMode(pin, INPUT);
            int val = digitalRead(pin);
            SERIAL_CON.write(SerialCommand::READ_GPIO);
            SERIAL_CON.write(val);
            break;
        }
        case SerialCommand::WRITE_DAC: {
            uint8_t offset = g_serial_data[1];
            uint8_t value = g_serial_data[2];
            
            if (offset >= NUM_DACS) {
                send_error(command);
                break;
            }

            if (dac_power_down[offset]) {
                dacs[offset].setMode(MCP4706_AWAKE);
                dac_power_down[offset] = false;
            }
            dacs[offset].setVoltage(value);
            break;
        }
        case SerialCommand::HIZ_DAC: {
            uint8_t offset = g_serial_data[1];
            
            if (offset >= NUM_DACS) {
                send_error(command);
                break;
            }

            dacs[offset].setMode(MCP4706_PWRDN_500K);
            dac_power_down[offset] = true;
            break;
        }
        case SerialCommand::READ_ADC: {
            uint8_t pin = g_serial_data[1];
            int val = analogRead(pin);
            SERIAL_CON.write(SerialCommand::READ_ADC);
            SERIAL_CON.write((val >> 8) & 0xFF); // high
            SERIAL_CON.write(val & 0xFF); // low
            break;
        }
        case SerialCommand::WRITE_POT: {
            uint8_t offset = g_serial_data[1];
            uint8_t value = g_serial_data[2];

            if (offset >= NUM_DIGIPOTS) {
                send_error(command);
                break;
            }

            digipots[offset].setSteps(value);
            break;
        }
        case SerialCommand::SEND_CAN: {
            uint8_t bus = g_serial_data[1];
            uint32_t signal = (static_cast<uint32_t>(g_serial_data[2]) << 24) |
                    (static_cast<uint32_t>(g_serial_data[3]) << 16) |
                    (static_cast<uint32_t>(g_serial_data[4]) << 8)  |
                    static_cast<uint32_t>(g_serial_data[5]);
            uint8_t length = g_serial_data[6];
            CAN_message_t msg = { 0 };
            msg.id = signal;
            msg.len = length;
            memcpy(msg.buf, &g_serial_data[7], length);
            msg.len = length;
            msg.flags.extended = true;

            if (bus == VCAN_BUS) {
                vCan.write(msg);
            } else if (bus == MCAN_BUS) {
                mCan.write(msg);
            } else {
                send_error(command);
                break;
            }
            break;
        }
        default: {
            send_error(command);
            break;
        }
        }
    } else if (SERIAL_CON.available() > 0) {
        g_serial_data[g_data_idx] = SERIAL_CON.read();
        g_data_idx++;

        uint8_t command = g_serial_data[0];
        if (g_data_idx == TO_READ[command]) {
            g_data_ready = true;
        }
    } else if (vCan.read(recv_msg)) {
        send_can(VCAN_BUS);
    } else if (mCan.read(recv_msg)) {
        send_can(MCAN_BUS);
    }
}
//----------------------------------------------------------------------------//