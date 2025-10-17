import hil2.hil2 as hil2
import mk_assert.mk_assert as mka
import time

import logging

def float_range(start, stop, step):
    while start <= stop:
        yield start
        start += step

# def do_test(h: hil2.Hil2):
#     do_2 = h.do("HIL2Bread", "DO@2")
#     di_28 = h.di("HIL2Bread", "DI@28")
#     ai_14 = h.ai("HIL2Bread", "AI@14")

#     do_2.set(True)
#     val = di_28.get()
#     a = ai_14.get()
#     print(f"DI@28: {val}, AI@14: {a}")
#     mka.assert_true(val, "DI@28 should be True after setting DO@2 to True")
#     mka.assert_eqf(a, 3.3, 0.5, "AI@14 should be approximately 3.3V")

#     do_2.set(False)
#     val = di_28.get()
#     a = ai_14.get()
#     print(f"DI@28: {val}, AI@14: {a}")
#     mka.assert_false(val, "DI@28 should be False after setting DO@2 to False")
#     mka.assert_eqf(a, 0.0, 0.5, "AI@14 should be approximately 0.0V")

#     vcan = h.can("HIL2", "VCAN")
#     vcan.send("BrakeLeft", { "raw_reading": 12 })

def set_all_do_low(h: hil2.Hil2):
    for i in range(0, 10):
        do = h.do("HIL2", f"DO{i+1}")
        print(f"Setting DO{i+1} LOW")
        do.set(False)

def do_di_test(h: hil2.Hil2):
    # do = h.do("HIL2", "DO1")

    # for i in range(1, 11):
    #     do = h.do("HIL2", f"DO{i+1}")
    #     print(f"Setting DO{i+1} LOW")
    #     do.set(False)

    # while True:
    #     for i in range(0, 10):
    #         set_all_do_low(h)
    #         print("All DOs set to LOW")
    #         input("Press Enter to continue...")
    #         do = h.do("HIL2", f"DO{i+1}")
    #         print(f"Setting DO{i+1} HIGH")
    #         do.set(True)
    #         input("Press Enter to continue...")

    # set_all_do_low(h)
    # input("Press Enter to continue...")

    # do = h.do("HIL2", f"DO1")
    # print(f"Setting DO1 HIGH")
    # do.set(True)




    # do = h.do("HIL2", f"DO5")
    # print(f"Setting DO5 HIGH")
    # do.set(True)
    # time.sleep(0.1)
    # input("Press Enter to continue...")

    # print("Setting DO5 LOW")
    # do.set(False)
    # time.sleep(0.1)
    # input("Press Enter to continue...")

    # input("Press Enter to continue...")

    # do = h.do("HIL2", f"DO{4}")
    # print(f"Setting DO4 HIGH")
    # do.set(True)
    # time.sleep(0.1)

    # input("Press Enter to continue...")


    print("Setting DO1 LOW")
    do = h.do("HIL2", f"DO1")
    do.set(False)
    time.sleep(0.1)
    input("Press Enter to continue...")
    state = True
    while True:
        print("")
        print(f"Setting DO1 to {state}")
        do.set(state)
        time.sleep(0.05)

        # for i in range(0, 16):
        #     di = h.di("HIL2", f"DMUX_{i}")
        #     val = di.get()
        #     add = "" if not val else " (HIGH)"
        #     print(f"DI_DMUX_{i}: {val} {add}")
        #     time.sleep(0.03)

        # for i in range(1, 3):
        #     ai = h.ai("HIL2", f"DAI{i}")
        #     val = ai.get()
        #     print(f"AI_DAI{i}: {val} V")
        #     time.sleep(0.03)


        state = not state
        input("Press Enter to toggle DO1...")

