# Handwritten Digit Recognition on Xilinx FPGA using DPU IP

This guide walks you through the hardware design of the DPU IP using Vivado 2021.1, Petalinux 2021.1 installation and setup, Vitis AI 1.4 installation and setup, and running a neural network model on FPGA for handwritten digit recognition.

---

## Vivado Setup

### 1. Create DPU Hardware Platform on Vivado 2021.1

#### Set up the Vivado environment:

- Open **Vivado 2021.1**
- Create a new project using the **ZCU104** board.
- Add the `dpu_ip` folder to the IP repository:
  
  - Go to **IP Catalog**
  - Right-click on **Vivado Repository**
  - Select **Add Repository**
  - Choose the `dpu_ip` directory

> **Note:**  
> The default settings of the DPU are:  
> - `B4096`  
> - `RAM_USAGE_LOW`  
> - `CHANNEL_AUGMENTATION_ENABLE`  
> - `DWCV_ENABLE`  
> - `POOL_AVG_ENABLE`  
> - `RELU_LEAKYRELU_RELU6`  
> - `Softmax`  
> 
> You can modify these settings in the DPU block configuration in your Vivado design.  
> ZCU104 has fewer BRAM resources than ZCU102, so we need to use both BRAM and URAM.  
> 
> In this project:
> - For **1 DPU core**: set UltraRAM usage to **30**
> - For **2 DPU cores**: set UltraRAM usage to **40**

---

### 2. Run the DPU Platform Creation Script

In the Vivado Tcl console, execute the following command to create the hardware platform with 1 DPU core:

```tcl
# Make sure to change the directory to your script path
cd hw_script
source dpux1_zcu104.tcl
```
### Block Design of the DPU TRD Project

3. **Create HDL Wrapper:**  
   - In the **Design Sources**, right-click on `top.bd`
   - Select **Create HDL Wrapper**
   - Choose **Let Vivado manage wrapper and auto-update**
   - Click **OK**

4. **Generate Pre-synthesis Design:**  
   - From the **Flow Navigator**, click **Generate Block Design**
   - Under **Synthesis Options**, select **Out of context per IP**

5. **Change Implementation Strategy:**  
   - Open **Implementation Settings**
   - Change the strategy from `Default` to `Performance_ExplorePostRoutePhysOpt`
   - Navigate to **Post-Route Phys Opt Design**
   - Expand the **-directive** option
   - Choose `AggressiveExplore`

   > ⚠️ This step helps resolve timing issues that may occur with the default implementation strategy.

6. **Generate Bitstream:**  
   - Click on **Generate Bitstream** from the Flow Navigator

> ⏳ Bitstream generation may take approximately **45 minutes**.  
> In the meantime, you can proceed with setting up the Ubuntu environment for **Petalinux**.



## PetaLinux Installation
This section explains how to install and configure PetaLinux on an Ubuntu-based system (Ubuntu 20.04). These steps prepare the environment, install required dependencies, and configure TFTP for booting the FPGA.

---

### 🛠️ Initial System Setup
```bash
sudo apt update
sudo apt upgrade
```
Reconfigure dash to use bash instead (important for build scripts):
```bash
sudo dpkg-reconfigure dash
# Choose <No> when prompted
```
Enable 32-bit architecture and grant user permissions for serial communication:
```bash
sudo dpkg --add-architecture i386
sudo adduser $USER dialout
```

### 📦 Install Required Packages
Install all dependencies needed by PetaLinux, cross-compilation tools, networking utilities, and TFTP server:
```bash
sudo apt-get install gparted xinetd gawk gcc net-tools ncurses-dev openssl libssl-dev flex bison xterm autoconf libtool texinfo zlib1g-dev

sudo apt-get install iproute2 make libncurses5-dev tftpd libselinux1 wget diffstat chrpath socat tar unzip gzip python3 tofrodos lsb libftdi1 libftdi1-2

sudo apt-get install lib32stdc++6 libgtk2.0-0:i386 libfontconfig1:i386 libx11-6:i386 libxext6:i386 libxrender1:i386 libsm6:i386 tree openssh-server

sudo apt-get install debianutils iputils-ping libegl1-mesa libsdl1.2-dev pylint python3 cpio tftpd-hpa gnupg zlib1g:i386 haveged perl xvfb

sudo apt-get install gcc-multilib build-essential automake screen putty pax g++ python3-pip xz-utils python3-git python3-jinja2 python3-pexpect

sudo apt-get install liberror-perl mtd-utils xtrans-dev libxcb-randr0-dev libxcb-xtest0-dev libxcb-xinerama0-dev libxcb-shape0-dev libxcb-xkb-dev

sudo apt-get install util-linux sysvinit-utils cython3 google-perftools patch diffutils ocl-icd-libopencl1 opencl-headers ocl-icd-opencl-dev clang clangd

sudo apt-get install libncurses5 libncurses5-dev libncursesw5:amd64 libncursesw5-dev libncurses5:i386 libtinfo5 libstdc++6:i386 libgtk2.0-0:i386 dpkg-dev:i386

sudo apt install gedit

sudo apt update
sudo apt upgrade
```

