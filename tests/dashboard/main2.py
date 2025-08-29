from typing import Optional

import hil2.hil2 as hil2
import hil2.component as hil2_comp
import hil2.can_helper as can_helper
import mk_assert.mk_assert as mka

import time
import logging

# Consts ------------------------------------------------------------------------------#
PEDAL_LOW_V = 0.5 # volts read when pedal is not pressed (in normal orientation)
PEDAL_HIGH_V = 4.5 # volts read when pedal is fully pressed (in normal orientation)
PEDAL_PERCENT_V = (PEDAL_HIGH_V - PEDAL_LOW_V) / 100.0

SLEEP_TIME = 0.03 # seconds, how long to wait before checking a CAN message

MSG_NAME = "raw_throttle_brake" # note: motor "off" => throttle = 0


# Helpers -----------------------------------------------------------------------------#
def power_cycle(h: hil2.Hil2, delay_s: float = 0.5):
    """
    Power cycle the system by turning the power off for delay_s seconds, then back on.
    
    :param pow: Power DO component (e.g. relay)
    :param delay_s: Time in seconds to wait with power off
    """
    pow = h.do("HIL2", "RLY1")
    pow.set(False)
    time.sleep(delay_s)
    pow.set(True)
    time.sleep(delay_s)

def pedal_percent_to_volts_1(percent: float) -> float:
    """
    Normal linear mapping from 0-100% to volts
    
    :param percent: Percent value from 0 to 100
    :return: Corresponding voltage value
    """
    return PEDAL_LOW_V + percent * PEDAL_PERCENT_V

def pedal_percent_to_volts_2(percent: float) -> float:
    """
    Inverted linear mapping from 0-100% to volts
    
    :param percent: Percent value from 0 to 100
    :return: Corresponding voltage value
    """
    return PEDAL_HIGH_V - percent * PEDAL_PERCENT_V

def set_both(pedal1: hil2_comp.AO, pedal2: hil2_comp.AO, percent: float) -> None:
    """
    Set a set of two pedals to the same percent value.

    :param pedal1: First pedal AO component (in normal orientation)
    :param pedal2: Second pedal AO component (in inverted orientation)
    :param percent: Percent value from 0 to 100
    """
    pedal1.set(pedal_percent_to_volts_1(percent))
    pedal2.set(pedal_percent_to_volts_2(percent))

def check_msg(can_bus: hil2_comp.CAN, msg_name: str | int, test_prefix: str) -> Optional[can_helper.CanMessage]:
    msg = can_bus.get_last(msg_name)
    mka.assert_true(msg is not None, f"{test_prefix}: VCAN message received")
    return msg

def check_brakes(msg: Optional[can_helper.CanMessage], exp_percent: float, tol_v: float, test_prefix: str):
    mka.assert_eqf(msg is not None and msg.data["brake"],       exp_percent, tol_v, f"{test_prefix}: brake left {exp_percent}%")
    mka.assert_eqf(msg is not None and msg.data["brake_right"], exp_percent, tol_v, f"{test_prefix}: brake right {exp_percent}%")

def check_throttles_diff(msg: Optional[can_helper.CanMessage], exp_percent1: float, exp_percent2: float, tol_v: float, test_prefix: str):
    mka.assert_eqf(msg is not None and msg.data["throttle"],       exp_percent1, tol_v, f"{test_prefix}: throttle left {exp_percent1}%")
    mka.assert_eqf(msg is not None and msg.data["throttle_right"], exp_percent2, tol_v, f"{test_prefix}: throttle right {exp_percent2}%")

def check_throttles(msg: Optional[can_helper.CanMessage], exp_percent: float, tol_v: float, test_prefix: str):
    check_throttles_diff(msg, exp_percent, exp_percent, tol_v, test_prefix)

def check_uart(uart: hil2_comp.DI, test_prefix: str):
    for _ in range(10):
        if uart.get():
            mka.assert_true(True, f"{test_prefix}: UART activity detected")
            return
        time.sleep(0.01)
    mka.assert_true(False, f"{test_prefix}: UART activity detected")

