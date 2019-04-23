# -*- coding: utf-8 -*-

import can
import os
import sys
from threading import Thread
import time

os.environ['KIVY_GL_BACKEND'] = 'gl'
os.environ['KIVY_WINDOW'] = 'egl_rpi'

from kivy.app import App
from kivy.properties import NumericProperty
from kivy.properties import BoundedNumericProperty
from kivy.properties import StringProperty
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.stencilview import StencilView
from kivy.animation import Animation

messageCommands = {
    'GET_DOORS_COMMAND': 0x220D,
    'GET_OIL_TEMPERATURE' : 0x202F,
    'GET_OUTDOOR_TEMPERATURE' : 0x1014,
    'GET_INDOOR_TEMPERATURE' : 0x2613,
    'GET_COOLANT_TEMPERATURE' : 0xF405,
    'GET_SPEED' : 0xF40D,
    'GET_RPM' : 0xF40C,
    'GET_KM_LEFT': 0x2294,
    'GET_FUEL_LEFT': 0x2206,
    'GET_TIME': 0x2216,
    'GET_DISTANCE':0x2203,
    'GET_FUEL_CONSUMPTION':0x2299
}

bus = can.interface.Bus(channel='can0', bustype='socketcan')

class PropertyState:
    def __init__(self, last, current):
        self.last = last
        self.current = current

    def lastIsNotNow(self):
        return self.last is not self.current

class CanListener(can.Listener):
    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.speedStates = PropertyState(None,None)
        self.rpmStates = PropertyState(None,None)
        self.kmLeftStates = PropertyState(None,None)
        self.coolantTemperatureStates = PropertyState(None,None)
        self.fuelLeftStates = PropertyState(None,None)
        self.oilTempratureStates = PropertyState(None,None)
        self.timeStates = PropertyState(None,None)
        self.outDoorTemperatureStates = PropertyState(None,None)
        self.distanceStates = PropertyState(None,None)
        self.fuelConsumptionStates = PropertyState(None,None)
        self.doorsStates = PropertyState(None,None)
        self.carMinimized = True

    def on_message_received(self, message):
    	messageCommand = message.data[3] | message.data[2] << 8

        if message.arbitration_id == 0x77E and messageCommand == messageCommands['GET_SPEED']:
            self.speedStates.current = message.data[4]
            if self.speedStates.lastIsNotNow():
                self.dashboard.speedometer.text = str(self.speedStates.current)
                self.speedStates.last = self.speedStates.current

        if message.arbitration_id == 0x77E and messageCommand == messageCommands['GET_RPM']:
            self.rpmStates.current = message.data[5] | message.data[4] << 8
            if self.rpmStates.lastIsNotNow():
                self.dashboard.rpm.value = self.rpmStates.current/4
                self.rpmStates.last = self.rpmStates.current
        if message.arbitration_id == 0x35B:
            self.rpmStates.current = message.data[2] | message.data[1] << 8
            if self.rpmStates.lastIsNotNow():
                self.dashboard.rpm.value = self.rpmStates.current/4
                self.rpmStates.last = self.rpmStates.current

        if message.arbitration_id == 0x77E and messageCommand == messageCommands['GET_KM_LEFT']:
            self.kmLeftStates.current = message.data[5] | message.data[4] << 8
            if self.kmLeftStates.lastIsNotNow():
                self.dashboard.kmLeftLabel.text = str(self.kmLeftStates.current)
                self.kmLeftStates.last = self.kmLeftStates.current

        if message.arbitration_id == 0x77E and messageCommand == messageCommands['GET_COOLANT_TEMPERATURE']:
            self.coolantTemperatureStates.current = message.data[4]
            print("coolant=", self.coolantTemperatureStates.current)
            if self.coolantTemperatureStates.lastIsNotNow():
                # 0 = 50C
                # 256 = 130C
                # 1C = 3.2
                temperature = self.coolantTemperatureStates.current-81
                if (temperature > 50):
                    self.dashboard.coolantBar.height = (temperature-50)*3.2
                    self.coolantTemperatureStates.last = self.coolantTemperatureStates.current

        if message.arbitration_id == 0x77E and messageCommand == messageCommands['GET_FUEL_LEFT']:
            self.fuelLeftStates.current = message.data[4]
            if self.fuelLeftStates.lastIsNotNow():
                # 55L = 256
                # 0L = 0
                # 1L = 4.65 
                self.dashboard.fuelBar.height = self.fuelLeftStates.current*4.65
                self.fuelLeftStates.last = self.fuelLeftStates.current

        if message.arbitration_id == 0x77E and messageCommand == messageCommands['GET_OIL_TEMPERATURE']:
            self.oilTempratureStates.current = message.data[4]
            if self.oilTempratureStates.lastIsNotNow():
                self.dashboard.oilLabel.text = str(self.oilTempratureStates.current-58)
                self.oilTempratureStates.last = self.oilTempratureStates.current

        if message.arbitration_id == 0x77E and messageCommand == messageCommands['GET_TIME']:
            self.timeStates.current = message.data[5] | message.data[4] << 8
            if self.timeStates.lastIsNotNow():
                self.dashboard.clock.text = str(message.data[4]) + ":" + str(message.data[5])
                self.timeStates.last = self.timeStates.current

        if message.arbitration_id == 0x77E and messageCommand == messageCommands['GET_OUTDOOR_TEMPERATURE']:
            self.outDoorTemperatureStates.current = float(message.data[4])
            if self.outDoorTemperatureStates.lastIsNotNow():
                self.dashboard.outDoorTemperatureLabel.text = str((self.outDoorTemperatureStates.current - 100)/2)
                self.outDoorTemperatureStates.last = self.outDoorTemperatureStates.current

        if message.arbitration_id == 0x77E and messageCommand == messageCommands['GET_DISTANCE']:
            self.distanceStates.current = message.data[5] | message.data[4] << 8
            if self.distanceStates.lastIsNotNow():
                self.dashboard.distanceLabel.text = self.distanceStates.current*10
                self.distanceStates.last = self.distanceStates.current

        if message.arbitration_id == 0x77E and messageCommand == messageCommands['GET_FUEL_CONSUMPTION']:
            self.fuelConsumptionStates.current = float(message.data[5] | message.data[4] << 8)
            if self.fuelConsumptionStates.lastIsNotNow():
                self.dashboard.fuelConsumptionLabel.text = self.fuelConsumptionStates.current/10
                self.fuelConsumptionStates.last = self.fuelConsumptionStates.current

        if message.arbitration_id == 0x77E and messageCommand == messageCommands['GET_DOORS_COMMAND']:
            self.doorsStates.current = message.data[4]
            if self.doorsStates.lastIsNotNow():
                self.doorsStates.last = self.doorsStates.current
                self.dashboard.car.doorsStates=message.data[4]

                # all doors closed -> minimize car
                if self.doorsStates.current == 0x55:
                    self.dashboard.minimizeCar()
                    self.carMinimized = True
                else:
                    if self.carMinimized:
                        self.dashboard.maximizeCar()
                        self.carMinimized = False

