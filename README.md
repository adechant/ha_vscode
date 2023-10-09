# Home Assistant VSCode Tunnel

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![pre-commit][pre-commit-shield]][pre-commit]
[![Black][black-shield]][black]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Community Forum][forum-shield]][forum]

<img src="https://raw.githubusercontent.com/adechant/ha_vscode/main/custom_components/ha_vscode/images/icon.png" alt="Home Assistant VSCode Tunel logo" title="HA VSCode Tunnel" align="right" height="60" />


## HACS Installation


1. Install the custom component from HACS.
2. Restart Home Assistant.
3. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Home Assistant VSCode Tunnel".
4. Follow the installation instructions. Authenticating with github is required.
5. Restart Home Assistant
6. Turn on the VSCode Tunnel Switch entity to start the tunnel.
7. Go to https://vscode.dev/your_tunnel_name to access your home assistant files (configuartion.yaml, etc)
8. Turn off the VScode Tunnel Switch if you want to stop the tunnel and the associated external connection.

https://vscode.dev can't be opened in an iframe, so this will not work as a sidebar menu item in home assistant - YET! Apparently this feature has been requested and hopefully will be available soon! (see https://github.com/microsoft/vscode/issues/150152)

**This component will set up the following platforms.**

| Platform  | Description                                                                |
| --------- | -------------------------------------------------------------------------- |
| `switch`  | VSCode tunnel in your HA Docker container. Turn it on/off with the switch  |

## Manual Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `ha_vscode`.
4. Download _all_ the files from the `custom_components/ha_vscode/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Home Assistant"
8. Turn on the VSCode Tunnel Switch entity to start the tunnel.
9. Go to https://vscode.dev/your_tunnel_name to access your home assistant files (configuartion.yaml, etc)
10. Turn off the VScode Tunnel Switch if you want to stop the tunnel and the associated external connection.

Using your HA configuration directory (folder) as a starting point you should now also have this:

```text
custom_components/ha_vscode/translations/en.json
custom_components/ha_vscode/__init__.py
custom_components/ha_vscode/config_flow.py
custom_components/ha_vscode/const.py
custom_components/ha_vscode/exceptions.py
custom_components/ha_vscode/manifest.json
custom_components/ha_vscode/switch.py
custom_components/ha_vscode/vscode_device.py
```

## Configuration is done in the UI

If you are having trouble with authentication, increase the timeout in the options.

If you are experiencing a "reload error" after browsing to https://vscode.dev/your_tunnel_name, ensure that you have "turned on" the switch in your home assistant instance. If you are still having difficulties browse to https://vscode.dev and select you tunnel instance from the workspace dropdown menu at the top of the page.

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Credits

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[black]: https://github.com/psf/black
[black-shield]: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
[buymecoffee]: https://www.buymeacoffee.com/adechant
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/adechant/ha_vscode.svg?style=for-the-badge
[commits]: https://github.com/adechant/ha_vscode/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/adechant/ha_vscode.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40adechant-blue.svg?style=for-the-badge
[pre-commit]: https://github.com/pre-commit/pre-commit
[pre-commit-shield]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/adechant/ha_sscode.svg?style=for-the-badge
[releases]: https://github.com/adechant/ha_vscode/releases
[user_profile]: https://github.com/oncleben31