### 🌐 Configure TFTP Server
TFTP (Trivial File Transfer Protocol) is needed to boot the FPGA over Ethernet from your development machine.
```bash
sudo gedit /etc/xinetd.d/tftp
```
Paste the following into the editor and save:
```
service tftp 
{
  protocol = udp 
  port = 69 
  socket_type = dgram 
  wait = yes 
  user = nobody 
  server = /usr/sbin/in.tftpd 
  server_args = /tftpboot 
  disable = no
}
```
Set Up TFTP Directory
```bash
sudo mkdir /tftpboot
sudo chmod -R 777 /tftpboot
sudo chown -R nobody /tftpboot
# Start TFTP Service
sudo /etc/init.d/xinetd stop
sudo /etc/init.d/xinetd start
```

## 🧰 PetaLinux Installer Setup & Project Creation

This section describes how to install the PetaLinux 2021.1 tools and create a PetaLinux project for the ZCU104 board.

---

### 📦 Install PetaLinux 2021.1

First, prepare the installation directory and run the installer:

```bash
# Create a directory for PetaLinux
sudo mkdir -p ~/PetaLinux/2021.1/
sudo chmod -R 755 ~/PetaLinux/2021.1/
sudo chown -R $USER:$USER ~/PetaLinux/2021.1/
```
Navigate to the directory where the petalinux-v2021.1-final-installer.run file is Downloaded, and run:
```bash
# Make the installer executable
sudo chmod 777 ./petalinux-v2021.1-final-installer.run

# Run the installer and specify the target installation directory
./petalinux-v2021.1-final-installer.run --dir ~/PetaLinux/2021.1/
```
After installation, set up the environment:
```bash
cd ~/PetaLinux/2021.1/
source settings.sh

# Confirm the installation
petalinux-create --help
```

## 🚀 Create PetaLinux Project

To begin, ensure you have:

- The **TRD BSP** file included in this repository: `ZCU104 TRD -BSP/xilinx-zcu104-v2021.1-05230256.bsp`
- A hardware description file (`.xsa`) exported from your Vivado project

---

### 📁 Create Project from BSP

```bash
mkdir -p ~/projects && cd ~/projects

# Use the BSP file from this repo (adjust the path)
petalinux-create -t project -s <TRD-BSP-Path>/xilinx-zcu102-trd.bsp -n zcu104_project
```

## ⚙️ Configure the PetaLinux Project
Navigate into the newly created project:

```bash
cd zcu104_project

# Replace the path below with the location of your .xsa file exported from Vivado
petalinux-config --get-hw-description=../../dpu_zcu104_hw
```
## 🔧 Configuration Steps
Once inside the config UI:

**Note :** In this by entering **'n'** in the [ ] menu selection will **Disable** the selection, and **'y'** in the [ ] menu selection will **Enable** the selection.


- Set board name, Yocto Settings → Yocto board settings (zcu104) YOCTO_BOARD_NAME

- Go to  → DTG Settings, change the Machine name to *zcu104-rev1.0* and make sure of kernel bootrags

- Go to → Firmware Version Configuration, Replace zcu102 with zcu104 wherever applicable

- Go to → Image Packaging Configuration, Disable tftp and set → Root filesystem type (EXT4 (SD/eMMC/SATA/USB))

Now Exit and Save.

---

### 📥 Add `meta-vitis-ai` Yocto Layer

To enable Vitis AI support in your PetaLinux build, you need to add the `meta-vitis-ai` layer to the Yocto build system.

