# -*- coding: utf-8 -*-

import can
import os
import sys
from threading import Thread
import time


from kivy.app import App
from kivy.properties import NumericProperty
from kivy.properties import BoundedNumericProperty
from kivy.properties import StringProperty
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter
from kivy.uix.stencilview import StencilView
from kivy.animation import Animation


os.environ['KIVY_GL_BACKEND'] = 'gl'
os.environ['KIVY_WINDOW'] = 'egl_rpi'


message_commands = {
    'GET_DOORS_COMMAND': 0x220D,
    'GET_OIL_TEMPERATURE': 0x202F,
    'GET_OUTDOOR_TEMPERATURE': 0x1014,
    'GET_INDOOR_TEMPERATURE': 0x2613,
    'GET_COOLANT_TEMPERATURE': 0xF405,
    'GET_SPEED': 0xF40D,
    'GET_RPM': 0xF40C,
    'GET_KM_LEFT': 0x2294,
    'GET_FUEL_LEFT': 0x2206,
    'GET_TIME': 0x2216,
    'GET_DISTANCE': 0x2203,
    'GET_FUEL_CONSUMPTION': 0x2299
}

bus = can.interface.Bus(channel='can0', bustype='socketcan')


class PropertyState(object):
    def __init__(self, last, current):
        self.last = last
        self.current = current

    def last_is_not_now(self):
        return self.last is not self.current


