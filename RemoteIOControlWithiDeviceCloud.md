# Introduction #

Did you know that you can turn on and off a remote XBee's I/O pins if you have your Digi ConnectPort gateway connected to the free [Device Cloud](http://www.devicecloud.com) service?  Here's how:

  1. Create a [DeveloperZone account](http://www.etherios.com/products/devicecloud/developerzone).
  1. Under Device Cloud's "Devices" section use the plus button to connect your ConnectPort gateway to the Device Cloud platform, note your device's id (e.g. 00409DFF-FF3D7062)
  1. Click on the "Web Services" section
  1. From the examples drop-down select Examples->SCI->Python Callback
  1. Copy and paste the below XML:

```
<sci_request version="1.0">
  <send_message>
    <targets>
      <device id="00000000-00000000-00409DFF-FF43FA07"/>
    </targets>
    <rci_request version="1.1">
      <do_command target="xig">
        <at hw_address="00:13:a2:00:40:48:5a:23!" command="D0" value="1" />       
        <at hw_address="00:13:a2:00:40:48:5a:23!" command="D1" value="4" />
        <at hw_address="00:13:a2:00:40:48:5a:23!" command="D2" value="4" />       
        <at hw_address="00:13:a2:00:40:48:5a:23!" command="D3" value="5" />
        <at hw_address="00:13:a2:00:40:48:5a:23!" command="D4" value="5" apply="True" />
      </do_command>
    </rci_request>
  </send_message>
</sci_request>
```

  * Modify the above XML's "id" parameter to match the device id of your ConnectPort gateway
  * Modify the "hw\_address" parameter(s) to be the extended address of your radio
  * Modify the