# EV.4.7.2 ----------------------------------------------------------------------------#
def ev_4_7_2_test(h: hil2.Hil2):
    """
    If brake is activated (5% pressed) and throttle is activated more than 25%, motor
    must shutdown and stay shutdown until throttle is under 5%
    
    - brake low, throttle low, check motor on
    - brake high, throttle low, check motor on
    - brake high, throttle high, check motor off
    - brake low, throttle mid, check motor off (sweep down to 5% on throttle)
    - brake low, throttle low, check motor back on
    """

    brk1 = h.ao("Dashboard", "BRK1_RAW")
    brk2 = h.ao("Dashboard", "BRK2_RAW")
    thrtl1 = h.ao("Dashboard", "THRTL1_RAW")
    thrtl2 = h.ao("Dashboard", "THRTL2_RAW")
    vcan = h.can("HIL2", "VCAN")

    # Setup: set brake and throttle to 0%
    vcan.clear()
    set_both(brk1, brk2, 0)
    set_both(thrtl1, thrtl2, 0)
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Setup")
    check_brakes(msg, 0, 0.1, "Setup")
    check_throttles(msg, 0, 0.1, "Setup")
    time.sleep(0.1)
    
    # Test 1: brake low, throttle low, check motor on
    vcan.clear()
    set_both(brk1, brk2, 5)
    set_both(thrtl1, thrtl2, 5)
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Brakes low, throttle low")
    check_brakes(vcan, 5, 0.1, "Brakes low, throttle low")
    check_throttles(vcan, 5, 0.1, "Brakes low, throttle low")
    time.sleep(0.1)

    # Test 2: brake high, throttle low, check motor on
    vcan.clear()
    set_both(brk1, brk2, 50)
    set_both(thrtl1, thrtl2, 5)
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Brakes high, throttle low")
    check_brakes(msg, 50, 0.1, "Brakes high, throttle low")
    check_throttles(msg, 5, 0.1, "Brakes high, throttle low")
    time.sleep(0.1)

    # Test 3: brake high, throttle high, check motor off
    vcan.clear()
    set_both(brk1, brk2, 50)
    set_both(thrtl1, thrtl2, 50)
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Brakes high, throttle high")
    check_brakes(msg, 50, 0.1, "Brakes high, throttle high")
    check_throttles(msg, 0, 0.1, "Brakes high, throttle high")
    time.sleep(0.1)

    # Test 4: brake low, throttle mid, check motor off (sweep down to 5% on throttle)
    vcan.clear()
    set_both(brk1, brk2, 4)
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Brakes low, throttle mid")
    check_brakes(msg, 4, 0.1, "Brakes low, throttle mid")

    for p in range(50, 4, -1):
        vcan.clear()
        set_both(thrtl1, thrtl2, p)
        time.sleep(SLEEP_TIME)
        msg = check_msg(vcan, MSG_NAME, f"Brakes low, throttle {p}")
        expected_throttle = 0 if p > 5 else p
        check_throttles(msg, expected_throttle, 0.1, f"Brakes low, throttle {p} (expected {expected_throttle}%)")
    
    time.sleep(0.1)

    # Test 5: brake low, throttle mid, check motor back on
    vcan.clear()
    set_both(brk1, brk2, 5)
    set_both(thrtl1, thrtl2, 25)
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Brakes low, throttle mid")
    check_brakes(msg, 5, 0.1, "Brakes low, throttle mid")
    check_throttles(msg, 25, 0.1, "Brakes low, throttle mid")