class CanListener(can.Listener):
    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.speed_states = PropertyState(None, None)
        self.rpm_states = PropertyState(None, None)
        self.km_left_states = PropertyState(None, None)
        self.coolant_temperature_states = PropertyState(None, None)
        self.fuel_left_states = PropertyState(None, None)
        self.oil_temperature_states = PropertyState(None, None)
        self.time_states = PropertyState(None, None)
        self.outdoor_temperature_states = PropertyState(None, None)
        self.distance_states = PropertyState(None, None)
        self.fuel_consumption_states = PropertyState(None, None)
        self.doors_states = PropertyState(None, None)
        self.car_minimized = True

    def on_message_received(self, message):
        message_command = message.data[3] | message.data[2] << 8

        if message.arbitration_id == 0x77E and message_command == message_commands['GET_SPEED']:
            self.speed_states.current = message.data[4]
            if self.speed_states.last_is_not_now():
                self.dashboard.speedometer.text = str(self.speed_states.current)
                self.speed_states.last = self.speed_states.current

        if message.arbitration_id == 0x77E and message_command == message_commands['GET_RPM']:
            self.rpm_states.current = message.data[5] | message.data[4] << 8
            if self.rpm_states.last_is_not_now():
                self.dashboard.rpm.value = self.rpm_states.current / 4
                self.rpm_states.last = self.rpm_states.current

        if message.arbitration_id == 0x35B:
            self.rpm_states.current = message.data[2] | message.data[1] << 8
            if self.rpm_states.last_is_not_now():
                self.dashboard.rpm.value = self.rpm_states.current / 4
                self.rpm_states.last = self.rpm_states.current

        if message.arbitration_id == 0x77E and message_command == message_commands['GET_KM_LEFT']:
            self.km_left_states.current = message.data[5] | message.data[4] << 8
            if self.km_left_states.last_is_not_now():
                self.dashboard.kmLeftLabel.text = str(self.km_left_states.current)
                self.km_left_states.last = self.km_left_states.current

        if message.arbitration_id == 0x77E and message_command == message_commands['GET_COOLANT_TEMPERATURE']:
            self.coolant_temperature_states.current = message.data[4]
            if self.coolant_temperature_states.last_is_not_now():
                # 0 = 50C
                # 256 = 130C
                # 1C = 3.2
                temperature = self.coolant_temperature_states.current - 81
                if temperature > 50:
                    self.dashboard.coolantBar.height = (temperature-50)*3.2
                    self.coolant_temperature_states.last = self.coolant_temperature_states.current

        if message.arbitration_id == 0x77E and message_command == message_commands['GET_FUEL_LEFT']:
            self.fuel_left_states.current = message.data[4]
            if self.fuel_left_states.last_is_not_now():
                # 55L = 256
                # 0L = 0
                # 1L = 4.65 
                self.dashboard.fuelBar.height = self.fuel_left_states.current * 4.65
                self.fuel_left_states.last = self.fuel_left_states.current

        if message.arbitration_id == 0x77E and message_command == message_commands['GET_OIL_TEMPERATURE']:
            self.oil_temperature_states.current = message.data[4]
            if self.oil_temperature_states.last_is_not_now():
                self.dashboard.oilLabel.text = str(self.oil_temperature_states.current - 58)
                self.oil_temperature_states.last = self.oil_temperature_states.current

        if message.arbitration_id == 0x77E and message_command == message_commands['GET_TIME']:
            self.time_states.current = message.data[5] | message.data[4] << 8
            if self.time_states.last_is_not_now():
                self.dashboard.clock.text = str(message.data[4]) + ":" + str(message.data[5])
                self.time_states.last = self.time_states.current

        if message.arbitration_id == 0x77E and message_command == message_commands['GET_OUTDOOR_TEMPERATURE']:
            self.outdoor_temperature_states.current = float(message.data[4])
            if self.outdoor_temperature_states.last_is_not_now():
                self.dashboard.outDoorTemperatureLabel.text = str((self.outdoor_temperature_states.current - 100) / 2)
                self.outdoor_temperature_states.last = self.outdoor_temperature_states.current

        if message.arbitration_id == 0x77E and message_command == message_commands['GET_DISTANCE']:
            self.distance_states.current = message.data[5] | message.data[4] << 8
            if self.distance_states.last_is_not_now():
                self.dashboard.distanceLabel.text = self.distance_states.current * 10
                self.distance_states.last = self.distance_states.current

        if message.arbitration_id == 0x77E and message_command == message_commands['GET_FUEL_CONSUMPTION']:
            self.fuel_consumption_states.current = float(message.data[5] | message.data[4] << 8)
            if self.fuel_consumption_states.last_is_not_now():
                self.dashboard.fuelConsumptionLabel.text = self.fuel_consumption_states.current / 10
                self.fuel_consumption_states.last = self.fuel_consumption_states.current

        if message.arbitration_id == 0x77E and message_command == message_commands['GET_DOORS_COMMAND']:
            self.doors_states.current = message.data[4]
            if self.doors_states.last_is_not_now():
                self.doors_states.last = self.doors_states.current
                self.dashboard.car.doorsStates = message.data[4]

                # all doors closed -> minimize car
                if self.doors_states.current == 0x55:
                    self.dashboard.minimize_car()
                    self.car_minimized = True
                else:
                    if self.car_minimized:
                        self.dashboard.maximize_car()
                        self.car_minimized = False


