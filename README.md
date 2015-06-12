Inception
=========
Inception is a set of tools for auto configuring android devices. You can do the following:

- [Include any apps to be (pre)installed](https://github.com/tgalal/inception/wiki/configkey:-update.apps)
- [Remove any stock apps](https://github.com/tgalal/inception/wiki/configkey:-update.files)
- [Root the device](https://github.com/tgalal/inception/wiki/Rooting-devices)
- [Install busybox](https://github.com/tgalal/inception/wiki/configkey:-update.busybox)
- [Configure Wifi networks](https://github.com/tgalal/inception/wiki/configkey:-update.network)
- [Generate all device settings](https://github.com/tgalal/inception/wiki/configkey:-update.settings)
- [Patch APKs](https://github.com/tgalal/inception/wiki/configkey:-update.apps)
- Replace Kernel, and/or ramdisk data in both [boot](https://github.com/tgalal/inception/wiki/configkey:-boot) and [recovery](https://github.com/tgalal/inception/wiki/configkey:-recovery) imgs
- [Place your adb keys, configure USB debugging](https://github.com/tgalal/inception/wiki/configkey:-update.adb)

# How it works

- You bootstrap a new device configuration
- Update the bootstrapped config, which is a JSON file, with all the changes you need
- inception will compile your config into an Android OTA update package
- Install the update package to your device in recovery mode
- Or optionally let inception generate a cache partition img for your device, allowing you to deploy your update in bootloader/download mode
- No ROM compilation is involved.

Inception does not create a full system image or compile roms. It bundles only the required changes in an Android update package and generates an update script which applies those changes. This results in update packages that are substantially smaller than when flashing a whole ROM.

---
# DISCLAIMER

- **FLASHING DEVICES VOID THEIR WARRANTY**
- **USE AT YOUR OWN RISK, I'M NOT RESPONSIBLE FOR BRICKING YOUR DEVICE.**

---

# Quick start:

## Install

[See installation](https://github.com/tgalal/inception#installation)

## [Bootstrap](https://github.com/tgalal/inception/wiki/incept-bootstrap)
```bash
incept bootstrap --base inception.device --variant myconfig
```

This will generate a configuration file for your variant

Use the following command to list current available variants

```bash
incept ls -l
```

Outputs:
```
Variants:
=========
inception.android.common    ~/.inception/variants/inception/android/common/common.json
inception.device.myconfig   ~/.inception/variants/inception/device/myconfig/myconfig.json
```

Edit ~/.inception/variants/inception/device/myconfig/myconfig.json

Override device settings, add wifi settings, add some apps, root the device and install busybox

For example:

```json
{
    "__extends__": "inception.device",
    "device": {
        "name": "custom"
    },
    "update": {
        "__make__": true,
        "root_method": "supersu",
        "busybox": {
            "__make__": true
        },
        "network": {
            "aps": [
                {
                    "ssid": "Home network",
                    "security": "WPA-PSK",
                    "key": "CE3000FEED"
                }
            ]
        },
        "apps": {
            "com.whatsapp": {
                "apk": "myapps/whatsapp.apk"
            }
        }
    }
}

```
then:

## [Make](https://github.com/tgalal/inception/wiki/incept-make)

```bash
incept make --variant inception.device.myconfig
```

This will generate:

 > ~/.inception/out/inception/device/myconfig/update.zip

Which is an OTA android update that you can install in [several ways](https://github.com/tgalal/inception/wiki/Prerequisites#for-installing-the-update-package).

**Hint**
You will find the full config that generated the OTA package at:

 > ~/.inception/out/inception/device/myconfig/config.json

Inspect that file to see how a full config looks like, override any properties in your original config, run make again and see your changes easily going through.

# Do more

- [Config file structure](https://github.com/tgalal/inception/wiki/Configuration-files)
- [Support any device](https://github.com/tgalal/inception/wiki/Support-any-device)
- [Create Auto-Root packages](https://github.com/tgalal/inception/wiki/incept-autoroot)
- [Rooting devices](https://github.com/tgalal/inception/wiki/Rooting-devices)
- [Config sources](https://github.com/tgalal/inception/wiki/sources.json)
- [Makers/Submakers](https://github.com/tgalal/inception/wiki/Makers)
- [FAQ](https://github.com/tgalal/inception/wiki/FAQ)

# Installation
## On your system:
### Requirements:

- For installation:
  - python < 3.0
  - python-setuptools
  - swig
  - dulwich
  - argparse
- For [incept learn](https://github.com/tgalal/inception/wiki/incept-learn) and [incept bootstrap --learn-*](https://github.com/tgalal/inception/wiki/incept-bootstrap) (optional):
  - [adb](https://pypi.python.org/pypi/adb) >= 1.1.1 
  - libssl-dev
  - dpkg-dev on debian distros, because: https://github.com/martinpaljak/M2Crypto/issues/62
- For some 32bit binaries that are included in base configs (namely make_ext4s), unless overridden:
  - gcc-multilib
  - lib32z1
- For patching APKs
  - libstdc++6 and/or lib32stdc++6 

### Install

```
git clone https://github.com/tgalal/inception.git
python setup.py install
```
or
```
pip install inception-android
```

## Using docker

Here is also a [docker container](https://registry.hub.docker.com/u/tgalal/inception/) for inception

```
docker pull tgalal/inception

```

# License:

inception is licensed under the GPLv3+: http://www.gnu.org/licenses/gpl-3.0.html.

---

```
ui_print("");
ui_print(".__                            __             .___");
ui_print("|__| ____   ____  ____ _______/  |_  ____   __| _/");
ui_print("|  |/    \_/ ___\/ __ \____ \   __\/ __ \ / __ | ");
ui_print("|  |   |  \  \__\  ___/|  |_> >  | \  ___// /_/ | ");
ui_print("|__|___|  /\___  >___  >   __/|__|  \___  >____ | ");
ui_print("        \/     \/    \/|__|             \/     \/ ");
ui_print("");
```