class Dashboard(FloatLayout):
    def __init__(self,**kwargs):
        super(Dashboard,self).__init__(**kwargs)

        # Background
        self.backgroundImage = Image(source='bg.png')
        self.add_widget(self.backgroundImage)

        # RPM
        self.rpm = Gauge(file_gauge = "gauge512.png", do_rotation=False, do_scale=False, do_translation=False, value=0, size_gauge=512, pos=(72,-16))
        self.add_widget(self.rpm)
        self.rpm.value = 1

        # Bottom Bar
        self.bottomBar = Image(source='bottomBar.png', pos=(0,-209))
        self.add_widget(self.bottomBar)

        # Speedometer
        self.speedometer = Label(text='0', font_size=80, font_name='hemi_head_bd_it.ttf', pos=(0,0))
        self.add_widget(self.speedometer)

        # KM LEFT
        self.kmLeftLabel = Label(text='000', font_name='Avenir.ttc', halign="right", text_size=self.size, font_size=32, pos=(260,234))
        self.add_widget(self.kmLeftLabel)

        # CLOCK
        self.clock = Label(text='00:00', font_name='Avenir.ttc', halign="right", text_size=self.size, font_size=32, pos=(-130,-180))
        self.add_widget(self.clock)

        # OUTDOOR TEMPERATURE
        self.outDoorTemperatureLabel = Label(text='00.0', font_name='Avenir.ttc', halign="right", text_size=self.size, font_size=32, pos=(95,-180))
        self.add_widget(self.outDoorTemperatureLabel)
        self.unitC = Label(text='°C', font_name='Avenir.ttc', halign="left", text_size=self.size, font_size=24, pos=(200,-172))
        self.add_widget(self.unitC)

        # OIL TEMPERATURE
        self.oilLabel = Label(text='00', font_name='Avenir.ttc', halign="right", text_size=self.size, font_size=27, pos=(-390,-180))
        self.add_widget(self.oilLabel)

        # DISTANCE
        self.distanceLabel = Label(text='000000', font_name='Avenir.ttc', halign="right", text_size=self.size, font_size=27, pos=(305,-180))
        self.add_widget(self.distanceLabel)

        # FUEL CONSUMPTION
        self.fuelConsLabel = Label(text='00.0', font_name='Avenir.ttc', halign="right", text_size=self.size, font_size=32, pos=(-285,234))
        self.add_widget(self.fuelConsLabel)

        # COOLANT TEMPERATURE
        self.coolantBar = StencilView(size_hint=(None,None), size=(94,256),pos=(15,112))
        self.coolantImage = Image(source='coolantScaleFull.png', size=(94,256), pos=(15,112))
        self.coolantBar.add_widget(self.coolantImage)
        self.add_widget(self.coolantBar)
        self.coolantBar.height = 160;

        # FUEL LEFT
        self.fuelBar = StencilView(size_hint=(None,None), size=(94,256),pos=(686,112))
        self.fuelImage = Image(source='fuelScaleFull.png', size=(94,256), pos=(686,112))
        self.fuelBar.add_widget(self.fuelImage)
        self.add_widget(self.fuelBar)
        self.fuelBar.height = 220;

        # CAR DOORS
        self.car = Car(pos=(257,84))
        self.add_widget(self.car)
        self.minimizeCar()

    def minimizeCar(self, *args):
        anim = Animation(scale=0.5, opacity = 0,  t='linear', duration=0.5)
        anim.start(self.car)

        animRpm = Animation(scale=1, opacity = 1, t='linear', duration=0.5)
        animRpm.start(self.rpm)

    def maximizeCar(self, *args):
        anim = Animation(scale=1, opacity = 1,  t='linear', duration=0.5)
        anim.start(self.car)

        animRpm = Animation(scale=0.5, opacity = 0, t='linear', duration=0.5)
        animRpm.start(self.rpm)


