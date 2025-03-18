# Calibration tools for Switch Pro Controller
I made those scripts to calibrate my Switch Pro Controller to be usable with both Switch and PC, as I swapped the sticks out with hall effect sticks (Ginful V3, other ones are also out there) and set the magnets to get the best circularity with the magnets, but which also resulted in offset centerpoints. Joycon Toolkit has similar functions, but can only adjust the calibration settings for Switch, not the ones that PC uses. This project runs using simple Python, so everyone (and I) can easily understand and modify it when needed.

**Note**, that these scripts are meant to be modified. This is not a one-click calibration tool. I made these scripts to more easily interface with the controller, so you don't need to write the connection code and similar yourself.  
If you don't understand something about the calibration I recommend reading through the SPI and HID notes I've linked under References.
# References
The code in this project is based on the following projects. If you want to know more indepth how the calibration settings and others are saved to the controller, check out **SPI and HID notes** or **HID API usage** for implementation details.

**SPI and HID notes**: https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering

**Joycon Toolkit**: https://github.com/CTCaer/jc_toolkit

**HID API usage**: https://github.com/shinyquagsire23/HID-Joy-Con-Whispering
# Setup
**FIRST BACKUP YOUR SPI** USING **JoyCon Toolkit**. I am in no way responsible for anything that happens to your controller by using this project.

Clone this repo, pip install the `requirements.txt` and check the python-files.
# Notable Functions
A lot of the functionality was based on the functions from **HID API usage**.
- `controller_actions.py`
	- `tryConnectController()` - Connect to a Pro Controller. Works best with Bluetooth. When using USB, you might need to reconnect the controller multiple times.
	- `disconnectController()` - Disconnect the controller, so it uses Bluetooth again. This function might be a bit buggy. If something happens, just try reconnecting your controller.
	- `setColorType()` - Sets the custom color mode for the controller. When changing the color the grips with **Joycon Toolkit** the switch may only recognise the body color. Use this function to set the corresponding flag, so you can set the grip colors to whatever you want and also have them show on the switch.
- `hid_utils.py`
	-	`send_subcommand()` - Can send a custom command to the controller. The **SPI and HID notes** project has a list of all subcommands and their arguments.
	-	`read_spi_flash()` - Read out a specific address of the SPI. You can only read up to 0x1D bytes.
	-	`write_spi_flash()` - Write to a specific address of the SPI. You can write up to 0x1D bytes.
	-	`setPlayerLED()` - Unrelated to calibration. You can set the pattern of the player LEDs.
- `calibration.py`
	- `readCalibration()` - Read out the calibration for the left or right stick from either the user or the factory section.
	- `writeCalibration()` - Write new calibration data for the left or right stick to either the user or the factory section.
	- `changeCalibrationValue()` - Changes a specific calibration value (Not yet writton to the controller. Use writeCalibration() for that). Every stick has a min, middle and max value for the horizontal and vertical positions and ranges of each stick (Used in the code as `hmin,hmid,hmax,vmin,vmid,vmax`). Note, that the min and max values are not used as the most outer stick positions. Instead they denote the distance from the middle to the outer edge. For example the horizontal left most position would be reached with `hmid - hmin` and the right most position is reached with `hmid + hmax`. This means that if your controller does not reach the end of the circle, you can make the hmin/hmax value smaller, so the stick reaches the highest value sooner.
	- `copyCalibration()` - Copies the calibration data for both the left and right stick from either the user section to the factory section or the other way around.
	- `print_stick_dict()` - Prints out the calibration values obtained by `readCalibration()`.
	- `find_calibration_values()` - Prints the current stick position. Note, that this position is dependand on the current calibration, so if the calibration changes, then the value for the same position will be different. 
# Usage Help
The Pro Controller has two places in SPI where calibration data is saved. There is a section for "user"-calibration data (0x603D) and "factory" calibration data (0x8010). Afaik Switch uses the user section. It can be set up in the settings of a Switch. Windows seems to only use the factory section, so this is the one you need to calibrate yourself to make the controller usable on PC.
1. Check your current calibrations on https://hardwaretester.com/gamepad (Gamepadtester). If they're good, you can quit as you don't need to use those scripts.
2. **Backup** your SPI using **Joycon Toolkit**.
3. Calibrate the controller using your switch, if not already done.
4. Use `readCalibration()` and `writeCalibration()` for left and right stick to copy the user calibration (source), which was setup by the switch, to the factory section. This is usually a good starting point for the following calibration steps. 
	- You can write all values down first, so you can just restore them and start again from the same point if you mess up somewhere.
	- If both sticks were calibrated badly, you can instead use `copyCalibration()` to simply copy the user calibration for both sticks to the factory section.
5. Check your sticks again on Gamepadtester. Your sticks may be off centered, not reach full range and or overshoot the ranges. We will first correct the middle point. Use `find_calibration_values()` to read out the position value of your stick in its resting position and write it down. 
6. Next use Gamepadtester and `find_calibration_values()` read out the position value of where the stick would be centered and write it down. 
7. Use math to determine the differences of those values separately for the horizontal and vertical axis. You can now change the middle values of the stick `hmid`/`vmid` by this difference using `changeCalibrationValue()` to move the center position to where it should be. Then check again in the Gamepadtester. If your sticks are still off centered you can try again.
	-  Sometimes the stick does not move in the Gamepadtester on any or both axis. This happens when the minimum or maximum range calibration settings go out of bounds, i.e. for example `hmid - hmin < 0` or `hmid + hmax > 0xFFF`. You can decrease the `hmin` or `hmax` values to make the stick show properly again in the Gamepadtester.
8. Check your ranges in the Gamepadtester. Adjust the minimum/maximum values `hmin`/`hmax`/`vmin`/`vmax` so that the stick reaches full range, but does not overshoot too much.
9. You can also adjust the deadzones for both sticks (though I'm not sure if they actually change anything on Windows). At least on your Switch this might give you more control on your sticks if the sticks are not too loose. You can use the calibration settings in **Joycon Toolkit** to do that. Afaik the deadzone settings are for both the Switch and Windows, so check the new settings on your Switch too.
	- In my own experience there is a spot on the stick, where the controller shortly shows as if it is centered.  I presume either the deadzone is a bit buggy on Widows or it has something to do with the soldiering of the new stick.
10. Now your stick should mostly work as expected on both PC and Switch. If the deadzone did not work for you, use Steam to launch your applications, as it has it's own deadzone setting in software. 