# T.4.2.5 -----------------------------------------------------------------------------#
def t_4_2_5_test(h: hil2.Hil2):
    """
    - sens1 and sens2 similar, check motor on, sdc not triggered
    - sens1 and sens2 slightly different, check motor on, sdc not triggered
    - sens1 and sens2 10% different, check motor on, sdc not triggered
    - sens1 and sens2 slightly different, check motor on, sdc not triggered
    - sens1 and sens2 10% different, check motor on, sdc not triggered
    - sens1 and sens2 still 10% different (~100 msec later), check motor off, sdc not triggered
    - power cycle, confirm everything resets
    - sens1 and sens2 similar, check motor on, sdc not triggered
    """
    thrtl1 = h.ao("Dashboard", "THRTL1_RAW")
    thrtl2 = h.ao("Dashboard", "THRTL2_RAW")
    vcan = h.can("HIL2", "VCAN")
    sdc = h.di("Dashboard", "SDC")

    # Set 1: sens1 = left, sens2 = right ----------------------------------------------#

    # Similar, check motor on, sdc not triggered
    vcan.clear()
    set_both(thrtl1, thrtl2, 25)
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Set 1 - Similar")
    check_throttles(msg, 25, 0.1, "Set 1 - Similar")
    mka.assert_false(sdc.get(), "Set 1 - Similar: SDC not triggered")
    time.sleep(0.1)

    # Slightly different, check motor on, sdc not triggered
    vcan.clear()
    thrtl1.set(pedal_percent_to_volts_1(20))
    thrtl2.set(pedal_percent_to_volts_2(25))
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Set 1 - Slightly different")
    check_throttles_diff(msg, 20, 25, 0.1, "Set 1 - Slightly different")
    mka.assert_false(sdc.get(), "Set 1 - Slightly different: SDC not triggered")
    time.sleep(0.1)

    # 10% different, check motor on, sdc not triggered
    vcan.clear()
    thrtl1.set(pedal_percent_to_volts_1(20))
    thrtl2.set(pedal_percent_to_volts_2(30))
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Set 1 - 10% different")
    check_throttles_diff(msg, 20, 30, 0.1, "Set 1 - 10% different")
    mka.assert_false(sdc.get(), "Set 1 - 10% different: SDC not triggered")
    time.sleep(0.03)

    # Slightly different, check motor on, sdc not triggered
    vcan.clear()
    thrtl1.set(pedal_percent_to_volts_1(25))
    thrtl2.set(pedal_percent_to_volts_2(30))
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Set 1 - Slightly different")
    check_throttles_diff(msg, 25, 30, 0.1, "Set 1 - Slightly different")
    mka.assert_false(sdc.get(), "Set 1 - Slightly different: SDC not triggered")
    time.sleep(0.1)

    # 10% different, check motor on, sdc not triggered
    vcan.clear()
    thrtl1.set(pedal_percent_to_volts_1(20))
    thrtl2.set(pedal_percent_to_volts_2(30))
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Set 1 - 10% different")
    check_throttles_diff(msg, 20, 30, 0.1, "Set 1 - 10% different")
    mka.assert_false(sdc.get(), "Set 1 - 10% different: SDC not triggered")
    time.sleep(0.03)

    # Still 10% different (~100 msec later), check motor off, sdc not triggered
    vcan.clear()
    time.sleep(0.07)
    msg = check_msg(vcan, MSG_NAME, "Set 1 - Still 10% different (~100 msec later)")
    check_throttles(msg, 0, 0.1, "Set 1 - Still 10% different (~100 msec later)")
    mka.assert_false(sdc.get(), "Set 1 - Still 10% different (~100 msec later): SDC not triggered")
    time.sleep(0.1)

    # Power cycle and confirm everything resets
    power_cycle(h)

    # Similar, check motor on, sdc not triggered
    vcan.clear()
    set_both(thrtl1, thrtl2, 20)
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Set 1 - Similar")
    check_throttles(msg, 20, 0.1, "Set 1 - Similar")
    mka.assert_false(sdc.get(), "Set 1 - Similar: SDC not triggered")
    time.sleep(0.1)

    # Set 2: sens1 = right, sens2 = left ----------------------------------------------#
    
    # Similar, check motor on, sdc not triggered
    vcan.clear()
    set_both(thrtl1, thrtl2, 25)
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Set 2 - Similar")
    check_throttles(msg, 25, 0.1, "Set 2 - Similar")
    mka.assert_false(sdc.get(), "Set 2 - Similar: SDC not triggered")
    time.sleep(0.1)

    # Slightly different, check motor on, sdc not triggered
    vcan.clear()
    thrtl1.set(pedal_percent_to_volts_1(25))
    thrtl2.set(pedal_percent_to_volts_2(20))
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Set 2 - Slightly different")
    check_throttles_diff(msg, 25, 20, 0.1, "Set 2 - Slightly different")
    mka.assert_false(sdc.get(), "Set 2 - Slightly different: SDC not triggered")
    time.sleep(0.1)

    # 10% different, check motor on, sdc not triggered
    vcan.clear()
    thrtl1.set(pedal_percent_to_volts_1(30))
    thrtl2.set(pedal_percent_to_volts_2(20))
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Set 2 - 10% different")
    check_throttles_diff(msg, 30, 20, 0.1, "Set 2 - 10% different")
    mka.assert_false(sdc.get(), "Set 2 - 10% different: SDC not triggered")
    time.sleep(0.03)

    # Slightly different, check motor on, sdc not triggered
    vcan.clear()
    thrtl1.set(pedal_percent_to_volts_1(30))
    thrtl2.set(pedal_percent_to_volts_2(25))
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Set 2 - Slightly different")
    check_throttles_diff(msg, 30, 25, 0.1, "Set 2 - Slightly different")
    mka.assert_false(sdc.get(), "Set 2 - Slightly different: SDC not triggered")
    time.sleep(0.1)

    # 10% different, check motor on, sdc not triggered
    vcan.clear()
    thrtl1.set(pedal_percent_to_volts_1(30))
    thrtl2.set(pedal_percent_to_volts_2(20))
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Set 2 - 10% different")
    check_throttles_diff(msg, 30, 20, 0.1, "Set 2 - 10% different")
    mka.assert_false(sdc.get(), "Set 2 - 10% different: SDC not triggered")
    time.sleep(0.03)

    # Still 10% different (~100 msec later), check motor off, sdc not triggered
    vcan.clear()
    time.sleep(0.07)
    msg = check_msg(vcan, MSG_NAME, "Set 2 - Still 10% different (~100 msec later)")
    check_throttles(msg, 0, 0.1, "Set 2 - Still 10% different (~100 msec later)")
    mka.assert_false(sdc.get(), "Set 2 - Still 10% different (~100 msec later): SDC not triggered")
    time.sleep(0.1)

    # Power cycle and confirm everything resets
    power_cycle(h)

    # Similar, check motor on, sdc not triggered
    vcan.clear()
    set_both(thrtl1, thrtl2, 20)
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Set 2 - Similar")
    check_throttles(msg, 20, 0.1, "Set 2 - Similar")
    mka.assert_false(sdc.get(), "Set 2 - Similar: SDC not triggered")
    time.sleep(0.1)

