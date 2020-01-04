# Raspberry-Pi-irrigator
A Raspberry Pi controlled irrigation system to water plants based on soil moisture.

This project is ongoing and these are my notes...

## Components

* Pi 3B+. The website business to check the status is why I am not using an Arduino Uno —in my case, a fake Uno by Elegoo— despite having to deal with analog signals. I was going to use the Pi Zero but I want to use the camera (wich is for reg pi) and I don't have a spare USB hub to configure the wifi dongle (as I'd need either an ethernet dongle or keyboard to do so).
* 2x Goso AB11 solenoid pumps (from eBay)[https://www.ebay.co.uk/itm/12V-Dosing-Pump-Peristaltic-Head-For-Aquarium-Lab-Analytical-Water-Arduino-DIY/202050095537] in green and blue. The pumps run at 12V 7.5W. SO 7.5W÷12V=0.625A.
* 2x STM ULN2803A Darlington Drivers (from eBay)[https://www.ebay.co.uk/itm/ULN2803A-Darlington-Driver-TRANSISTOR-ARRAY-8-NPN-x-2-pcs/222622920820]. The darlington driver has inbuilt rectifier diodes. 
* MCP3008 ADC (previous)
* YL69 moisture sensor (previous, from Kuman kit from Amazon). The YL-69 consists of an electrode and an amplifier (LM393) module. The YL69 oxidises over time, further down the line, I might need to switch the electrode to a pair of graphite cores of a pencil as suggested online —or 2mm mechanical pencil refills. LM393 is a comparator not a op-amp like a LM358. For project completion I would need multiple sensors. I'll decide once I try the YL-69.
* GL5528 photoresistors (previous)
* AC/DC adaptor 12V⎓3A with standard ⊖-C*-⊕ coaxial and screw clippy-thinggy adaptor. 

## Code

I am reusing chunks of code from my previous projects:

* [temp monitor site](https://github.com/matteoferla/Temperature-moniting-website-via-Rasberry-Pi)
* [Spirometry via photoresistor](https://github.com/matteoferla/Spirometry_via_photoresistor)



