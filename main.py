import gc
import time

from machine import ADC, Pin

from peripherals import init_peripherals

# LED parametrit
led_adc = ADC(Pin(28))  # Pin 28 = ADC2
led_ref_voltage = 3.3  # viitejännite (Picon 3.3V)
led_ADC_bits = 65535  # 16-bittinen muunnos, volteista biteiksi (3.3V = 65535, 0.0V = 0)

# LED kalibroinnit, nämä kaksi muutettava !!
led_temp_calibration = 24.60  # Kalibroinnin lämpötila (yleensä 25°C!)
led_forward_voltage = 1.7221454  # kynnysjännite (ADC2 lukema jännite) kalibroinnin lämpötilassa

# jännitteen muutos/°C, lineaarisena keskiarvona +25°-40°C ~-2mV/°C (millivoltteja)
# -0.002 on hyvä yleiskeskiarvo
led_coefficent = -0.00185618

onboardLed = Pin("LED", Pin.OUT)  # Picon ledi
csv_filename = "mittaukset.csv"

update_interval = 10  # kuinka usein päivitetään näyttöä mittauksessa (10 = 0.1s välein)


def main() -> None:
    ref_sensor = {}  # referenssianturi objekti, täyetään init_peripheralsissa
    screen = {}  # näyttö objekti, täytetään init_peripheralsissa
    init_peripherals(ref_sensor, screen)
    # .CSV luonti
    try:
        with open(csv_filename, "r") as file:
            pass
    except OSError:
        with open(csv_filename, "w") as file:
            if ref_sensor:
                file.write("Aika,LED lämpötila (°C),LED jännite (V), Referenssi (°C)")
            else:
                file.write("Aika,LED lämpötila (°C),LED jännite (V)")

    print("Starting measuring.")
    onboardLed.value(1)
    time.sleep(1)
    onboardLed.value(0)

    while True:
        led_temperature_sum: float = 0
        led_voltage_sum: float = 0
        ref_sum: float = 0

        # Otetaan 3 mitatun lämpötilan keskiarvo (0s, 5s, 10s)
        for i in range(3):
            time.sleep(5)
            # ref lämpötila joka 5s
            if ref_sensor:
                ref_sum += ref_sensor["measure"]()

            # ADC-lukema jännitteeksi:
            voltage_sum = 0
            for j in range(200):  # otetaan 200 mittausta
                time.sleep(0.01)
                raw = led_adc.read_u16()
                voltage_sum += raw  # ynnätään jännitteet(bitteinä)

                # Ruudun päivitys
                if screen and (j % update_interval == 0):
                    # Väliaika tiedot
                    led_voltage = (
                        voltage_sum / (j + 1) / led_ADC_bits
                    ) * led_ref_voltage
                    led_temp = (
                        led_temp_calibration
                        + (led_voltage - led_forward_voltage) / led_coefficent
                    )
                    screen["onUpdate"](
                        screen["screen"], j, i, led_voltage, led_temp, ref_sum / (i + 1)
                    )

            led_raw = voltage_sum / 200  # lasketaan keskiarvo(bitteinä)
            # print(led_raw / led_ADC_bits * 3.3)

            # kynnysjännite = (bitit/65535) * viitejännite:
            led_voltage = (led_raw / led_ADC_bits) * led_ref_voltage
            led_voltage_sum += led_voltage

            # Lasketaan lämpötila suhteessa kalibrointiin
            # lämpötila = kalibroinnin lämpötila + (mitattu kynnysjännite - kalibroinnin jännite) / jännitteen muutos/°C
            led_temp: float = (
                led_temp_calibration + (led_voltage - led_forward_voltage) / led_coefficent
            )
            led_temperature_sum += led_temp
            # Päivitetään näyttö ennen 5s unta
            if screen:
                screen["onUpdate"](
                    screen["screen"], 199, i, led_voltage, led_temp, ref_sum / (i + 1)
                )
                screen["onSleep"](screen["screen"])

        led_temperature_average = led_temperature_sum / 3
        led_voltage_average = led_voltage_sum / 3
        ref_average = ref_sum / 3

        measureTime = time.localtime()
        timestamp = "\n{:02d}.{:02d}.{:4d} {:02d}:{:02d}:{:02d}".format(
            measureTime[2],
            measureTime[1],
            measureTime[0],
            measureTime[3],
            measureTime[4],
            measureTime[5],
        )
        print(timestamp)
        print("LED Voltage: {}".format(led_voltage_average))
        print("LED Temperature: {:.2f}°C".format(led_temperature_average))
        if screen:
            screen["onFinish"](
                screen["screen"],
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
                file.write(
                    f"{timestamp},{led_temperature_average:.2f},{led_voltage_average:.6f}"
                )

        gc.collect()  # Pidetään muisti hallinnassa

    return None


main()