```bash
git clone https://github.com/Xilinx/meta-vitis-ai.git -b rel-v2021.1
# remember this downloaded meta-vitis-ai layer package path
```
To Configure PetaLinux to Use This Layer run petalinux-config
```bash
petalinux-config
```
- Navigate to → Yocto Settings → User Layers 
- Select Add Layer
- Enter the full path to your cloned meta-vitis-ai directory. For example:
```bash
/home/user/<downloaded-path>/meta-vitis-ai
```

Then click ok, Exit and save

---

### 🧹 Remove Deprecated DNNDK Package

The **DNNDK** package is deprecated and no longer supported in `Vitis AI 1.4 (2021.1)`.  
Since we’ve added the `meta-vitis-ai` layer, we need to **remove the DNNDK entry** from the default Petalinux recipe to avoid conflicts in the file path plnx-prj-root/components/yocto/layers/meta-petalinux/recipes-core/packagegroups/packagegroup-petalinux-vitisai.bb



### ✏️ Edit `packagegroup-petalinux-vitisai.bb` File

Open the following file in a text editor:
Remove the following line:

```bash
dnndk \
```
The updated packagegroup-petalinux-vitisai.bb file should look like this:

```bash
DESCRIPTION = "PetaLinux Vitis AI packages"

inherit packagegroup

PACKAGE_ARCH = "${SOC_FAMILY_ARCH}"

COMPATIBLE_MACHINE = "^$"
COMPATIBLE_MACHINE_zynqmp = ".*"

RDEPENDS_${PN} = "\
    glog \
    googletest \
    json-c \
    protobuf \
    python3-pip \
    opencv \
    python3-pybind11 \
    vitis-ai-library \
    xir \
    target-factory \
    vart \
    unilog \
    "

RDEPENDS_${PN}-dev += "\
    protobuf-c \
    libeigen-dev \
    "
```

---
### 🎥 Enable `libv4l` and `libav` for OpenCV (Video Processing Support)

To enable **video input/output support** in OpenCV for applications using `libv4l` (V4L2) and `libav` (FFmpeg), you need to append these options to the OpenCV recipe using a `.bbappend` file.

```bash
mkdir -p <plnx-proj-root>/project-spec/meta-user/recipes-support/opencv
vim <plnx-proj-root>/project-spec/meta-user/recipes-support/opencv/opencv_%.bbappend
```
now add these Following lines in the vim editor, Press **'i'** to enter insert mode and copy paste below lines and then enter **Esc** to exit insert mode, Type **':wq'** to save and Exit.

```bash
# opencv_%.bbappend
PACKAGECONFIG_append = "libv4l libav"
```

---
### 📝 Edit `user-rootfsconfig` file

To include essential runtime libraries, tools, OpenCL, DPU support, X11, and development packages in your PetaLinux root filesystem, add the following configurations to the `user-rootfsconfig` file.

Open the file in the text editor: plnx-prj-path/project-spec/meta-user/conf/user-rootfsconfig and copy paste the following

```bash
CONFIG_gpio-demo
CONFIG_peekpoke
CONFIG_packagegroup-petalinux-v4lutils
CONFIG_packagegroup-petalinux-audio
CONFIG_xrt
CONFIG_xrt-dev
CONFIG_opencl-clhpp-dev
CONFIG_opencl-headers-dev
CONFIG_dpu
CONFIG_dpcma
CONFIG_dnf
CONFIG_e2fsprogs-resize2fs
CONFIG_parted
CONFIG_packagegroup-petalinux-vitisai
CONFIG_packagegroup-petalinux-self-hosted
CONFIG_cmake
CONFIG_packagegroup-petalinux-vitisai-dev
CONFIG_packagegroup-petalinux-opencv
CONFIG_packagegroup-petalinux-opencv-dev
CONFIG_mesa-megadriver
CONFIG_packagegroup-petalinux-x11
CONFIG_packagegroup-petalinux-matchbox
```

---
### 📝 Edit `petalinuxbsp.conf` file
Enable the GStreamer1.0-libav package and whitelist the license flag:

Go to plnx-proj-root-path/project-spec/meta-user/conf/petalinuxbsp.conf and **add Following lines**

```bash
IMAGE_INSTALL_append = " gstreamer1.0-libav"
LICENSE_FLAGS_WHITELIST_append = " commercial_gstreamer1.0-libav"
```

