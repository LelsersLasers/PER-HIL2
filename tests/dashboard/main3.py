"""
    We only have 1 DAC rn (because all 8 DACs accidently have the same I2C address)
    So we will use voltage dividers for 3 pedal inputs and use the 1 DAC for the 4th
    pedal input.
"""

from typing import Optional

import hil2.hil2 as hil2
import hil2.component as hil2_comp
import hil2.can_helper as can_helper
import mk_assert.mk_assert as mka

import time
import logging

# MSG_NAME = "raw_throttle_brake"
MSG_NAME = 0x8A00000
BRAKE_PERCENT = 0.0 # precent
BRAKE_TOL = 10
THROTTLE_TOL = 10

# BRAKE1_RAW = 300
# BRAKE2_RAW = 300
# THROTTLE2_RAW = 300
V_TO_ADC = lambda v: (v / 5.0) * 4095
V_TO_ADC_INV = lambda v: 4095 - V_TO_ADC(v)

def check_msg(msg: Optional[can_helper.CanMessage], v: float, test_prefix: str):
    mka.assert_true(msg is not None, f"{test_prefix}: VCAN message received")
    if msg is None:
        return
    
    brake = msg.data["brake"]
    brake_right = msg.data["brake_right"]
    throttle = msg.data["throttle"]
    throttle_right = msg.data["throttle_right"]

    logging.info(f"{test_prefix}: throttle={throttle}, brake={brake}, throttle_right={throttle_right}, brake_right={brake_right}")

    adc_exp = V_TO_ADC_INV(v)
    adc_exp_inv = V_TO_ADC(v)
    mka.assert_eqf(brake, adc_exp, BRAKE_TOL, f"{test_prefix}: brake ({brake}) should be approximately {adc_exp}")
    mka.assert_eqf(brake_right, adc_exp, BRAKE_TOL, f"{test_prefix}: brake_right ({brake_right}) should be approximately {adc_exp}")
    mka.assert_eqf(throttle, adc_exp, THROTTLE_TOL, f"{test_prefix}: throttle ({throttle}) should be approximately {adc_exp}")
    mka.assert_eqf(throttle_right, adc_exp_inv, THROTTLE_TOL, f"{test_prefix}: throttle_right ({throttle_right}) should be approximately {adc_exp_inv}")


def t_4_2_5_test(h: hil2.Hil2):
    """
    - Questionable setup:
        - Brake pedal 1 is 0.5v (0% pressed) (via 5v -> 0.5v voltage divider)
        - Brake pedal 2 is 0.5v (0% pressed) (via 5v -> 0.5v voltage divider)
        - Throttle pedal 1 is varied (DAC/AO)
        - Throttle pedal 2 is 2.5v (50% pressed) (via 5v -> 2.5v voltage divider)
    
    Ideally:
    - sens1 and sens2 similar, check motor on, sdc not triggered
    - sens1 and sens2 slightly different, check motor on, sdc not triggered
    - sens1 and sens2 10% different, check motor on, sdc not triggered
    - sens1 and sens2 slightly different, check motor on, sdc not triggered
    - sens1 and sens2 10% different, check motor on, sdc not triggered
    - sens1 and sens2 still 10% different (~100 msec later), check motor off, sdc not triggered
    - sens1 and sens2 similar, check motor on, sdc not triggered
    Note: Check for motor off: throttle can message is 0

    Right now:
    - Setup everything
    - Just check that the message is correct (throttle 50%, brake 0%)
    """
    
    # brake1 = h.do("HIL2", "DO1")
    # brake2 = h.do("HIL2", "DO5")
    # throttle1 = h.ao("HIL2", "DAC3")
    # throttle2 = h.do("HIL2", "DO9")

    vcan = h.can("HIL2", "VCAN")
    dac = h.ao("HIL2", "DAC1")

    # brake1.set(True)
    # brake2.set(True)
    # throttle1.set(2.5)
    # throttle2.set(True)

    input("Setup (brakes 0%, throttle 50%), press Enter to continue...")

    check_msg(vcan.get_last(MSG_NAME), 2.5, "Initial")

    # vcan.clear()
    # time.sleep(0.02)
    # msg = vcan.get_last(MSG_NAME)
    # check_msg(msg, 50.0, "Initial")

    # all_msgs = vcan.get_all()
    # for msg in all_msgs:
    #     print(f"Received CAN message: ID={msg.signal}, Data={msg.data}")
    # # msg_ids = set([m. for m in all_msgs])
    # # msg_ids = msg_ids - {MSG_NAME}
    # # print(f"Other CAN message IDs received on VCAN: {msg_ids}")

    for i in range(5, 46, 1):
        vcan.clear()
        v = i / 10.0
        dac.set(v)
        time.sleep(0.02)

        msg = vcan.get_last(MSG_NAME)
        check_msg(msg, v, f"Throttle set to {v}V")

        time.sleep(0.2)


# Main --------------------------------------------------------------------------------#
def main():
    logging.basicConfig(level=logging.INFO)

    with hil2.Hil2(
        "./tests/dashboard/config.json",
        "device_configs",
        None,
        "./tests/dashboard/dbc"
    ) as h:
        
        mka.add_test(t_4_2_5_test, h)
        mka.run_tests()


if __name__ == "__main__":
    main()