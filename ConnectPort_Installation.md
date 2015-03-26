# XBee Internet Gateway for Digi ConnectPort X2/3/4/8 #

---

by Rob Faludi (http://faludi.com), Jordan Husney (http://jordan.husney.com), Michael Sutherland (http://digi.com) & Ted Hayes (http://log.liminastudio.com),


## I. CONNECTPORT INSTALLATION ##

To install the XIG, ensure your Digi ConnectPort X gateway is powered
on and configured to access the Internet (by following Digi's
ConnectPort X Getting Started Guide or Rob Faludi's book, [Building Wireless Sensor Networks](http://faludi.com/bwsn/)).  Next you must transfer the XIG application to the gateway and enable it to auto-start.  This may be done through the Device Cloud Management Portal. Here's how:

  1. Open a web-browser and navigate to [Device Cloud Developer Zone](http://www.etherios.com/products/devicecloud/developerzone)
  1. Click on the "Sign Up Now" button, and create a new Device Cloud developer account
  1. Log in to your new Device Cloud account and click on the "Devices" link from the menu on the left side of the page
  1. Ensure your Digi ConnectPort X gateway is powered on and connected to the same network as your computer
  1. On the Device Cloud site, click the "Add Devices" button on the Device toolbar.  Your gateway will be discovered by Device Cloud.  Select your gateway and then click the "OK" button.
  1. Click the refresh icon on the toolbar until your gateway status transitions to "Connected"; double click on the your gateway in the table and its configuration UI will appear
  1. Select "Python" from the configuration interface
  1. Click the upload button from the "Python Files" toolbar, use "Browse" to select "`xig.py`", "`_xig.zip`" and `xig_config.py` from the XIG binary release and click "OK" to upload the files
  1. Under "Auto-start Settings" add "`xig.py`" to one of the "Auto-start Command Line" entries and check the corresponding auto-start "Enable" check boxes.
  1. Click the Save button.  Your new settings will be written to the gateway.
  1. Click on the "Devices" tab, right click on the gateway entry and select "Administration->Reboot..."  Click "Yes" to reboot the device and wait.

## II. USE ##

See the XBee Internet Gateway UserDocumentation for further information.

For more information on Digi's gateways see the following web-page: http://www.digi.com/products/wireless-routers-gateways/