---
### 📝 Edit `system-user.dtsi` file
**Update the Device tree** Look at the Address Editor on Vivado project to see the base-addr and interupt number of DPU and change its value in project-spec/meta-user/recipes-bsp/device-tree/files/system-user.dtsi.

```bash
/include/ "system-conf.dtsi"
/{
        dpu@80000000 {
                compatible = "deephi, dpu";
                reg = <0x0 0x80000000 0x0 0x700>;
                interrupts = <0x0 106 0x1>;
                interrupt-parent = <&gic>;
                core-num = <0x1>;

                softmax@800001000 {
                        compatible = "deephi,smfc";
                        interrupt-parent = <&gic>;
                        interrupts = <0x0 0x6e 0x1>;
                        core-num = <0x1>;
                };
        };
        dpcma: dpcma {
                compatible = "deephi,cma";
        };
};

&sdhci1 {
      no-1-8-v;
      disable-wp;
};
```
⚠️ Make sure the base addresses and interrupt numbers match those in your actual Vivado design.

Apply Changes

---

### 🧩 Root Filesystem Configuration
Now, configure the root filesystem for the PetaLinux project. 

Run the below command
```bash
petalinux-config -c rootfs
```
Follow the below steps :

- Go to → user packages → modules, **Select all the list of packages which were added in the user-rootfsconfig file**

- Go to → Image Features, Disable ssh-server-dropbear, enable ssh-server-openssh, enable package-management and debug_tweaks option and click Exit

- Go to → Filesystem Packages → misc → packagegroup-core-ssh-dropbear, Disable packagegroup-core-ssh-dropbear and click Exit

- Go to → Filesystem Packages-> console → network → openssh, enable openssh, openssh-sftp-server, openssh-sshd, openssh-scp and click exit

- Go to → Filesystem Packages  → console  → utils → Vim, enable Vim and exit

- Go to → Petalinux Package Groups → packagegroup-petalinux-gstreamer, enable packagegroup-petalinux-gstreamer and exit

Go back to root level by Exit four times and save.

---

### ⚙️ Kernel Configuration
un the following command to configure the Linux kernel options for your PetaLinux project:

```bash
petalinux-config -c kernel
```
- Go to → CPU Power Mangement → CPU Idle → CPU idle PM support and disable it

- Go to → CPU Power Management → CPU Frequency scaling → CPU Frequency scaling and disable it

Exit and Save.

---

### 🔨 Build the PetaLinux Project
Run the Build
```bash
petalinux-build
```
This step will compile the kernel, device tree, and root filesystem based on your hardware (.xsa) and configuration. It may take some time depending on your system.

----

### 🧰 Troubleshooting Checks

If you encounter issues during the build process, here are some common things to check:


### Mirror Configuration

- Different versions of PetaLinux may use different mirror servers.
- Some mirrors might become outdated or unavailable.
- Recommended: Use **archive mirrors** instead of the default ones to avoid broken link issues.


### Network and Download Issues

- If you're building **offline**, make sure all necessary downloads are pre-fetched.
- On some corporate or restricted networks, **sstache** or recipe downloads may be blocked, leading to:
  - `fetch failed` errors
  - `checksum mismatch` issues
- Solution: Try building on an unrestricted network or use a proxy with correct configuration.


### TMP Space Overflow

- In `build/conf/layer.conf`, you can reduce the TMP file limit to avoid build failures related to excessive temp file usage.
- This helps in cases where you encounter `do_compile` or `do_rootfs` tasks getting stuck or killed.



### Disk Space Requirements

- A general PetaLinux build requires **at least 30 GB** of free disk space.
- A DPU-enabled build (especially with Vitis AI) can consume **up to 80 GB** or more.
- Ensure you have **sufficient free space** before running `petalinux-build`.

---


### 📦 petalinux-package (Create Boot Image)


Once the `petalinux-build` completes successfully, the final step is to package the bootable files into a `BOOT.BIN` file.

```bash
# Navigate to the output directory:
cd images/linux/

# Run the following command to generate the boot image:
petalinux-package --boot --force --fsbl ./zynqmp_fsbl.elf --fpga ./system.bit --u-boot u-boot.elf --pmufw ./pmufw.elf
```
The output will be a BOOT.BIN file in the same directory.
Finally, copy files to the SD-card

---



## 💾 Copy Files to SD Card

To prepare your SD card for booting the ZCU104 board, you need to create **two partitions**:

- 🟡 **Boot Partition** – FAT32 format
- 🔵 **Root File System (rootfs)** – EXT4 format


### 🔍 Check for Devices

Before beginning, identify the correct device path for your SD card.

### List USB Devices
```bash
ls /dev/ttyUSB*
# df -List Block Devices 
```
```bash
lsblk /dev/sdb
# Note: Replace /dev/sdb with your actual SD card device.
```

## 🧩 Partitioning the SD Card
Run fdisk to configure the partitions:

```bash
sudo fdisk /dev/sdb
```

View current partition table:

```bash
Command (m for help): p
```
Delete existing partitions (if any):
```bash
Command (m for help): d
```
Repeat if multiple partitions exist.


---
### Create Boot Partition

1. Create new partition:

```bash
Command (m for help): n
```
2. Choose primary partition (p), and use default partition number and first sector.

3. Set size for boot partition: +1G

4. Set the bootable flag:

```bash
Command (m for help): a 
#by entering a it will make this created partition as a boot partition
```
### Create Root Filesystem Partition
5. Create another new partition:

```bash
Command (m for help): n
```
6. Choose primary partition (p), and accept default values for first and last sectors.

Review Partition Table
```bash
Command (m for help): p
```
Expected output:

```bash
Device     Boot   Start      End   Sectors   Size  Id  Type
/dev/sdb1  *       2048   2099199   2097152   1G    b   W95 FAT32
/dev/sdb2       2099200  15564799  13465600   6.4G  83  Linux
```
Write and Exit
```bash
Command (m for help): w
```
now partitons are created succesfully

---
---

Below is the exact flow how it looks like:


---
```bash
Command (m for help): n                     # enter 'n' here
Partition type
   p   primary (0 primary, 0 extended, 4 free)
   e   extended (container for logical partitions)
Select (default p): p                       # enter  'p' here
Partition number (1-4, default 1):          # click Enter
First sector (2048-15564799, default 2048): # click Enter
Last sector, +/-sectors or +/-size{K,M,G,T,P} (2048-15564799, default 15564799): +1G  # enter '+1G' here and enter

Created a new partition 1 of type 'Linux' and of size 1 GiB.
Partition 

Do you want to remove the signature? [Y]es/[N]o: Y  # choose 'Y' here

The signature will be removed by a write command.

Command (m for help): a   # enter 'a' here to make the created partition as boot
Selected partition 1
The bootable flag on partition 1 is enabled now.

Command (m for help): n                              # enter 'n' here
Partition type
   p   primary (1 primary, 0 extended, 3 free)
   e   extended (container for logical partitions)
Select (default p): p                                # enter  'p' here
Partition number (2-4, default 2):                   # click Enter
First sector (2099200-15564799, default 2099200):    # click Enter
Last sector, +/-sectors or +/-size{K,M,G,T,P} (2099200-15564799, default 15564799):  # click Enter

Created a new partition 2 of type 'Linux' and of size 6.4 GiB.
Partition

Do you want to remove the signature? [Y]es/[N]o: Y   # choose 'Y' here

The signature will be removed by a write command.

Command (m for help): p   # enter  'p' here to check the created partitions
Disk /dev/sdb: 7.43 GiB, 7969177600 bytes, 15564800 sectors
Disk model: STORAGE DEVICE  
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: dos
Disk identifier: 0x522f5659

Device     Boot   Start      End  Sectors  Size Id Type
/dev/sdb1  *       2048  2099199  2097152    1G 83 Linux
/dev/sdb2       2099200 15564799 13465600  6.4G 83 Linux

Filesystem/RAID signature on partition 1 will be wiped.
Filesystem/RAID signature on partition 2 will be wiped.

Command (m for help): w  # enter 'w' here to save and exit
The partition table has been altered.
Calling ioctl() to re-read partition table.
Syncing disks.

```

---
---
## lets Copy files to SD card
Before copying, create mount directories to attach the SD card partitions:

```bash
sudo mkdir /mnt/boot
sudo mkdir /mnt/rootfs
```
####  Navigate to Your PetaLinux Project's Output Directory: Go to --> plnx-prj-path/images/linux/

