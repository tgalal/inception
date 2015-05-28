Inception
=========
Inception is a set of tools for quick, easy modification and deployment of android roms.

#In short

For a brand new device Inception helps you automate the following:

- Generate all device settings
- Include any apps to be be (pre)installed
- Remove any stock apps
- Root the device
- Configure Wifi networks
- Patch APKs
- Replace Kernel, and/or ramdisk data in both boot and recovery imgs
- Place your adb keys

# Usage:
```python incept.py ACTION [args]```

Where ACTION is one of:

- bootstrap
- make
- plant
- learn

Explanation of each action and its arguments are found under "[Actions](#actions)"

# Use Cases

## Business which distribute devices
For business which rely on tablets/phone customization and distribution. For example those that provide restaurants and hotels with devices for their guests and customers to use. It's important that they are able to easily have a custom build configuration per target. And with the hierarichal configuration approach Inception uses, it eliminates all redundant information that are common across those different devices, reducing the complexity to a high degree

## Company devices
This tool allows quick setup of work phones/tablets provided to employees in a company. In a few seconds the company can prepare a newly out of the box device with the company's apps, wifi settings, security settings.. etc

# How it works

## config.json

You specify your configuration in JSON format. Your configuration can extend another configuration, and so you can have common parent configurations.

### base configs dir

This dir contains base configurations. It should ideally contain purely device-specific configs, or configurations that are generic and are meant to be only extended and not used directly.
```

samsung
    samsung.json

tab3
    tab3.json
```

### variant configs dir

This is where all target product-specific configs would go. A variant must extend a base config, or another variant.

```
samsung
    tab3
        restaurant_mainbranch
            restaurant_mainbranch.json
        restaurant_southbranch
            restaurant_southbranch.json
    tab4
        ...
```


You only need to modify the variant directory:
 - Add files to its fs directory
 - Modify contents of boot and/or recovery
 - Swap kernels
 - Modify ramdisk
 - Update the json config
 - Add Wifi networks
 - Add apps
 - Remove system apps
 - Configure Adb keys

Basically however you want your device to be like when it boots the first time you can setup that in the variant dir.

Once done, Inception compiles your config and generates an "update.zip", which is basically and Android OTA update that applies your config to the device.
Optionally inception could also generate the following:
    - cache.img
        - This bundles the previously generated update.zip inside, and instructions for the device to apply this update once flashed with it.
    - recovery.img
        - Typically a custom recovery, since stock recovery won't accept our generated update.zip unless you have manufacturer's signing keys
    - boot.img
        - In case you're modifying the boot kernel or ramdisk

You can toggle each of those generated stuff separately depending on what you need.

## Getting started
### Directory structure
**Base directory has the following hierarchy for defining a device config:**
  
  - Base_dir
    - Vendor_A_Name
        - Model_A_Name/Identifier
            - Model_A_Name/Identifier.json
        - Model_B_Name/Identifier
            - Model_B_Name/Identifier.json
        - ...
    - Vendor_B_Name
    - ...

**Variant directory is generated with the following hierarchy:**

 - Variants_dir
    - Vendor_A_Name
        - Model_A_Name/Identifier
            - Model_A_Name/Identifier
                - Variant_A_Name
                    - Variant_A_Name.json
                - Variant_B_Name
                    - Variant_B_Name.json
                - ...
            - Model_B_Name/Identifier
            - ...
        - ...
    - Vendor_B_Name
    - ...

**Output directory is where final built images are placed**

 - Out_dir
    - Vendor_A_Name
        - Model_A_Name/Identifier
            - Model_A_Name/Identifier
                - Variant_A_Name
                    - boot.img
                    - cache.img
                    - recovery.img
                    - update.zip
                - Variant_B_Name
                    - boot.img
                    - cache.img
                    - recovery.img
                    - update.zip
                - ...
        - Model_B_Name/Identifier
            - ...
        - ...
    - Vendor_B_Name
    - ...

### Actions
#### Creating a new variant
```bootstrap [-h] -b BASE -v VARIANT [-f] [-s]```

You create a new variant using "bootstrap" action. It accepts as argument the name of base configuration to which the new one will extend. It also accept the name of the new configuration name.