class Dashboard(FloatLayout):
    def __init__(self, **kwargs):
        super(Dashboard, self).__init__(**kwargs)

        # Background
        self.background_image = Image(source='bg.png')
        self.add_widget(self.background_image)

        # RPM
        self.rpm = Gauge(file_gauge="gauge512.png", do_rotation=False, do_scale=False, do_translation=False, value=0,
                         size_gauge=512, pos=(72, -16))
        self.add_widget(self.rpm)
        self.rpm.value = 1

        # Bottom Bar
        self.bottom_bar = Image(source='bottomBar.png', pos=(0, -209))
        self.add_widget(self.bottom_bar)

        # Speedometer
        self.speedometer = Label(text='0', font_size=80, font_name='hemi_head_bd_it.ttf', pos=(0, 0))
        self.add_widget(self.speedometer)

        # KM LEFT
        self.km_left_label = Label(text='000', font_name='Avenir.ttc', halign="right", text_size=self.size,
                                   font_size=32, pos=(260, 234))
        self.add_widget(self.km_left_label)

        # CLOCK
        self.clock = Label(text='00:00', font_name='Avenir.ttc', halign="right", text_size=self.size, font_size=32,
                           pos=(-130, -180))
        self.add_widget(self.clock)

        # OUTDOOR TEMPERATURE
        self.outdoor_temperature_label = Label(text='00.0', font_name='Avenir.ttc', halign="right", text_size=self.size,
                                               font_size=32, pos=(95, -180))
        self.add_widget(self.outdoor_temperature_label)
        self.unitC = Label(text='°C', font_name='Avenir.ttc', halign="left", text_size=self.size, font_size=24,
                           pos=(200, -172))
        self.add_widget(self.unitC)

        # OIL TEMPERATURE
        self.oil_label = Label(text='00', font_name='Avenir.ttc', halign="right", text_size=self.size, font_size=27,
                               pos=(-390, -180))
        self.add_widget(self.oil_label)

        # DISTANCE
        self.distance_label = Label(text='000000', font_name='Avenir.ttc', halign="right", text_size=self.size,
                                    font_size=27, pos=(305, -180))
        self.add_widget(self.distance_label)

        # FUEL CONSUMPTION
        self.fuel_cons_label = Label(text='00.0', font_name='Avenir.ttc', halign="right", text_size=self.size,
                                     font_size=32, pos=(-285, 234))
        self.add_widget(self.fuel_cons_label)

        # COOLANT TEMPERATURE
        self.coolant_bar = StencilView(size_hint=(None, None), size=(94, 256), pos=(15, 112))
        self.coolant_image = Image(source='coolantScaleFull.png', size=(94, 256), pos=(15, 112))
        self.coolant_bar.add_widget(self.coolant_image)
        self.add_widget(self.coolant_bar)
        self.coolant_bar.height = 160

        # FUEL LEFT
        self.fuel_bar = StencilView(size_hint=(None, None), size=(94, 256), pos=(686, 112))
        self.fuel_image = Image(source='fuelScaleFull.png', size=(94, 256), pos=(686, 112))
        self.fuel_bar.add_widget(self.fuel_image)
        self.add_widget(self.fuel_bar)
        self.fuel_bar.height = 220

        # CAR DOORS
        self.car = Car(pos=(257, 84))
        self.add_widget(self.car)
        self.minimize_car()

    def minimize_car(self):
        anim = Animation(scale=0.5, opacity=0,  t='linear', duration=0.5)
        anim.start(self.car)

        anim_rpm = Animation(scale=1, opacity=1, t='linear', duration=0.5)
        anim_rpm.start(self.rpm)

    def maximize_car(self):
        anim = Animation(scale=1, opacity=1,  t='linear', duration=0.5)
        anim.start(self.car)

        anim_rpm = Animation(scale=0.5, opacity=0, t='linear', duration=0.5)
        anim_rpm.start(self.rpm)