def ao_ai_test(h: hil2.Hil2):
    # ao1 = h.ao("HIL2", "DAC1")
    # ao2 = h.ao("HIL2", "DAC2")

    # while True:
    #     for voltage in float_range(0.0, 5.0, 0.2):
    #         print("")
            
    #         print(f"Setting DAC1 to {voltage}V")
    #         ao1.set(voltage)
    #         time.sleep(0.2)


    for i in range(0, 8):
        ao = h.ao("HIL2", f"DAC{i+1}")
        print(f"Setting DAC{i+1} to 0.0V")
        ao.set(0.0)

    input("Press Enter to continue...")

    xs = []
    ys = []

    for v in range(0, 50):
        voltage = v / 10.0
        xs.append(voltage)
        # print(f"Setting all DACs to {voltage}V")
        for i in range(0, 8):
            ao = h.ao("HIL2", f"DAC{i+1}")
            ao.set(voltage)
        time.sleep(0.05)

        ai = h.ai("HIL2", "5vMUX_0")
        val = ai.get()
        ys.append(val)
        # print(f"DAI2 reading: {val}V")
        mka.assert_eqf(val, voltage, 0.05, f"DAI2 should read approximately {voltage}V (got {val}V)")
        
    input("Press Enter to continue...")
    

    ao_ai_test(h)
            



    # dai = h.ai("HIL2", "DAI2")
    # ai = h.ai("HIL2", "5vMUX_0")

    # val = dai.get()
    # print(f"Initial DAI2 reading: {val}V")

    # for voltage in float_range(0.0, 5.0, 0.2):
    #     print("")
        
    #     print(f"Setting DACS to {voltage}V")
    #     ao1.set(voltage)
    #     ao2.set(voltage)
    #     time.sleep(0.02)

    #     val = dai.get()
    #     mka.assert_eqf(val, voltage, 0.02, f"DAI2 should read approximately {voltage}V (got {val}V)")

    #     val = ai.get()
    #     mka.assert_eqf(val, voltage, 0.02, f"5vMUX_0 should read approximately {voltage}V (got {val}V)")

    #     input("Press Enter to continue...")

def can_recv_test(h: hil2.Hil2):
    vcan = h.can("HIL2", "VCAN")
    mcan = h.can("HIL2", "MCAN")

    print("Listening for CAN messages on VCAN and MCAN...")
    while True:
        msg = vcan.get_last()
        if msg is not None:
            print(f"Received CAN message: ID={msg.signal}, Data={msg.data}")
            vcan.clear()
        msg = mcan.get_last()
        if msg is not None:
            print(f"Received CAN message: ID={msg.signal}, Data={msg.data}")
            mcan.clear()
        time.sleep(0.1)

        
def can_send_test(h: hil2.Hil2):
    vcan = h.can("HIL2", "VCAN")

    print("Sending CAN messages on VCAN...")
    val = 0
    while True:
        print(f"Sending CAN message: main_hb_amk, start: {val}")
        vcan.send("main_hb_amk", { "precharge_state": 1, "car_state": val })
        if val == 0:
            val = 1
        else:
            val = 0

        msgs = vcan.get_all()
        msg_ids = list(set([msg.signal for msg in msgs]))
        print(f"\tRECV: {msg_ids}")
        vcan.clear()

        time.sleep(1)


def main():
    logging.basicConfig(level=logging.DEBUG)
    
    with hil2.Hil2(
        "./tests/example/config.json",
        "device_configs",
        None,
        "/home/ronak/coding/PER/firmware/common/daq"
    ) as h:
        # mka.add_test(do_di_test, h)
        # mka.add_test(ao_ai_test, h)
        # mka.add_test(can_recv_test, h)
        mka.add_test(can_send_test, h)

        mka.run_tests()

    # v_bat = h.ao("Main_Module", "VBatt")
    # v_bat.set(3.2)
    # val = v_bat.get()

    # h.set_ao("Main_Module", "VBatt", 3.2)
    # val = h.get_ao("Main_Module", "VBatt")

    # h.get_last_can("HIL2", "MCAN", "Signal")

    # mcan = h.can("HIL2", "MCAN")
    # mcan.send("Signal", {})
    # mcan.send(23, {})
    # sig_dict = mcan.get_last("Signal")
    # sig_dict = mcan.get_last(23)
    # sig_dicts = mcan.get_all("Signal")
    # sig_dicts = mcan.get_all(23)
    # sig_dicts = mcan.get_all()
    # mcan.clear("Signal")
    # mcan.clear(23)
    # mcan.clear()


if __name__ == "__main__":
    main()
