from machine import Pin

# Käytettävät vapaaehtoiset sensorit/näytöt, muutettava tarpeen mukaan
use_sh1106 = True
use_LCD = False
use_dht22 = True
use_sht30 = False

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
ref_sensor = {}  # Asetetaan init_peripheralssissa
screen = {}  # Asetetaan init_peripheralssissa


def init_peripherals(ref_sensor, screen) -> None:
    ## Todo
    if use_LCD:
        from lcd_api import LcdApi
        from machine import I2C
        from pico_i2c_lcd import I2cLcd

        i2c = I2C(
            LCD_config["i2c_id"],
            scl=Pin(LCD_config["scl_pin"]),
            sda=Pin(LCD_config["sda_pin"]),
            freq=400000,
        )

        screen["screen"] = I2cLcd(
            i2c, LCD_config["num_lines"], LCD_config["num_columns"]
        )
        screen["screen"].clear()
        screen["screen"].text("Hello World")

        def update(
            target,
            frame: int,
            measurement: int,
            voltage: float,
            led_temp: float,
            ref_temp: float,
        ) -> None:
            """Päivittää näytön sisällön

            Args:
                target (näyttö): näyttöobjekti
                frame (int): mones mittaus 200:sta
                measurement (int): mones mittaus 3:sta
                voltage (float): ledin jännitteen keskiarvo
                led_temp (float): ledin lämpötila
                ref_temp (float): referenssianturin lämpötila
            """
            if use_dht22 or use_sht30:
                target.putstr(f"LED TEMP: {led_temp:.1f}C\nREF TEMP: {ref_temp:.1f}C")
            else:
                target.putstr(f"LED TEMP: {led_temp:.1f}C\nVOLTAGE: {voltage:.4f}V")

        def sleep(target) -> None:
            """Kutsutaan ennen nukkumaanmenoa"""
            target.putstr("Sleeping...")

        def finish(
            target, led_avg: float, voltage_average: float, ref_average: float
        ) -> None:
            """Kutsutaan mittauksen lopuksi

            Args:
                target (näyttö): näyttöobjekti
                led_avg (float): LED lämpötilan keskiarvo
                voltage_average (float): LED jännitteen keskiarvo
                ref_average (float): referenssianturin lämpötilan keskiarvo
            """
            if use_dht22 or use_sht30:
                target.putstr(f"LED TEMP: {led_avg:.1f}C\nREF TEMP: {ref_average:.1f}C")
            else:
                target.putstr(
                    f"LED TEMP: {led_avg:.1f}C\nVOLTAGE: {voltage_average:.4f}V"
                )

        screen["update"] = update
        screen["sleep"] = sleep

    if use_sh1106:
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

        def sleep(target) -> None:
            """Kutsutaan ennen nukkumaanmenoa"""
            target.fill_rect(0, 0, 128, 8, 0)
            target.text("Sleeping", 0, 0)
            target.show()

        def finish(
            target, led_avg: float, voltage_average: float, ref_average: float
        ) -> None:
            """Kutsutaan mittauksen lopuksi

            Args:
                target (näyttö): näyttöobjekti
                led_avg (float): LED lämpötilan keskiarvo
                voltage_average (float): LED jännitteen keskiarvo
                ref_average (float): referenssianturin lämpötilan keskiarvo
            """
            target.fill_rect(0, 24, 68, 8, 0)
            target.text(f"LED {led_avg:.1f}C", 0, 24)
            target.show()

        def update(target, frame, measurement, voltage, led_temp, ref_temp) -> None:
            """Päivittää näytön sisällön

            Args:
                target (näyttö): näyttöobjekti
                frame (int): mones mittaus 200:sta
                measurement (int): mones mittaus 3:sta
                voltage (float): ledin jännitteen keskiarvo
                led_temp (float): ledin lämpötila
                ref_temp (float): referenssianturin lämpötila
            """
            target.fill(0)
            target.text(f"Measuring...{measurement + 1}/3", 0, 0)

            # Pää
            target.ellipse(96, 36, 25, 18, 1)

            blink = (frame // 25) % 2 == 0
            if blink:
                target.ellipse(87, 32, 3, 5, 1)
                target.ellipse(105, 32, 3, 5, 1)
            else:
                target.hline(84, 32, 6, 1)
                target.hline(102, 32, 6, 1)

            # Suu
            target.hline(88, 46, 16, 1)

            target.rect(10, 58, 108, 4, 1)
            progress = min(frame / 200, 1.0)
            bar_width = int(progress * 108)
            target.fill_rect(10, 58, bar_width, 4, 1)

            target.text(f"{voltage:.3f}V", 0, 16)
            target.text(f"LED {led_temp:.1f}C", 0, 24)
            if ref_temp:
                target.text(f"DHT {ref_temp:.1f}C", 0, 32)

            target.show()

        screen["screen"] = sh1106.SH1106_I2C(
            sh1106_config["num_columns"],
            sh1106_config["num_lines"],
            i2c,
            rotate=sh1106_config["rotate"],
        )
        screen["screen"].fill(0)
        screen["screen"].text("Hello World", 0, 0)
        screen["screen"].show()
        screen["onUpdate"] = update
        screen["onSleep"] = sleep
        screen["onFinish"] = finish

    if use_dht22:
        import dht

        ref_sensor["sensor"] = dht.DHT22(Pin(dht_config["pin"]))

        def measure() -> float:
            ref_sensor["sensor"].measure()
            return ref_sensor["sensor"].temperature()

        ref_sensor["measure"] = measure

    if use_sht30:
        import sht3x

        ref_sensor["sensor"] = sht3x.SHT3x(**sht30_config)

        def measure() -> float:
            information = ref_sensor["sensor"].measure_basic()
            return information[0]

        ref_sensor["measure"] = measure
