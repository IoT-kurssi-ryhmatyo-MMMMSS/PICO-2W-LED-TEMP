"""Määrittelee käytettävät oheislaitteet ja niiden alustuksen."""

from machine import Pin

from pico_i2c_lcd import I2cLcd

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
    "i2c_address": 0x27,
    "scl_pin": 27,
    "sda_pin": 26,
    "num_lines": 2,
    "num_columns": 16,
}

if REF_TYPE == "DHT22":
    import dht

elif REF_TYPE == "SHT30":
    msg = "SHT30 tuki ei ole vielä valmis."
    raise NotImplementedError(msg)


if SCREEN_TYPE == "SH1106":
    import sh1106

    if sh1106_config["mode"] == 1:
        from machine import SoftI2C
    else:
        from machine import I2C

elif SCREEN_TYPE == "LCD":
    from machine import I2C

    from pico_i2c_lcd import I2cLcd


class TemperatureSensor:
    """Yliluokka lämpötila-antureille."""

    def __init__(self, sensor: object) -> None:
        """Alustaa lämpötila-anturin."""
        self._sensor: object = sensor

    def measure(self) -> float:
        """Palauttaa mitatun lämpötilan celsiusasteina."""
        return 0

    @property
    def sensor(self) -> object:
        """Palauttaa käytettävän anturin."""
        return self._sensor


class DHT22(TemperatureSensor):
    """DHT22 lämpötila-anturi."""

    def __init__(self, sensor: "dht.DHT22") -> None:
        """Alustaa DHT22 anturin."""
        super().__init__(sensor)

    @property
    def sensor(self) -> "dht.DHT22":
        return self._sensor  # pyright: ignore[reportReturnType]

    def measure(self) -> float:
        self.sensor.measure()
        return self.sensor.temperature()


class SHT30(TemperatureSensor):
    """SHT30 lämpötila-anturi."""

    def __init__(self, sensor: object) -> None:
        """Alustaa SHT30 anturin."""
        super().__init__(sensor)

    @property
    def sensor(self) -> object:
        return self._sensor

    def measure(self) -> float:
        ## TODO(make): Etsi SHT30 kirjasto
        information = self.sensor.measure_basic()  # pyright: ignore[reportAttributeAccessIssue]
        return information[0]


class Screen:
    """Yliluokka näytöille."""

    def __init__(self, screen: object, dimensions: tuple[int, int]) -> None:
        """Alustaa näytön."""
        self._screen: object = screen
        self._dimensions: tuple[int, int] = dimensions

    def has_ref(self) -> bool:
        """Palauttaa, onko käytössä referenssianturi."""
        return REF_TYPE in ("DHT22", "SHT30")

    @property
    def screen(self) -> object:
        """Palauttaa käytettävän näytön."""
        return self._screen

    def update(
        self,
        frame: int,
        measurement: int,
        voltage: float,
        led_temp: float,
        ref_temp: float,
    ) -> None:
        """Päivittää näytön sisällön.

        Args:
            frame (int): mones mittaus 200:sta
            measurement (int): mones mittaus 3:sta
            voltage (float): ledin jännitteen keskiarvo
            led_temp (float): ledin lämpötila
            ref_temp (float): referenssianturin lämpötila

        """

    def hello_world(self) -> None:
        """Näyttää aloitustekstin."""

    def sleep(self) -> None:
        """Kutsutaan ennen nukkumaanmenoa."""

    def finish(self, led_avg: float, voltage_average: float, ref_average: float) -> None:
        """Kutsutaan mittauksen lopuksi.

        Args:
            led_avg (float): LED lämpötilan keskiarvo
            voltage_average (float): LED jännitteen keskiarvo
            ref_average (float): referenssianturin lämpötilan keskiarvo

        """


class Oled(Screen):
    """SH1106 OLED näyttö."""

    def __init__(self, screen: "sh1106.SH1106", dimensions: tuple[int, int]) -> None:
        """Alustaa SH1106 näytön."""
        super().__init__(screen, dimensions)

    @property
    def screen(self) -> "sh1106.SH1106":
        return self._screen  # pyright: ignore[reportReturnType]

    def hello_world(self) -> None:
        self.screen.fill(0)
        self.screen.text("Hello World", 0, 0)
        self.screen.show()

    def sleep(self) -> None:
        self.screen.fill_rect(0, 0, 128, 8, 0)
        self.screen.text("Sleeping", 0, 0)
        self.screen.show()

    def finish(self, led_avg: float, voltage_average: float, ref_average: float) -> None:
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

        blink = ((frame-1) // 25) % 2 == 0
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


class LCD(Screen):
    """Geneerinen LCD näyttö."""

    def __init__(self, screen: object, dimensions: tuple[int, int]) -> None:
        """Alustaa LCD näytön."""
        super().__init__(screen, dimensions)

    @property
    def screen(self) -> "I2cLcd":
        return self._screen  # pyright: ignore[reportReturnType]

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

    def finish(self, led_avg: float, voltage_average: float, ref_average: float) -> None:
        if self.has_ref():
            self.screen.putstr(f"LED TEMP: {led_avg:.1f}C\nREF TEMP: {ref_average:.1f}C")
        else:
            self.screen.putstr(f"LED TEMP: {led_avg:.1f}C\nVOLTAGE: {voltage_average:.4f}V")


def init_peripherals() -> tuple[TemperatureSensor | None, Screen | None]:
    """Alustaa oheislaitteet."""
    ref_sensor = None
    screen = None

    ## Testaamatonta koodia, ei löytynyt laitteita
    if SCREEN_TYPE == "LCD":
        i2c = I2C(
            LCD_config["i2c_id"],
            scl=Pin(LCD_config["scl_pin"]),
            sda=Pin(LCD_config["sda_pin"]),
            freq=400000,
        )
        screen = LCD(
            I2cLcd(
                i2c, LCD_config["i2c_address"], LCD_config["num_lines"], LCD_config["num_columns"]
            ),
            (LCD_config["num_lines"], LCD_config["num_columns"]),
        )
        screen.hello_world()
    elif SCREEN_TYPE == "SH1106":
        if sh1106_config["mode"] == 0:
            i2c = I2C(
                sh1106_config["i2c_id"],
                scl=Pin(sh1106_config["scl_pin"]),
                sda=Pin(sh1106_config["sda_pin"]),
                freq=400000,
            )
        else:
            i2c = SoftI2C(Pin(sh1106_config["scl_pin"]), Pin(sh1106_config["sda_pin"]))

        screen = Oled(
            sh1106.SH1106_I2C(
                sh1106_config["num_columns"],
                sh1106_config["num_lines"],
                i2c,
                rotate=sh1106_config["rotate"],
            ),
            (sh1106_config["num_lines"], sh1106_config["num_columns"]),
        )
        screen.hello_world()

    if REF_TYPE == "DHT22":
        ref_sensor = DHT22(dht.DHT22(Pin(dht_config["pin"])))
    elif REF_TYPE == "SHT30":
        # ref_sensor = SHT30(sht3x.SHT3x(**sht30_config))
        pass

    return ref_sensor, screen
