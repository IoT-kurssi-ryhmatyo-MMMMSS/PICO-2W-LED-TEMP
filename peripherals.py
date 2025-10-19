from machine import Pin

# Käytettävät vapaaehtoiset anturit/näytöt, muutettava tarpeen mukaan
SCREEN_TYPE = "SH1106"  # "SH1106" tai "LCD" tai "NONE"
REF_TYPE = "DHT22"  # "DHT22", "SHT30" tai "NONE"

dht_config = {"pin": 17}
sht30_config = {
    "i2c_id": 0,
    "scl_pin": 5,
    "sda_pin": 4,
    "i2c_address": 0x44,
}

sh1106_config = {
    "i2c_id": 1,
    "mode": 0,  # 0 = I2C, 1 = SoftI2C
    "scl_pin": 27,
    "sda_pin": 26,
    "rotate": 180,
    "num_lines": 64,
    "num_columns": 128,
}
LCD_config = {
    "i2c_id": 1,
    "scl_pin": 27,
    "sda_pin": 26,
    "num_lines": 2,
    "num_columns": 16,
}


class TemperatureSensor:
    def __init__(self, sensor: object) -> None:
        self._sensor: object = sensor

    def measure(self) -> float:
        return 0

    @property
    def sensor(self):
        return self._sensor

    def __bool__(self) -> bool:
        return self.sensor is not None


class DHT22(TemperatureSensor):
    def __init__(self, sensor: object) -> None:
        super().__init__(sensor)

    def measure(self) -> float:
        self.sensor.measure()
        return self.sensor.temperature()


class SHT30(TemperatureSensor):
    def __init__(self, sensor: object) -> None:
        super().__init__(sensor)

    def measure(self) -> float:
        information = self.sensor.measure_basic()
        return information[0]


class Screen:
    def __init__(self, screen: object) -> None:
        self._screen: object = screen

    def measure(self) -> float:
        return 0

    def has_ref(self) -> bool:
        return REF_TYPE in ("DHT22", "SHT30")

    @property
    def screen(self):
        return self._screen

    def __bool__(self) -> bool:
        return self.screen is not None

    def update(
        self,
        frame: int,
        measurement: int,
        voltage: float,
        led_temp: float,
        ref_temp: float,
    ) -> None:
        """Päivittää näytön sisällön

        Args:
            frame (int): mones mittaus 200:sta
            measurement (int): mones mittaus 3:sta
            voltage (float): ledin jännitteen keskiarvo
            led_temp (float): ledin lämpötila
            ref_temp (float): referenssianturin lämpötila
        """
        pass

    def hello_world(self) -> None:
        """Näyttää aloitustekstin"""
        pass

    def sleep(self) -> None:
        """Kutsutaan ennen nukkumaanmenoa"""
        pass

    def finish(
        self, led_avg: float, voltage_average: float, ref_average: float
    ) -> None:
        """Kutsutaan mittauksen lopuksi

        Args:
            led_avg (float): LED lämpötilan keskiarvo
            voltage_average (float): LED jännitteen keskiarvo
            ref_average (float): referenssianturin lämpötilan keskiarvo
        """
        pass