Copy bootfile to SD card Boot Partition (FAT32)
```bash
sudo mount /dev/sdb1 /mnt/boot
sudo cp BOOT.BIN boot.scr Image system.dtb /mnt/boot
sudo umount /mnt/boot
```
Copy rootfs file to SD card Rootfs Partition (EXT4)
```bash
sudo mount /dev/sdb2 /mnt/rootfs
sudo tar -xvzf rootfs.tar.gz -C /mnt/rootfs
sudo umount /mnt/rootfs
```
✅ Once done, safely eject the SD card and insert it into your Zynq UltraScale+ board for boot.

## Connect the Target board & open the serial terminal

Once your SD card is ready and inserted into the Zynq board, power it ON and connect the UART/USB cable to your PC.

If you're using Ubuntu Server (terminal only), you can open a serial terminal using the following command-line tools:
```bash
lsusb
dmesg | grep ttyUSB
# Open Serial Terminal Using screen
sudo screen /dev/ttyUSB1 115200  
```

---
Once the system finishes booting, you'll see a login prompt.

Login credentials:
```bash
Username: root
Password: root
```
if you feel something went wrong then try once again copying file to SD card

---
### 🧼 Steps for Formatting the Partitions of SD-card
Unmount the device if mounted:

```bash
#before runnign this commad check where the device is mounted
sudo umount /dev/sdb1  
sudo umount /dev/sdb2
```
Format the partitions:

Format boot partition as FAT32:

```bash
sudo mkfs.vfat -F 32 /dev/sdb1
```
Format rootfs partition as ext4:

```bash
sudo mkfs.ext4 /dev/sdb2
```
Now the both partitions were cleaned succefully


#### Run the resnet example in the target just to verify it.

---

## 🐳 Docker Installation on Ubuntu

```bash
# Update and Install Required Packages
sudo apt update
sudo apt install apt-transport-https ca-certificates curl software-properties-common -y

# Add Docker’s Official GPG Key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Add Docker Repository
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Verify Repository is Set Correctly
apt-cache policy docker-ce

# Install Docker Engine
sudo apt install docker-ce -y
sudo systemctl status docker

# Verify Docker Installation
docker --version
sudo docker run hello-world
```
Pull and Run Docker Image
```bash
sudo docker pull [image-name]
sudo docker run [image-name]
sudo docker run --name [container-name] [image-name]
```

To avoid needing `sudo` every time you use Docker, Add Your User to Docker Group
```bash
sudo usermod -aG docker $USER

# ⚠️ You must log out and log back in, or run:
newgrp docker
```

#### After Reboot, Confirm Docker Works Without `sudo`

```bash
docker run hello-world
```

Docker is succesfully installed.

## 🚀 Run Vitis AI DPU Flow in Docker

Choose the Correct Docker Image Version from here: https://hub.docker.com/r/xilinx/vitis-ai-cpu/tags 

Since we are using DPU IP v3.3, it requires Vitis AI v1.4. Let's pull the corresponding Docker image. if you have gpu pully the `vitis-ai-gpu`

```bash
docker pull xilinx/vitis-ai-cpu:1.4.1.978
```
👉 If you have a GPU, pull the `vitis-ai-gpu` Docker image instead:

```bash
docker pull xilinx/vitis-ai-gpu:<version>
```
#### Run the Docker Container

```bash
docker run -it --rm -v ~/docker_workspace:/workspace xilinx/vitis-ai-cpu:1.4.1.978 /bin/bash
```


### Activate TensorFlow Environment

First, activate the Vitis AI TensorFlow Conda environment:
```bash
conda activate vitis-ai-tensorflow
```
Make sure Python 3.8 is being used for tensorflow 1.x inside the Docker container. 

---

### Tarin the model
Run the training script
```bash
python DigitRecognitiion_model.py
```
This will train your handwritten digit recognition model and save the trained model in `.pb` (frozen graph) format.

---

### Prepare Calibration Dataset
To perform quantization, you'll need a calibration dataset with at least 100-1000 images.
```bash
python generate_calib_images.py
```
Then, generate a list of image filenames:

```bash
ls calib_images > labesls.txt
```

To inspect the input and output nodes of your frozen model :
```bash
vai_q_tensorflow inspect --input_frozen_graph=/tmp/inception_v1_inf_graph.pb
```

---

### Run Quantization

You need an input_fn.py script to preprocess the calibration images. It should define how input images are loaded and formatted for quantization.

Ensure it includes:

- Correct paths to calib_images and labels.txt

- Batch size set to 20

