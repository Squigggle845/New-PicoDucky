These are instructions on how to install on RPI pico 2 with no wireless (If wanted for original pico, use dbisu Picoducky)

First, download the circuitpython .UF2 for your board here https://circuitpython.org/downloads. 
Then, plug your pico into your computer, while holding the BOOTSEL button.
A location like RPI2050 should show up.
If you think there is a remaining .UF2 file, drag and drop a .UF2 nuke. There is one in the repo. The RPI2050 should disappear, then reappear.
Drag and drop the circuit python .UF2 into the RPI2050. It should disappear, then reappear.
Drag the contents of the Root folder on this repo, and it will ask to cancel, replace, or keep both (At least on MacOS), and you should replace the older files.
After this is all done, download a payload from somewhere (I would recommend the official Hak5 USB rubber ducky github, but the pico cant hold any files taken, and cant put them in remote server), and name it payload.dd.
If on MacOS, then make sure to save as plain text file, then convert the extension to .dd.
After this is all done, the pico-ducky should work.

To edit payloads, bridge the GPIO pins: 0 and GND, so it shows up as USB drive again.

Alternatively, you can name your payloads: payload1.dd, payload2.dd, payload3.dd, or payload4.dd. You can have a maximum of 4 payloads held, and to switch between, 
payload1 = GPIO4 to GND
payload2 = GPIO5 to GND
payload3 = GPIO10 to GND
payload4 = GPIO11 to GND
