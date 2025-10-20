"""Pää moduuli PICO-2W-LED-TEMP projektille."""

import gc
import time

from machine import ADC, Pin

from peripherals import TemperatureSensor, init_peripherals

# LED parametrit
led_adc_pin = ADC(Pin(28))  # Pin 28 = ADC2
led_ref_voltage = 3.3  # viitejännite (Picon 3.3V)
led_adc_bits = 65535  # 16-bittinen muunnos, volteista biteiksi (3.3V = 65535, 0.0V = 0)

# LED kalibroinnit, nämä kaksi muutettava !!
led_calibration_temp = 24.60  # Kalibroinnin lämpötila (yleensä 25°C!)
led_calibration_voltage = 1.7221454  # kynnysjännite (ADC2 lukema jännite) kalibroinnin lämpötilassa

# jännitteen muutos/°C, lineaarisena keskiarvona +25°-40°C ~-2mV/°C (millivoltteja)
# -0.002 on hyvä yleiskeskiarvo
led_coefficent = -0.00185618

onboard_led = Pin("LED", Pin.OUT)  # Picon ledi
csv_filename = "mittaukset.csv"

update_interval = 10  # kuinka monen mittauksen välein näytön päivitys tapahtuu (10 = 0.1s välein)


def create_csv(ref_sensor: TemperatureSensor | None) -> None:
    """Luo .csv tiedosto, jos sitä ei ole jo olemassa."""
    try:
        with open(csv_filename) as file:
            pass
    except OSError:
        with open(csv_filename, "w") as file:
            if ref_sensor:
                file.write("Aika,LED lämpötila (°C),LED jännite (V), Referenssi (°C)")
            else:
                file.write("Aika,LED lämpötila (°C),LED jännite (V)")


def main() -> None:
    """Pääsilmukka, suorittaa mittaukset ja tallentaa ne .csv tiedostoon."""
    ref_sensor, screen = init_peripherals()
    create_csv(ref_sensor)

    print("Starting measuring.")
    onboard_led.value(1)
    time.sleep(1)
    onboard_led.value(0)

    while True:
        led_temperature_sum: float = 0
        led_voltage_sum: float = 0
        ref_sum: float = 0

        # Otetaan 3 mitatun lämpötilan keskiarvo (0s, 5s, 10s)
        for i in range(3):
            time.sleep(5)
            # ref lämpötila joka 5s
            if ref_sensor:
                ref_sum += ref_sensor.measure()

            # ADC-lukema jännitteeksi:
            voltage_sum = 0
            for j in range(200):  # otetaan 200 mittausta
                time.sleep(0.01)
                raw = led_adc_pin.read_u16()
                voltage_sum += raw  # ynnätään jännitteet(bitteinä)

                # Ruudun päivitys
                if screen and (j % update_interval == 0):
                    # Väliaika tiedot
                    led_voltage = (voltage_sum / (j + 1) / led_adc_bits) * led_ref_voltage
                    led_temp = (
                        led_calibration_temp
                        + (led_voltage - led_calibration_voltage) / led_coefficent
                    )
                    screen.update(j, i, led_voltage, led_temp, ref_sum / (i + 1))

            led_raw = voltage_sum / 200  # lasketaan keskiarvo(bitteinä)

            # kynnysjännite = (bitit/65535) * viitejännite:
            led_voltage = (led_raw / led_adc_bits) * led_ref_voltage
            led_voltage_sum += led_voltage

            # Lasketaan lämpötila suhteessa kalibrointiin
            # lämpötila =
            #   kalibroinnin lämpötila +
            #   (mitattu kynnysjännite - kalibroinnin jännite) / jännitteen muutos/°C
            led_temp: float = (
                led_calibration_temp + (led_voltage - led_calibration_voltage) / led_coefficent
            )
            led_temperature_sum += led_temp
            # Päivitetään näyttö ennen 5s unta
            if screen:
                screen.update(200, i, led_voltage, led_temp, ref_sum / (i + 1))
                screen.sleep()

        led_temperature_average = led_temperature_sum / 3
        led_voltage_average = led_voltage_sum / 3
        ref_average = ref_sum / 3

        measure_time = time.localtime()
        timestamp = (
            f"\n{measure_time[2]:02d}.{measure_time[1]:02d}."
            f"{measure_time[0]:4d} {measure_time[3]:02d}:"
            f"{measure_time[4]:02d}:{measure_time[5]:02d}"
        )
        print(timestamp)
        print(f"LED Voltage: {led_voltage_average}")
        print(f"LED Temperature: {led_temperature_average:.2f}°C")
        if screen:
            screen.finish(
                led_temperature_average,
                led_voltage_average,
                ref_average,
            )

        if ref_average:
            print(f"ref Temperature: {ref_average:.2f}C°C")

        with open(csv_filename, "a") as file:
            if ref_sensor:
                file.write(
                    f"{timestamp},{led_temperature_average:.2f},{led_voltage_average:.6f},{ref_average:.2f}"
                )
            else:
                file.write(f"{timestamp},{led_temperature_average:.2f},{led_voltage_average:.6f}")

        gc.collect()  # Pidetään muisti hallinnassa


main()