##### How it works:
The provided variant name should be in the format "VENDOR.model.variant". Using this code, it creates the directory structure VENDOR/MODEL/VARIANT. Inside that directory it creates a basic configuration, inside which a property called "extends", with value set as parent configuration name. This value will be used in other actions to recreate the full configuration based on specified parents heierarchy.
It also creates 2 empty directories, that is "imgs" and "fs". Inside imgs, boot image and recovery img will be extracted. This allows for easily modification of imgs as desired, they will then be automatically repacked later.
"fs" dir contains 2 empty directories, "data" and "system". Content inside those directories will be deployed to the device.

#### Deploying a variant
```plant [-h] -v VARIANT -t (heimdall|dd) [-m] [-b] [-c] [-r]```

"plant" action deploys a variant to the device using  several possible methods depending on the device power state.

Supported methods, specified via -t/--through include:

 - heimdall:   for samsung devices in download mode
 - dd:         for devices in recovery mode or normal mode with root access. Might require more configuration.
 - fastboot:   for devices which support fastboot

This action expects the variant images to be already build using "make" action. Or you can tell it to build the variant using "-m/--make" switch. You can also specify which image to flash if you don't want them all to be deployed. 

#### Other actions:
##### learn
```learn [-h] -v VARIANT```

If you have a device which you have already adjusted the settings, installed apps and other stuff, then this action allows you to download these data to the FS of your variant. And so when you deploy the variant, it will be identical to your original device in settings and others.


### Config file
Config file is basically a JSON file containing all configuration values necessary for building a customized variant. It must carry the same name as the containing directory (model identifier/ variant name) and .json extension.

The following keys are currently supported:

 - **extends:** \[String\] Parent config name
 - **device:** \[Object\] Contains information about the device
    - **name:** \[String\] Identifier name for that device
    - **manufacturer:** \[String\] Manufacturer's name
    - **model_name:** \[String\] Model name
    - **model_numer:** \[String\]
 - **imgs:** \[Object\] (Required) Paths to different images
    - **boot:** \[String\] (Required) Path to boot image
    - **recovery:** \[String\] (Required) Path to recovery image
 - **fstab:** \[Object\] (Required) information about the device filesystem. It will NOT be used to create any fstab file.
    - **cache:** \[Object\] (Required) Information about the cache partition
        - **dev:** \[String\] device name
        - **type:** \[String\] Filesystem type
        - **mount:** \[String\] (Required) Cache mount point
        - **size:** \[Integer\] (Required) Size in bytes
        - **sparsed:** \[boolean\] (Required) Whether cache.img files should be sparsed
        - **pit_name:** \[String\] Partition name for devices which support download mode, used by plant action
    - **data:** \[Object\]
        - ...
    - ...
 - **fs:** \[Object\]:
    - **add:** \[Array\] An array files/dirs inside fs dir to deploy on the device
    - **rm:** \[Array\] An array of file paths to delete from the device.
 - **files:** \[Object\] It contains information about files on the device.
    - **/path/to/file:** \[Object\] The key references the file or dir
        - **uid:** \[String\] Owner ID numerical value
        - **gid:**  \[String\] Group ID numerical value
        - **mode:** \[String\] File mode if it's a file
        - **mode_files:** \[String\] Mode of contained files, if it's a dir
        - **mode_dirs:** \[String\] Mode of contained dirs, if it's a dir
    - ...
 - **config:** \[Object\] Contains configuration for different tools and paths used by Inception
    - **make_ext4fs:** \[Object\] config for make_ext4fs
        - **bin:** \[String\] Path to make_ext4fs binary. If the binary path contains "device://" as prefix, it will be executed on the device. You need to connect the device with adb enabled for this to succeed.
    - **mkbootimg:** \[Object\] config for mkbootimg
        - **bin:** \[String\] Path to mkbootimg binary
    - **unpackbootimg:** \[Object\] config for unpackbootimg
        - **bin:** \[String\] path to unpackbootimg binary
    - ...


## License
Contact: Tarek Galal <tare2.galal@gmail.com>

License:

    Copyright (c) 2012, Tarek Galal <tare2.galal@gmail.com>

    Inception is free software: you can redistribute it and/or modify it under the terms 
    of the GNU General Public License as published by the Free Software Foundation, 
    either version 2 of the License, or (at your option) any later version.

    Inception is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
    without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along with Wazapp. 
    If not, see http://www.gnu.org/licenses/.