class Car(Scatter):
    carImage = StringProperty("car362/car.png")

    driverDoorClosedImage = StringProperty("car362/driverClosedDoor.png")
    driverDoorOpenedImage = StringProperty("car362/driverOpenedDoor.png")

    passangerDoorClosedImage = StringProperty("car362/passangerClosedDoor.png")
    passangerDoorOpenedImage = StringProperty("car362/passangerOpenedDoor.png")

    leftDoorClosedImage = StringProperty("car362/leftClosedDoor.png")
    leftDoorOpenedImage = StringProperty("car362/leftOpenedDoor.png")

    rightDoorClosedImage = StringProperty("car362/rightClosedDoor.png")
    rightDoorOpenedImage = StringProperty("car362/rightOpenedDoor.png")

    doorsStates = NumericProperty(0)

    size = (286, 362)

    def __init__(self, **kwargs):
        super(Car, self).__init__(**kwargs)

        _car = Image(source=self.carImage, size=self.size)

        self.driverDoorOpened = Image(source=self.driverDoorOpenedImage, size=self.size)
        self.passangerDoorOpened = Image(source=self.passangerDoorOpenedImage, size=self.size)
        self.leftDoorOpened = Image(source=self.leftDoorOpenedImage, size=self.size)
        self.rightDoorOpened = Image(source=self.rightDoorOpenedImage, size=self.size)

        self.driverDoorClosed = Image(source=self.driverDoorClosedImage, size=self.size)
        self.passangerDoorClosed = Image(source=self.passangerDoorClosedImage, size=self.size)
        self.leftDoorClosed = Image(source=self.leftDoorClosedImage, size=self.size)
        self.rightDoorClosed = Image(source=self.rightDoorClosedImage, size=self.size)

        self.add_widget(_car)
        self.add_widget(self.driverDoorOpened)
        self.add_widget(self.passangerDoorOpened)
        self.add_widget(self.leftDoorOpened)
        self.add_widget(self.rightDoorOpened)

        self.bind(doorsStates=self._update)

    def _update(self, *args):
        driverDoorStates = self.doorsStates&1
        passangerDoorStates = self.doorsStates&4
        leftDoorStates = self.doorsStates&16
        rightDoorStates = self.doorsStates&64
        if driverDoorStates != 0:
            try:
                self.remove_widget(self.driverDoorOpened)
                self.add_widget(self.driverDoorClosed)
            except:
                pass
        else:
            try:
                self.remove_widget(self.driverDoorClosed)
                self.add_widget(self.driverDoorOpened)
            except:
                pass
        if passangerDoorStates != 0:
            try:
                self.remove_widget(self.passangerDoorOpened)
                self.add_widget(self.passangerDoorClosed)
            except:
                pass
        else:
            try:
                self.remove_widget(self.passangerDoorClosed)
                self.add_widget(self.passangerDoorOpened)
            except:
                pass
        if leftDoorStates != 0:
            try:
                self.remove_widget(self.leftDoorOpened)
                self.add_widget(self.leftDoorClosed)
            except:
                pass
        else:
            try:
                self.remove_widget(self.leftDoorClosed)
                self.add_widget(self.leftDoorOpened)
            except:
                pass
        if rightDoorStates != 0:
            try:
                self.remove_widget(self.rightDoorOpened)
                self.add_widget(self.rightDoorClosed)
            except:
                pass
        else:
            try:
                self.remove_widget(self.rightDoorClosed)
                self.add_widget(self.rightDoorOpened)
            except:
                pass

