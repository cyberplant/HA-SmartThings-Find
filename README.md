# SmartThings Find Integration for Home Assistant

This integration adds support for devices from Samsung SmartThings Find. While intended mainly for Samsung SmartTags, it also works with other devices, such as phones, tablets, watches and earbuds.

Currently the integration creates three entities for each device:
* `device_tracker`: Shows the location of the tag/device.
* `sensor`: Represents the battery level of the tag/device (not supported for earbuds!)
* `button`: Allows you to ring the tag/device.

![screenshot](media/screenshot_1.png)

This integration does **not** allow you to perform actions based on button presses on the SmartTag! There are other ways to do that.

## Repository Lineage

This repository is a fork of a fork. The original repository by [Vedeneb](https://github.com/Vedeneb/HA-SmartThings-Find) was archived, so it was forked by [tomskra](https://github.com/tomskra/HA-SmartThings-Find) to continue maintenance. This current fork by [cyberplant](https://github.com/cyberplant/HA-SmartThings-Find) adds new features and improvements.

## ⚠️ Warning/Disclaimer ⚠️

- **API Limitations**: Created by reverse engineering the SmartThings Find API, this integration might stop working at any time if changes occur on the SmartThings side.
- **Limited Testing**: The integration hasn't been thoroughly tested. If you encounter issues, please report them by creating an issue.
- **Feature Constraints**: The integration can only support features available on the [SmartThings Find website](https://smartthingsfind.samsung.com/). For instance, stopping a SmartTag from ringing is not possible due to API limitations (while other devices do support this; not yet implemented)

## Notes on authentication

This integration supports two authentication methods:

### QR Code Authentication (Recommended)
The integration now supports proper OAuth2 authentication using QR codes, similar to the official SmartThings Find website. This method is more secure and user-friendly:

1. During setup, choose "QR Code Authentication"
2. A QR code will be displayed in Home Assistant
3. Scan the QR code with your Samsung device's camera or SmartThings app
4. Approve the login on your device
5. The integration will automatically complete the authentication

**Note**: The QR code authentication is currently in development and may fall back to manual JSESSIONID entry.

### Manual JSESSIONID Entry (Legacy)
If QR code authentication is not available, you can manually obtain the JSESSIONID:

1. Visit https://smartthingsfind.samsung.com/ and log in with your Samsung account
2. Open Developer Tools in your browser
3. Go to the Application/Storage tab and find cookies for smartthingsfind.samsung.com
4. Copy the JSESSIONID value
5. Enter this value in Home Assistant when prompted

**Session Validity**: The JSESSIONID session may expire over time. If you encounter authentication issues, Home Assistant will prompt you to re-authenticate.

## Notes on connection to the devices
Being able to let a SmartTag ring depends on a phone/tablet nearby which forwards your request via Bluetooth. If your phone is not near your tag, you can't make it ring. The location should still update if any Galaxy device is nearby. 

If ringing your tag does not work, first try to let it ring from the [SmartThings Find website](https://smartthingsfind.samsung.com/). If it does not work from there, it can not work from Home Assistant too! Note that letting it ring with the SmartThings Mobile App is not the same as the website. Just because it does work in the App, does not mean it works on the web. So always use the web version to do your tests.

## Notes on active/passive mode

Starting with version 0.2.0, it is possible to configure whether to use the integration in an active or passive mode. In passive mode the integration only fetches the location from the server which was last reported to STF. In active mode the integration sends an actual "request location update" request. This will make the STF server try to connect to e.g. your phone, get the current location and send it back to the STF server from where the integration can then read it. This has quite a big impact on the devices battery and in some cases might also wake up the screen of the phone or tablet.

By default active mode is enabled for SmartTags but disabled for any other devices. You can change this behaviour on the integrations page by clicking on `Configure`. Here you can also set the update interval, which is set to 120 seconds by default.


## Installation Instructions

### Using HACS

1. Add this repository as a custom repository in HACS. Either by manually adding `https://github.com/cyberplant/HA-SmartThings-Find` with category `integration` or simply click the following button:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cyberplant&repository=HA-SmartThings-Find&category=integration)

2. Search for "SmartThings Find" in HACS and install the integration
3. Restart Home Assistant
4. Proceed to [Setup instructions](#setup-instructions)

### Manual install

1. Download the `custom_components/smartthings_find` directory to your Home Assistant configuration directory
2. Restart Home Assistant
3. Proceed to [Setup instructions](#setup-instructions)

## Setup Instructions

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=smartthings_find)

1. Go to the Integrations page in Home Assistant
2. Search for "SmartThings *Find*" (**do not confuse this with the built-in SmartThings integration!**)
3. Choose your authentication method:
   - **QR Code Authentication (Recommended)**: Follow the on-screen instructions to scan the QR code with your Samsung device
   - **Manual JSESSIONID Entry**: Follow the steps below to obtain your JSESSIONID

### For Manual JSESSIONID Entry:
4. Visit https://smartthingsfind.samsung.com/ and log in with your Samsung account
5. Open Developer Tools in your browser (F12 or Ctrl+Shift+I)
6. Go to the Application/Storage tab and find cookies for smartthingsfind.samsung.com
7. Copy the JSESSIONID value
8. Enter this value in Home Assistant when prompted
9. Wait a few seconds for the integration to be ready

### Re-authentication
If your session expires, Home Assistant will automatically prompt you to re-authenticate. Simply follow the same process you used during initial setup.

## Debugging

To enable debugging, you need to set the log level in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.smartthings_find: debug
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributions

Contributions are welcome! Feel free to open issues or submit pull requests to help improve this integration.

## Support

For support, please create an issue on the GitHub repository.

## Roadmap

- No roadmap, unfortunately, I don't have time for adding features

## Disclaimer

This is a third-party integration and is not affiliated with or endorsed by Samsung or SmartThings.
