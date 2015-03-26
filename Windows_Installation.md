# XBee Internet Gateway for Windows #

---

by Rob Faludi (http://faludi.com), Jordan Husney (http://jordan.husney.com), Michael Sutherland (http://digi.com) & Ted Hayes (http://log.liminastudio.com),

## I. WINDOWS INSTALLATION ##

System requirements:
  * Windows 7 (other versions may work as well)
  * Chrome, Firefox, Internet Explorer or similar web browser
Hardware requirements:
  * XBee USB adaptor (XBee Explorer, Parallax, Adafruit, Digi XBee Evaluation board or similar)
  * USB cable
  * 802.15.4 (Series 1) or ZigBee ZB (Series 2) XBee radio
Hardware configuration 802.15.4 (Series 1):
  1. For 802.15.4 XBee radios, pick a PAN ID between 0x0 and 0xFFFE. This will need to be set the same for all radios in your network.
  1. We recommend updating your XBee to the latest firmware in X-CTU
  1. Use X-CTU or a terminal program to configure your 802.15.4 radio with the following settings:
    * ATRE (to factory reset the radio…alternately use the Reset button in X-CTU)
    * ATID 1966 (please replace 1966 with your chosen PAN ID!)
    * ATAP 1 (sets your radio to basic API mode)
    * ATD6 1 (turns on monitoring for RTS)
    * ATBD 6 (sets baud rate to 57,600 which is currently the highest supported baud rate)
    * ATWR (saves these as the startup settings)
Hardware configuration ZB ZigBee (Series 2):
  1. For ZigBee XBee radios, picking a PAN ID is optional, so we'll skip that for now.
  1. You will need to update your radio to use the ZigBee Coordinator in API mode firmware in X-CTU.
  1. Use X-CTU or a terminal program to configure your ZigBee Coordinator radio with the following settings:
    * ATRE (to factory reset the radio…alternately use the Reset button in X-CTU)
    * ATD6 1 (turns on monitoring for RTS)
    * ATBD 6 (sets baud rate to 57,600 which is the highest supported baud rate)
    * ATWR (saves these as the startup settings)
Software Installation:
  1. Download the latest version of the software from https://code.google.com/p/xig/wiki/DownloadFiles?tm=2.
  1. Double-click to open the zip file
  1. Drag the xig\_1\_5\_0 folder to your Desktop or to the Programs directory on your C drive to install it.
  1. Plug your XBee radio into its USB adaptor and then plug that adaptor into one of the USB ports on your computer. Windows 7 should locate and install the driver software automatically. On previous versions of Windows, you may need to load the FTDI drivers (http://www.ftdichip.com/Drivers/VCP.htm)
  1. Open this xig\_1\_5\_0 folder and double-click on xig\_app.exe to start the XIG application:
> ![http://www.faludi.com/xig/images/XIG_Windows_folder.png](http://www.faludi.com/xig/images/XIG_Windows_folder.png)
    * You will see a command-line window open in the background:
> ![http://www.faludi.com/xig/images/XIG_Windows_terminal.png](http://www.faludi.com/xig/images/XIG_Windows_terminal.png)
    * then your default web browser will be launched and directed to http://localhost:8000 to display the online user interface for the XIG (below).
    1. Select the correct COM port for your XBee USB adaptor in the pop-up list
    1. Select the correct baud rate for your XBee, typically 57,600 on Windows. With the correct COM port and baud rate, your XBee Status should change to a green "Joined or Formed Network" indicator.
    1. Enter a friendly name for your XBee Internet Gateway in the Description field.

## II. Device Cloud SETUP ##

  1. [Create a FREE account](http://www.etherios.com/products/devicecloud/developerzone) on Device Cloud.
  1. [Log in](https://login.etherios.com) to your new account.
  1. Select the Devices tab, to see the Devices panel: ![http://faludi.com/xig/images/XIG_iDigi_Manager_Pro_tab.png](http://faludi.com/xig/images/XIG_iDigi_Manager_Pro_tab.png)
  1. Click on Add Devices: ![http://faludi.com/xig/images/XIG_iDigi_Add_Devices_button.png](http://faludi.com/xig/images/XIG_iDigi_Add_Devices_button.png)
  1. Click on the Add Manually button: ![http://faludi.com/xig/images/XIG_iDigi_Add_Manually_button.png](http://faludi.com/xig/images/XIG_iDigi_Add_Manually_button.png)
  1. On the pop-up list, switch from MAC Address to Device ID. Then enter the Device ID that shows in the XIG Admin dashboard: ![http://faludi.com/xig/images/XIG_iDigi_Device_ID_list.png](http://faludi.com/xig/images/XIG_iDigi_Device_ID_list.png)
  1. Click the Add button to add that device to the list, then click the OK button at the bottom of the window: ![http://faludi.com/xig/images/XIG_iDigi_DeviceID_Add_button.png](http://faludi.com/xig/images/XIG_iDigi_DeviceID_Add_button.png) ![http://faludi.com/xig/images/XIG_iDigi_device_added_OK_button.png](http://faludi.com/xig/images/XIG_iDigi_device_added_OK_button.png)
  1. Your device should show up in the list, it might still appear as Disconnected: ![http://faludi.com/xig/images/XIG_iDigi_Devices_list_disconnected.png](http://faludi.com/xig/images/XIG_iDigi_Devices_list_disconnected.png)
  1. Wait a few moments, then click on the circling yellow arrows to Refresh the list: ![http://faludi.com/xig/images/XIG_iDigi_Refresh_button.png](http://faludi.com/xig/images/XIG_iDigi_Refresh_button.png)
  1. You should now see your device listed as Connected: ![http://faludi.com/xig/images/XIG_iDigi_Devices_list_connected.png](http://faludi.com/xig/images/XIG_iDigi_Devices_list_connected.png)
> > (By default you will be connected to the login.etherios.com server. If you would like to use a different server you can edit the address in xig/src/settings.json)
CONGRATULATIONS, you're done! Here's a quick tour of the important Device Cloud features:
  * **Getting Data**: Click on the Data Services tab. This is where data uploaded from your XIG will appear. The data you send will become available in a series of XML-formatted files. See the UserDocumentation under "Sending Sample Data to Device Cloud" for more information.
  * **Sending Data and Commands**: Click on the Web Services Console. This is where you can send test sending ASCII text and AT commands directly from the Internet to your XBees. See the UserDocumentation under "Sending Messages from the Internet to an XBee Using Device Cloud " and "Setting or Getting Remote XBee AT Settings via Device Cloud" for more information.
  * **Follow** the [XIGproject on Twitter](http://twitter.com/xigproject).
  * **Join** the [XBee Internet Gateway discussion group](http://groups.google.com/group/xbee-internet-gateway)

## III. USE ##

See the XBee Internet Gateway UserDocumentation for further information.

![http://www.faludi.com/xig/images/XIG_Windows_admin.png](http://www.faludi.com/xig/images/XIG_Windows_admin.png)