class Gauge(Scatter):
    value = NumericProperty(10) #BoundedNumericProperty(0, min=0, max=360, errorvalue=0)
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

    def _update(self, *args):
        self._gauge.pos = self.pos
        self._needle.pos = (self.x, self.y)
        self._needle.center = self._gauge.center

    def _turn(self, *args):
        self._needle.center_x = self._gauge.center_x
        self._needle.center_y = self._gauge.center_y
        self._needle.rotation = 112-(0.028*self.value) # 1 rpm = 0.028 gr

class requestsLoop(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.start()

    canCommands = [
        can.Message(arbitration_id=0x714, data=[0x03, 0x22, messageCommands['GET_DOORS_COMMAND'] >> 8, messageCommands['GET_DOORS_COMMAND'] & 0xff, 0x55, 0x55, 0x55, 0x55], extended_id=False),
        can.Message(arbitration_id=0x714, data=[0x03, 0x22, messageCommands['GET_SPEED'] >> 8, messageCommands['GET_SPEED'] & 0xff, 0x55, 0x55, 0x55, 0x55], extended_id=False),
        can.Message(arbitration_id=0x714, data=[0x03, 0x22, messageCommands['GET_KM_LEFT'] >> 8, messageCommands['GET_KM_LEFT'] & 0xff, 0x55, 0x55, 0x55, 0x55], extended_id=False),
        can.Message(arbitration_id=0x714, data=[0x03, 0x22, messageCommands['GET_RPM'] >> 8, messageCommands['GET_RPM'] & 0xff, 0x55, 0x55, 0x55, 0x55], extended_id=False),
        can.Message(arbitration_id=0x714, data=[0x03, 0x22, messageCommands['GET_OIL_TEMPERATURE'] >> 8, messageCommands['GET_OIL_TEMPERATURE'] & 0xff, 0x55, 0x55, 0x55, 0x55], extended_id=False),
        can.Message(arbitration_id=0x714, data=[0x03, 0x22, messageCommands['GET_FUEL_LEFT'] >> 8, messageCommands['GET_FUEL_LEFT'] & 0xff, 0x55, 0x55, 0x55, 0x55], extended_id=False),
        can.Message(arbitration_id=0x714, data=[0x03, 0x22, messageCommands['GET_OUTDOOR_TEMPERATURE'] >> 8, messageCommands['GET_OUTDOOR_TEMPERATURE'] & 0xff, 0x55, 0x55, 0x55, 0x55], extended_id=False),
        can.Message(arbitration_id=0x746, data=[0x03, 0x22, messageCommands['GET_INDOOR_TEMPERATURE'] >> 8, messageCommands['GET_INDOOR_TEMPERATURE'] & 0xff, 0x55, 0x55, 0x55, 0x55], extended_id=False),
        can.Message(arbitration_id=0x714, data=[0x03, 0x22, messageCommands['GET_COOLANT_TEMPERATURE'] >> 8, messageCommands['GET_COOLANT_TEMPERATURE'] & 0xff, 0x55, 0x55, 0x55, 0x55], extended_id=False),
        can.Message(arbitration_id=0x714, data=[0x03, 0x22, messageCommands['GET_TIME'] >> 8, messageCommands['GET_TIME'] & 0xff, 0x55, 0x55, 0x55, 0x55], extended_id=False),
        can.Message(arbitration_id=0x714, data=[0x03, 0x22, messageCommands['GET_DISTANCE'] >> 8, messageCommands['GET_DISTANCE'] & 0xff, 0x55, 0x55, 0x55, 0x55], extended_id=False),
        can.Message(arbitration_id=0x714, data=[0x03, 0x22, messageCommands['GET_FUEL_CONSUMPTION'] >> 8, messageCommands['GET_FUEL_CONSUMPTION'] & 0xff, 0x55, 0x55, 0x55, 0x55], extended_id=False)
 ]

    def run(self):
        while True:
            for command in self.canCommands:
                bus.send(command)
                time.sleep(0.005)

class BoxApp(App):
    def build(self):
        dashboard = Dashboard();
        listener = CanListener(dashboard)
        can.Notifier(bus, [listener])

        return dashboard
        
if __name__ == "__main__":
    # Send requests
    requestsLoop()

    _old_excepthook = sys.excepthook
    def myexcepthook(exctype, value, traceback):
        if exctype == KeyboardInterrupt:
            print "Handler code goes here"
        else:
            _old_excepthook(exctype, value, traceback)
    sys.excepthook = myexcepthook

    # Show dashboard
    BoxApp().run()
