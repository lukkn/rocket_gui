import networking
from configuration import load_config, get_interface_type_number
from gui_class import Handler
import sensor_logging

from gi.repository import Gtk
import gi
gi.require_version("Gtk", "3.0")

import faulthandler
faulthandler.enable()

if __name__ == '__main__':

    

    actuators, sensors = load_config()
    #networking.send_config_to_mote(sensors)

    #print(actuators[0])

    # Boilerplate GTK code to start the GUI
    builder = Gtk.Builder()
    builder.add_from_file("gui.glade")
    # idk if Gtk has a better way of doing this
    gui_class_handler = Handler(sensors, actuators, builder)
    builder.connect_signals(gui_class_handler)

    window = builder.get_object("main_window")
    window.connect("destroy", Gtk.main_quit)
    window.show_all()

    Gtk.main()