class Car(Scatter):
    car_image = StringProperty("car362/car.png")

    driver_door_closed_image = StringProperty("car362/driverClosedDoor.png")
    driver_door_opened_image = StringProperty("car362/driverOpenedDoor.png")

    passenger_door_closed_image = StringProperty("car362/passangerClosedDoor.png")
    passenger_door_opened_image = StringProperty("car362/passangerOpenedDoor.png")

    left_door_closed_image = StringProperty("car362/leftClosedDoor.png")
    left_door_opened_image = StringProperty("car362/leftOpenedDoor.png")

    right_door_closed_image = StringProperty("car362/rightClosedDoor.png")
    right_door_opened_image = StringProperty("car362/rightOpenedDoor.png")

    doors_states = NumericProperty(0)

    size = (286, 362)

    def __init__(self, **kwargs):
        super(Car, self).__init__(**kwargs)

        _car = Image(source=self.car_image, size=self.size)

        self.driver_door_opened = Image(source=self.driver_door_opened_image, size=self.size)
        self.passenger_door_opened = Image(source=self.passenger_door_opened_image, size=self.size)
        self.left_door_opened = Image(source=self.left_door_opened_image, size=self.size)
        self.right_door_opened = Image(source=self.right_door_opened_image, size=self.size)

        self.driver_door_closed = Image(source=self.driver_door_closed_image, size=self.size)
        self.passenger_door_closed = Image(source=self.passenger_door_closed_image, size=self.size)
        self.left_door_closed = Image(source=self.left_door_closed_image, size=self.size)
        self.right_door_closed = Image(source=self.right_door_closed_image, size=self.size)

        self.add_widget(_car)
        self.add_widget(self.driver_door_opened)
        self.add_widget(self.passenger_door_opened)
        self.add_widget(self.left_door_opened)
        self.add_widget(self.right_door_opened)

        self.bind(doorsStates=self._update)

    def _update(self):
        driver_door_states = self.doors_states & 1
        passenger_door_states = self.doors_states & 4
        left_door_states = self.doors_states & 16
        right_door_states = self.doors_states & 64
        if driver_door_states != 0:
            try:
                self.remove_widget(self.driver_door_opened)
                self.add_widget(self.driver_door_closed)
            except:
                pass
        else:
            try:
                self.remove_widget(self.driver_door_closed)
                self.add_widget(self.driver_door_opened)
            except:
                pass
        if passenger_door_states != 0:
            try:
                self.remove_widget(self.passenger_door_opened)
                self.add_widget(self.passenger_door_closed)
            except:
                pass
        else:
            try:
                self.remove_widget(self.passenger_door_closed)
                self.add_widget(self.passenger_door_opened)
            except:
                pass
        if left_door_states != 0:
            try:
                self.remove_widget(self.left_door_opened)
                self.add_widget(self.left_door_closed)
            except:
                pass
        else:
            try:
                self.remove_widget(self.left_door_closed)
                self.add_widget(self.left_door_opened)
            except:
                pass
        if right_door_states != 0:
            try:
                self.remove_widget(self.right_door_opened)
                self.add_widget(self.right_door_closed)
            except:
                pass
        else:
            try:
                self.remove_widget(self.right_door_closed)
                self.add_widget(self.right_door_opened)
            except:
                pass


class Gauge(Scatter):
    value = NumericProperty(10)  # BoundedNumericProperty(0, min=0, max=360, errorvalue=0)
    size_gauge = BoundedNumericProperty(512, min=128, max=512, errorvalue=128)
    size_text = NumericProperty(10)
    file_gauge = StringProperty("")

    def __init__(self, **kwargs):
        super(Gauge, self).__init__(**kwargs)

        self._gauge = Scatter(
            size=(self.size_gauge, self.size_gauge),
            do_rotation=False,
            do_scale=False,
            do_translation=False
        )

        _img_gauge = Image(source=self.file_gauge, size=(self.size_gauge, self.size_gauge))

        self._needle = Scatter(
            size=(self.size_gauge, self.size_gauge),
            do_rotation=False,
            do_scale=False,
            do_translation=False
        )

        _img_needle = Image(source="arrow512.png", size=(self.size_gauge, self.size_gauge))

        self._gauge.add_widget(_img_gauge)
        self._needle.add_widget(_img_needle)

        self.add_widget(self._gauge)
        self.add_widget(self._needle)

        self.bind(pos=self._update)
        self.bind(size=self._update)
        self.bind(value=self._turn)

    def _update(self):
        self._gauge.pos = self.pos
        self._needle.pos = (self.x, self.y)
        self._needle.center = self._gauge.center

    def _turn(self):
        self._needle.center_x = self._gauge.center_x
        self._needle.center_y = self._gauge.center_y
        self._needle.rotation = 112-(0.028*self.value)  # 1 rpm = 0.028 gr


