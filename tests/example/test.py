import hil2


def hil2_init():
	h = hil2.Hil2("config.json", "device_config.json", "netmap.csv", "can.dbc")
	return h


def main(h):
	v_bat = h.ao("Main_Module", "VBatt")
	v_bat.set(3.2)
	val = v_bat.get()

	h.set_ao("Main_Module", "VBatt", 3.2)
	val = h.get_ao("Main_Module", "VBatt")

	h.get_last_can("HIL2", "MCAN", "Signal")
	

	mcan = h.can("HIL2", "MCAN")
	mcan.send("Signal", {})
	mcan.send(23, {})
	sig_dict = mcan.get_last("Signal")
	sig_dict = mcan.get_last(23)
	sig_dicts = mcan.get_all("Signal")
	sig_dicts = mcan.get_all(23)
	sig_dicts = mcan.get_all()
	mcan.clear("Signal")
	mcan.clear(23)
	mcan.clear()

if __name__ == "__main__":
	h = hil2_init()
	main(h)