class Oled(Screen):
    def __init__(self, screen: object) -> None:
        super().__init__(screen)

    def hello_world(self) -> None:
        self.screen.fill(0)
        self.screen.text("Hello World", 0, 0)
        self.screen.show()

    def sleep(self) -> None:
        self.screen.fill_rect(0, 0, 128, 8, 0)
        self.screen.text("Sleeping", 0, 0)
        self.screen.show()

    def finish(
        self, led_avg: float, voltage_average: float, ref_average: float
    ) -> None:
        self.screen.fill_rect(0, 24, 68, 8, 0)
        self.screen.text(f"LED {led_avg:.1f}C", 0, 24)
        self.screen.show()

    def update(
        self,
        frame: int,
        measurement: int,
        voltage: float,
        led_temp: float,
        ref_temp: float,
    ) -> None:
        self.screen.fill(0)
        self.screen.text(f"Measuring...{measurement + 1}/3", 0, 0)

        # Pää
        self.screen.ellipse(96, 36, 25, 18, 1)

        blink = (frame // 25) % 2 == 0
        if blink:
            self.screen.ellipse(87, 32, 3, 5, 1)
            self.screen.ellipse(105, 32, 3, 5, 1)
        else:
            self.screen.hline(84, 32, 6, 1)
            self.screen.hline(102, 32, 6, 1)

        # Suu
        self.screen.hline(88, 46, 16, 1)

        self.screen.rect(10, 58, 108, 4, 1)
        progress = min(frame / 200, 1.0)
        bar_width = int(progress * 108)
        self.screen.fill_rect(10, 58, bar_width, 4, 1)

        self.screen.text(f"{voltage:.3f}V", 0, 16)
        self.screen.text(f"LED {led_temp:.1f}C", 0, 24)
        if ref_temp:
            self.screen.text(f"DHT {ref_temp:.1f}C", 0, 32)

        self.screen.show()


class LED(Screen):
    def __init__(self, screen: object) -> None:
        super().__init__(screen)

    def update(
        self,
        frame: int,
        measurement: int,
        voltage: float,
        led_temp: float,
        ref_temp: float,
    ) -> None:
        if self.has_ref():
            self.screen.putstr(f"LED TEMP: {led_temp:.1f}C\nREF TEMP: {ref_temp:.1f}C")
        else:
            self.screen.putstr(f"LED TEMP: {led_temp:.1f}C\nVOLTAGE: {voltage:.4f}V")

    def sleep(self) -> None:
        self.screen.putstr("Sleeping...")

    def finish(
        self, led_avg: float, voltage_average: float, ref_average: float
    ) -> None:
        if self.has_ref():
            self.screen.putstr(
                f"LED TEMP: {led_avg:.1f}C\nREF TEMP: {ref_average:.1f}C"
            )
        else:
            self.screen.putstr(
                f"LED TEMP: {led_avg:.1f}C\nVOLTAGE: {voltage_average:.4f}V"
            )


def init_peripherals() -> tuple[TemperatureSensor | None, Screen | None]:
    ref_sensor = None
    screen = None

    ## Testaamatonta koodia, ei löytynyt laitteita
    if SCREEN_TYPE == "LCD":
        from lcd_api import LcdApi
        from machine import I2C
        from pico_i2c_lcd import I2cLcd

        i2c = I2C(
            LCD_config["i2c_id"],
            scl=Pin(LCD_config["scl_pin"]),
            sda=Pin(LCD_config["sda_pin"]),
            freq=400000,
        )

        screen = LED(I2cLcd(i2c, LCD_config["num_lines"], LCD_config["num_columns"]))
        screen.hello_world()
    elif SCREEN_TYPE == "SH1106":
        import sh1106

        if sh1106_config["mode"] == 0:
            from machine import I2C

            i2c = I2C(
                sh1106_config["i2c_id"],
                scl=Pin(sh1106_config["scl_pin"]),
                sda=Pin(sh1106_config["sda_pin"]),
                freq=400000,
            )
        else:
            from machine import SoftI2C

            i2c = SoftI2C(Pin(sh1106_config["scl_pin"]), Pin(sh1106_config["sda_pin"]))

        screen = Oled(
            sh1106.SH1106_I2C(
                sh1106_config["num_columns"],
                sh1106_config["num_lines"],
                i2c,
                rotate=sh1106_config["rotate"],
            )
        )
        screen.hello_world()

    if REF_TYPE == "DHT22":
        import dht

        ref_sensor = DHT22(dht.DHT22(Pin(dht_config["pin"])))
    elif REF_TYPE == "SHT30":
        import sht3x

        ref_sensor = SHT30(sht3x.SHT3x(**sht30_config))

    return ref_sensor, screen