# T.4.2.10 ----------------------------------------------------------------------------#
def t_4_2_10_test(h: hil2.Hil2):
    """
    - sens1 and sens2 ok, check motor on, sdc not triggered
    - both are out of range high, check motor off, sdc triggered
    """

    thrtl1 = h.ao("Dashboard", "THRTL1_RAW")
    thrtl2 = h.ao("Dashboard", "THRTL2_RAW")
    vcan = h.can("HIL2", "VCAN")
    sdc = h.di("Dashboard", "SDC")

    # Set 1: out of range high --------------------------------------------------------#

    # Both ok, check motor on, sdc not triggered
    vcan.clear()
    set_both(thrtl1, thrtl2, 25)
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Both ok")
    check_throttles(msg, 25, 0.1, "Both ok")
    mka.assert_false(sdc.get(), "Both ok: SDC not triggered")
    time.sleep(0.1)

    # Both out of range high, check motor off, sdc triggered
    vcan.clear()
    thrtl1.set(5.5) # volts
    thrtl2.set(5.5) # volts
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Both out of range high")
    check_throttles(msg, 0, 0.1, "Both out of range high")
    mka.assert_true(sdc.get(), "Both out of range high: SDC triggered")
    time.sleep(0.1)

    # Power cycle and confirm everything resets
    power_cycle(h)

    # Both ok, check motor on, sdc not triggered
    vcan.clear()
    set_both(thrtl1, thrtl2, 20)
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Both ok")
    check_throttles(msg, 20, 0.1, "Both ok")
    mka.assert_false(sdc.get(), "Both ok: SDC not triggered")
    time.sleep(0.1)


    # Set 2: throttle 1 disconnects ---------------------------------------------------#

    # Sens1 disconnected, check motor off, sdc triggered
    vcan.clear()
    thrtl2.set(pedal_percent_to_volts_2(25))
    thrtl1.hiZ()
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Sens1 disconnected")
    check_throttles(msg, 0, 0.1, "Sens1 disconnected")
    mka.assert_true(sdc.get(), "Sens1 disconnected: SDC triggered")
    time.sleep(0.1)

    # Power cycle and confirm everything resets
    power_cycle(h)

    # Sens1 and sens2 ok, check motor on, sdc not triggered
    vcan.clear()
    set_both(thrtl1, thrtl2, 20)
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Sens1 and sens2 ok")
    check_throttles(msg, 20, 0.1, "Sens1 and sens2 ok")
    mka.assert_false(sdc.get(), "Sens1 and sens2 ok: SDC not triggered")
    time.sleep(0.1)

    # Set 3: throttle 2 disconnects ---------------------------------------------------#

    # Sens2 disconnected, check motor off, sdc triggered
    vcan.clear()
    thrtl1.set(pedal_percent_to_volts_1(25))
    thrtl2.hiZ()
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Sens2 disconnected")
    check_throttles(msg, 0, 0.1, "Sens2 disconnected")
    mka.assert_true(sdc.get(), "Sens2 disconnected: SDC triggered")
    time.sleep(0.1)

    # Power cycle and confirm everything resets
    power_cycle(h)

    # Sens1 and sens2 ok, check motor on, sdc not triggered
    vcan.clear()
    set_both(thrtl1, thrtl2, 20)
    time.sleep(SLEEP_TIME)
    msg = check_msg(vcan, MSG_NAME, "Sens1 and sens2 ok")
    check_throttles(msg, 20, 0.1, "Sens1 and sens2 ok")
    mka.assert_false(sdc.get(), "Sens1 and sens2 ok: SDC not triggered")
    time.sleep(0.1)


