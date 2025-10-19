# Lämpötilan mittaus LEDin avulla käyttämällä Pico 2 W:tä

## Aloitus
Tämä projekti käyttää aliprojekteina seuraavia kirjastoja:
- [RPI-PICO-I2C-LCD)](https://github.com/T-622/RPI-PICO-I2C-LCD) (LCD näytöille)  
- [SH1106](https://github.com/robert-hh/SH1106) (SH1106 OLED näytöille)  

Aliprojektit voi alustaa seuraavilla komennoilla:
```
git submodule update --init
git submodule foreach "git submodule update --init"
```

### Komponentit
* Raspberry Pi Pico 2 W
* punainen LED esim häkävaroittimesta
* 15 kgΩ vastus LEDin rajoittamiseen
* 30 µF kondensaattori LEDin tasoittamiseen
* 100nF kondensaattori suodattamaan mittauskohinaa
* johdot ja leipälauta
* (Suositeltava) Cat5 kaapeli LEDille ja referenssi anturille mittausmatkan pidentämiseen
* (valinnainen) DHT22 tai SHT30 lämpötila- ja kosteusanturi
* (valinnainen) I2C LCD näyttö tai SH1106 OLED näyttö

## Konfigurointi
Aseta `main.py` tiedostossa:
  * led_adc: ADC pinni, johon LED on kytketty
  * led_ref_voltage: LEDin referenssijännite (esim. 3.3V)
  * led_ADC_bits: ADC bittisyvyys
  * led_temp_calibration: LEDin lämpötilakalibrointi
  * led_forward_voltage: LEDin jännite kalibrointipisteessä
  * led_coefficent: LEDin lämpötilakerroin  V/°C, esim. -0.0020
  * csv_filename: CSV tiedoston nimi, johon tallennetaan mittaustiedot
  * update_interval: Päivitysväli sekunteina

#### Vapaaehtoiset anturit ja näytöt
Avaa `peripherals.py` ja määritä haluamasi anturi ja näyttö, molemmat ovat vapaaehtoisia.  
Voit käyttää DHT22 tai SHT30 lämpötila- ja kosteusanturia referenssianturina.  
Näytöksi voi valita I2C LCD näytön tai SH1106 OLED näytön.  
Jos et käytä valinnaisia osia aseta `use_dht22`, `use_sht30`, `use_LCD` ja `use_sh1106` arvoksi `False`.

## Kytkentäkaavio
![alt text](image.png)
Wokwi diagrammi: [a relative link](diagram.json)



## Käyttö
Siirrä `pico_i2c_lcd.py`, `lcd_api.py`, `sh1106.py` Pico 2 W:lle  
Siirrä main.py ja peripherals.py Pico 2 W:lle ja suorita main.py