- Calibration iterations (calib_iter) set to 5

This means: 20 x 5 = 100 images total for quantization.


Here’s the command to run quantization:
```bash
vai_q_tensorflow quantize \
  --input_frozen_graph DigitRecognitiion_model.pb \
  --input_nodes input \
  --input_shapes ?,28,28,1 \
  --output_nodes logits \
  --input_fn input_fn.calib_input \
  --method 1 \
  --gpu 0 \
  --calib_iter 2 \
  --output_dir quantized_model
```

⚠️ Note: Make sure:

- Your model file is named correctly (DigitRecognition_model.pb).

- Input/output nodes (input, logits) match your graph (you can confirm them using vai_q_tensorflow inspect).

- The input_fn.calib_input is a valid Python module path (e.g., input_fn.py must contain a function named calib_input()).

---

### Run Compilation
Once the model is quantized, compile it for your target DPU (ZCU104 in this case):

```bash
vai_c_tensorflow \
  --frozen_pb quantized_model/quantize_eval_model.pb \
  --arch /opt/vitis_ai/compiler/arch/DPUCZDX8G/ZCU104/arch.json \
  --output_dir compiled_model \
  --net_name digitRecognitiion
```
#### This will generate the final .xmodel file inside compiled_model/.

---

### Deploy to Target

After compiling your .xmodel file, deploy it to the ZCU104 target board along with your test images.

You can transfer files using either:

- Option 1: scp (Secure Copy)
```bash
scp compiled_model/mnist_model.xmodel root@<board-ip>:/home/root/
scp -r sample_images/ root@<board-ip>:/home/root/
```
- Option 2: SD Card
Copy the .xmodel and sample_images/ directory to the second partition (/mnt/rootfs) of your SD card, then insert the card into the board.

Additonally, copy the inference C++ file `inference_code.cpp` which is available in this repository.

Once on the board, compile your C++ inference file using the following command:
```bash
g++ -std=c++17 -O2 inference_code.cpp -o mnist_model \
  -I/usr/include/opencv4 \
  -L/usr/lib \
  -lopencv_core -lopencv_imgproc -lopencv_imgcodecs \
  -lglog -lxir -lvart-runner -lvart-dpu-runner -lvart-mem-manager
```
This will generate a binary executable named `mnist_model`.

To run the inference, you’ll need three arguments:

- The binary executable file
- The `.xmodel` file path
- The sample image path

```bash
# Format: ./<binary>          <path-to-xmodel>         <path-to-image>
./mnist_dpu compiled_model/mnist_model.xmodel sample_images/img_01.png
```

### Expected output is shown Below
```bash
root@xilinx-zcu104-2021_1:~/HandWrittenDigitRecognition# ./mnist_model compiled_model/digitRecognitiion.xmodel test_images/img_011.png
Predicted Digit: 5
Class 0: 2.74654e-43
Class 1: 0
Class 2: 0
Class 3: 5.38019e-32
Class 4: 0
Class 5: 1
Class 6: 1.60381e-28
Class 7: 0
Class 8: 1.42516e-21
Class 9: 3.78351e-44

--- Performance Metrics ---
Inference Time: 0.227 ms
Throughput (FPS): 4405.29 frames/sec
root@xilinx-zcu104-2021_1:~/HandWrittenDigitRecognition#
```

# References
- Vitis-AI 1.4v Doc : https://docs.amd.com/r/1.4.1-English/ug1414-vitis-ai/Setting-Up-the-Host

- DPU-TRD 2021.1v : https://github.com/Xilinx/Vitis-AI/blob/1.4/dsa/DPU-TRD/prj/Vivado/README.md

- DPU-TRD 2021.1v : https://github.com/luunguyen97/DPU-TRD-ZCU104?tab=readme-ov-file

- Version compatibility : https://xilinx.github.io/Vitis-AI/3.5/html/docs/reference/version_compatibility.html

- SD card : https://xilinx-wiki.atlassian.net/wiki/spaces/A/pages/18842385/How+to+format+SD+card+for+SD+boot

- PetaLinux Installation :  https://www.hackster.io/whitney-knitter/vivado-vitis-petalinux-2024-1-install-on-ubuntu-22-04-e76e91

- Docker Installation : https://phoenixnap.com/kb/install-docker-on-ubuntu-20-04

---

Feel free to raise any queries or issues you face during setup, build, or deployment.