# Buttons test ------------------------------------------------------------------------#
def buttons_test(h: hil2.Hil2):
    """
    4 buttons, gpio on the UART line
    - Try different combinations of the buttons and check that there is activity on the UART
    """

    up = h.do("Dashboard", "UP")
    down = h.do("Dashboard", "DOWN")
    select = h.do("Dashboard", "SELECT")
    start = h.do("Dashboard", "START")
    uart = h.di("Dashboard", "USART_LCD_TX")

    # Setup: set all buttons to not pressed
    up.set(False)
    down.set(False)
    select.set(False)
    start.set(False)

    # Test 1: press UP, check UART activity
    up.set(True)
    check_uart(uart, "Press UP")
    up.set(False)
    time.sleep(0.1)

    # Test 2: press DOWN, check UART activity
    down.set(True)
    check_uart(uart, "Press DOWN")
    down.set(False)
    time.sleep(0.1)

    # Test 3: press SELECT, check UART activity
    select.set(True)
    check_uart(uart, "Press SELECT")
    select.set(False)
    time.sleep(0.1)

    # Test 4: press START, check UART activity
    start.set(True)
    check_uart(uart, "Press START")
    start.set(False)
    time.sleep(0.1)


# Main --------------------------------------------------------------------------------#
def main():
    logging.basicConfig(level=logging.DEBUG)

    with hil2.Hil2(
        "./tests/dashboard/config.json",
        "./device_configs",
        "./netmap/per24.csv",
        "TODO"
    ) as h:
        mka.set_setup_fn(lambda: power_cycle(h))
        mka.set_teardown_fn(h.close)

        mka.add_test(ev_4_7_2_test, h)
        mka.add_test(t_4_2_5_test, h)
        mka.add_test(t_4_2_10_test, h)
        mka.add_test(buttons_test, h)
        
        mka.run_tests()


if __name__ == "__main__":
    main()