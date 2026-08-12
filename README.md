# INDEVOLT integration for Home Assistant

[简体中文](README.zh-CN.md) · [Change log](CHANGE.md)

A Home Assistant custom integration to monitor and control
[INDEVOLT](https://www.indevolt.com/) devices.

## Prerequisites

- [ ] Home Assistant has been installed according to the [official installation guide](https://www.home-assistant.io/installation/).
- [ ] The Indevolt device and Home Assistant server are on the **same local network**.
- [ ] The Indevolt device is powered on and has obtained an **IP address**.
  - Query via router’s management list;
  - Check in INDEVOLT App device settings;
- [ ] Ensure that the Indevolt device **API function is enabled**. This integration only supports OpenData HTTP mode.
<img width="800" alt="3http_mode" src="https://github.com/user-attachments/assets/67f8ed96-abb8-4368-b3f3-b2a3484bd4b9" />

- [ ] Confirm the firmware version meets the minimum requirement.

  | Model                       | Minimum Firmware Version        |
  | --------------------------- | ------------------------------- |
  | BK1600/BK1600Ultra          | V1.3.0A_R006.072_M4848_00000039 |
  | SolidFlex2000/PowerFlex2000 | CMS: V1406.07.002E |

<img width="400" alt="4fw_version" src="https://github.com/user-attachments/assets/7fb6d58f-9c95-4945-b588-810e68481f5b" />

## Install with HACS

This repository is installed through HACS as a custom repository:

1. Open HACS in Home Assistant.
2. Open the menu in the upper-right corner and select **Custom repositories**.
3. Enter `https://github.com/INDEVOLT/homeassistant-indevolt`, select
   **Integration** as the type, and click **ADD**.
4. Open **INDEVOLT** in HACS and select **Download**.
5. Restart Home Assistant.
6. Go to **Settings** > **Devices & services** and add INDEVOLT.

If an Indevolt entry created by another same-domain implementation already
exists, read [Switching between same-domain implementations](#switching-between-same-domain-implementations)
before installing this repository.

HACS and the manual method below both install the same
`custom_components/indevolt` directory. Do not combine files installed by the
two methods.

## Manual installation

### Step 1: Download the repository

1. Click **Code** > **Download ZIP**.
2. Unzip the ZIP file to your computer.

### Step 2: Locate the Home Assistant configuration directory

- **Home Assistant OS**: The configuration directory is located in `/config`.
- **Home Assistant Container**: You can access the configuration directory by locating the `configuration.yaml` file.

**Tip**: The directory should contain a `configuration.yaml` file.

```
config directory/
└── configuration.yaml
```

### Step 3: Create the custom integration directory

1. Enter the config directory.
2. Create the `custom_components` directory if it does not exist.

```
config directory/
├── custom_components/
└── configuration.yaml
```

**Note**: All custom integrations must be placed under `custom_components`, otherwise HA will not be able to recognize them.


### Step 4: Add the integration files

1. In the extracted repository, locate `custom_components/indevolt`.
2. Copy that complete `indevolt` directory into the Home Assistant
   `custom_components` directory. Do not merge it with files from another
   version.

Example installation path (the files inside `indevolt` vary by version):

```
config directory/
└── custom_components/
    └── indevolt/
        ├── __init__.py
        ├── manifest.json
        └── ...
```

### Step 5: Restart Home Assistant

1. Select **Settings** > **System** in the web interface.
2. Click the restart icon in the upper right corner.
3. Click **Restart Home Assistant**.
4. Click **RESTART**.

<img width="1000" alt="5restart_ha" src="https://github.com/user-attachments/assets/1270a590-faf8-43a4-8989-27923d1f3887" />


### Step 6: Add the integration to Home Assistant

1. After restarting, enter the web interface and select **Settings** > **Devices & services**.
    <img width="800" alt="" src="https://github.com/user-attachments/assets/f19c8fba-7eec-4994-8fed-4b5a7b2b2d3b" />


2. Click **+ADD INTEGRATION** in the lower right corner.  
   <img width="150" alt="image" src="https://github.com/user-attachments/assets/9282240e-f408-4ab0-a2ca-e6701994eaee" />

3. Search for integration INDEVOLT.  
    <img width="400" alt="" src="https://github.com/user-attachments/assets/836a3d34-d2ad-44c0-87f2-79fc80acd52d" />

4. Configuration parameters:
   - `host`: Device IP address, which can be obtained by checking the router/app.
   - `scan_interval`: Used to control the frequency of data updates, default is 30 seconds.  

     <img width="300" alt="" src="https://github.com/user-attachments/assets/0a0d38ed-15ed-4072-98bf-c94920d362cb" />

5. Click **SUBMIT** to finish the installation.
6. Follow the Home Assistant prompts to complete setup.

    <img width="300" alt="image" src="https://github.com/user-attachments/assets/f316fa13-44e4-4325-b3a8-09b904b0bd6f" />


## View Integration

Select the INDEVOLT integration to display the device and entity information.

<img width="300" alt="" src="https://github.com/user-attachments/assets/3997f4c9-c146-4c87-9d48-c0970dbe833c" />

<img width="800" alt="" src="https://github.com/user-attachments/assets/c26f0a2c-70ae-456b-9c66-683c2cb52617" />




## Update integration

### Update with HACS

1. Create a Home Assistant backup before updating.
2. Install the update from **Settings** > **Updates**, or open INDEVOLT in HACS
   and select **Redownload**.
3. Restart Home Assistant.
4. Confirm that the existing INDEVOLT entry, devices, and entities still load.

To roll back, open **Redownload** and choose the earlier version if HACS offers
a version selector. If no earlier version is available, restore a backup of the
complete `custom_components/indevolt` directory or reinstall the required
repository version manually. Restart Home Assistant afterward.

### Update manually

1. Back up the entire existing `custom_components/indevolt` directory outside
   `custom_components`, and record the currently installed version.
2. Download the new version and replace the installed `indevolt` directory with
   the complete `custom_components/indevolt` directory from that version. Do
   not merge files from different versions.
3. Keep the existing INDEVOLT integration entry, devices, and entities. This
   update does not require deleting or adding the entry again.
4. Restart Home Assistant.
5. Confirm that INDEVOLT loads without related errors and that the existing
   integration entry, devices, and entities are still present.

### Roll back a manual update

If validation fails, replace the entire `custom_components/indevolt` directory
with the backup, restart Home Assistant, and confirm that the original
integration entry, devices, and entities load normally.

### Switching between same-domain implementations

Removing this repository from HACS or deleting `custom_components/indevolt`
does not delete the saved integration entry. It also does not convert that entry
for the Indevolt integration already present in Home Assistant. The two
implementations store different configuration data even though they use the
same domain.

Before switching in either direction:

1. Create a Home Assistant backup.
2. Record the affected devices, entity IDs, dashboards, scripts, and automation
   references.
3. Remove the current Indevolt integration entry, switch the installed code,
   restart Home Assistant, and add Indevolt again with the target
   implementation.
4. Verify the recreated entities and repair any changed references before
   resuming automations.


## Create Automation: Set Real-Time Control

1. Go to **Settings** > **Automations & scenes**.
    <img width="800" alt="" src="https://github.com/user-attachments/assets/b5bb0b3a-9fce-49ae-b0ce-c9637e69cf9d" />

2. Click the button in the lower right corner **+ Create automation**.
    <img width="800" alt="" src="https://github.com/user-attachments/assets/6c3ed052-eba3-4ae1-b344-4b3c4004eb80" />

3. Select **Create new automation**.  
   <img width="300" alt="image" src="https://github.com/user-attachments/assets/0dd42045-2eeb-4750-b4a6-d8ada2289b0b" />

4. Click **+ Add Trigger** and configure the trigger event based on your requirements.  
   <img width="500" alt="image" src="https://github.com/user-attachments/assets/2988715f-c0ae-4bac-964e-7d483540120f" />

5. Click **+ Add Action** to configure the device action.
6. Select the Action for the target model:
   - **Set SolidFlex2000/PowerFlex2000 Work Mode**; or
   - **Set BK1600/BK1600 Ultra Work Mode**.

   The screenshots below use SolidFlex2000/PowerFlex2000 as the example.
   <img width="300" alt="image" src="https://github.com/user-attachments/assets/9b03b0f5-ecbd-43eb-a1f1-e3b82019724f" />

7. In the **Target** section, click **+ Choose Device** and select your device from the list.  
    <img width="800" alt="" src="https://github.com/user-attachments/assets/91964bf7-454e-48b3-9064-badb18706489" />
    <img width="300" alt="image" src="https://github.com/user-attachments/assets/6a7b6638-5be3-4749-aed2-f088a73d8fd4" />


8. In the **Work Mode** section, choose **Real-Time Control**, then configure **Status**, **Power**, and **Target SOC** as needed.  
    <img width="300" alt="image" src="https://github.com/user-attachments/assets/bedb1966-513f-4246-b7c4-5f5c579a2e3f" />
    <img width="300" alt="image" src="https://github.com/user-attachments/assets/a6ffeff5-e5c7-45a4-8aa5-5a948ce04b36" />

9. Click **Save** to complete the automation setup.

## FAQ

| Problem Description | Solutions |
| ------------------- | ----------|
| Integration not found in search list | Verify the integration file is located in the correct folder: `custom_components/indevolt`. |
| The integration stops loading after switching between implementations | Same-domain config entries are not automatically converted. Restore the previous code or remove the existing entry and add Indevolt again with the implementation you want to use. |
| - Unable to add  device. <br> - Unable to connect to the device.  <br> - No data available   | This is typically caused by an **HTTP request failure**. <br>  1.  Verify the device is powered on.<br> 2. Confirm the device's IP address is correct.<br> 3. Check the device's network status in Indevolt app.<br>4. Ensure you have met all the [prerequisites](#prerequisites). |

If you encounter any issues, please check the **Home Assistant logs** for detailed error messages.

## Contribute

We welcome your feedback and contributions! Please feel free to open an issue with your suggestions or submit a pull request.