class RequestsLoop(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.start()

    canCommands = [
        can.Message(
            arbitration_id=0x714,
            data=[
                0x03,
                0x22,
                message_commands['GET_DOORS_COMMAND'] >> 8,
                message_commands['GET_DOORS_COMMAND'] & 0xff,
                0x55, 0x55, 0x55, 0x55
            ],
            extended_id=False
        ),
        can.Message(
            arbitration_id=0x714,
            data=[
                0x03, 0x22,
                message_commands['GET_SPEED'] >> 8,
                message_commands['GET_SPEED'] & 0xff,
                0x55, 0x55, 0x55, 0x55
            ],
            extended_id=False
        ),
        can.Message(
            arbitration_id=0x714,
            data=[
                0x03,
                0x22,
                message_commands['GET_KM_LEFT'] >> 8,
                message_commands['GET_KM_LEFT'] & 0xff,
                0x55, 0x55, 0x55, 0x55
            ],
            extended_id=False
        ),
        can.Message(
            arbitration_id=0x714,
            data=[
                0x03,
                0x22,
                message_commands['GET_RPM'] >> 8,
                message_commands['GET_RPM'] & 0xff,
                0x55, 0x55, 0x55, 0x55
            ],
            extended_id=False
        ),
        can.Message(
            arbitration_id=0x714,
            data=[
                0x03, 0x22,
                message_commands['GET_OIL_TEMPERATURE'] >> 8,
                message_commands['GET_OIL_TEMPERATURE'] & 0xff,
                0x55, 0x55, 0x55, 0x55
            ],
            extended_id=False
        ),
        can.Message(
            arbitration_id=0x714,
            data=[
                0x03,
                0x22,
                message_commands['GET_FUEL_LEFT'] >> 8,
                message_commands['GET_FUEL_LEFT'] & 0xff,
                0x55, 0x55, 0x55, 0x55
            ],
            extended_id=False
        ),
        can.Message(
            arbitration_id=0x714,
            data=[
                0x03,
                0x22,
                message_commands['GET_OUTDOOR_TEMPERATURE'] >> 8,
                message_commands['GET_OUTDOOR_TEMPERATURE'] & 0xff,
                0x55, 0x55, 0x55, 0x55
            ],
            extended_id=False
        ),
        can.Message(
            arbitration_id=0x746,
            data=[
                0x03,
                0x22,
                message_commands['GET_INDOOR_TEMPERATURE'] >> 8,
                message_commands['GET_INDOOR_TEMPERATURE'] & 0xff,
                0x55, 0x55, 0x55, 0x55
            ],
            extended_id=False
        ),
        can.Message(
            arbitration_id=0x714,
            data=[
                0x03,
                0x22,
                message_commands['GET_COOLANT_TEMPERATURE'] >> 8,
                message_commands['GET_COOLANT_TEMPERATURE'] & 0xff,
                0x55, 0x55, 0x55, 0x55
            ],
            extended_id=False
        ),
        can.Message(
            arbitration_id=0x714,
            data=[
                0x03,
                0x22,
                message_commands['GET_TIME'] >> 8,
                message_commands['GET_TIME'] & 0xff,
                0x55, 0x55, 0x55, 0x55
            ],
            extended_id=False
        ),
        can.Message(
            arbitration_id=0x714,
            data=[
                0x03,
                0x22,
                message_commands['GET_DISTANCE'] >> 8,
                message_commands['GET_DISTANCE'] & 0xff,
                0x55, 0x55, 0x55, 0x55
            ],
            extended_id=False
        ),
        can.Message(
            arbitration_id=0x714,
            data=[
                0x03,
                0x22,
                message_commands['GET_FUEL_CONSUMPTION'] >> 8,
                message_commands['GET_FUEL_CONSUMPTION'] & 0xff,
                0x55, 0x55, 0x55, 0x55
            ],
            extended_id=False
        )
     ]

    def run(self):
        while True:
            for command in self.canCommands:
                bus.send(command)
                time.sleep(0.005)


class BoxApp(App):
    def build(self):
        dashboard = Dashboard()
        listener = CanListener(dashboard)
        can.Notifier(bus, [listener])

        return dashboard


if __name__ == "__main__":
    # Send requests
    RequestsLoop()

    _old_excepthook = sys.excepthook

    def myexcepthook(exctype, value, traceback):
        if exctype == KeyboardInterrupt:
            print "Handler code goes here"
        else:
            _old_excepthook(exctype, value, traceback)
    sys.excepthook = myexcepthook

    # Show dashboard
    BoxApp().run()
