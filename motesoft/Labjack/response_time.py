import lj_fake_pt
from labjack import ljm
import time

state = True
delay = 0.1 #seconds



while True:
    epoch = time.time()
    if state:
        volts = lj_fake_pt.psi_to_volts_5k(650)
    else:
        volts = lj_fake_pt.psi_to_volts_5k(820)

    state = not state
    time.sleep(delay)

    ljm.eWriteName(lj_fake_pt.handle, lj_fake_pt.PIN, volts)
    print("\nSet %s state : %f" % (lj_fake_pt.PIN, volts))
    print(time.time() - epoch)
