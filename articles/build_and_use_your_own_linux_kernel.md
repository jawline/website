!=!=! Uuid: f692dae2-519e-4fa1-bab7-14af60ccbd31
!=!=! Title: How to build and use a custom Linux kernel
!=!=! Created: 09-12-2020
!=!=! Tags: Projects

!=!=! Intro: Start
In this short article we cover how to clone a copy of the Linux source code and how to install alongside your distribution default.
!=!=! Intro: End

# TLDR;

```
apt-get install git build-essential
git clone https://github.com/torvalds/linux.git
cd linux
git checkout v5.9
make old_config
sudo make install
sudo make headers_install
INSTALL_MOD_STRIP=1 sudo make modules_install
sudo update-grub
```

# Explained

Occasionally it is necessary to use a Linux kernel different from the pre-built binary provided with your Linux distribution. Typically this is because you need access to new drivers or features, but can also occur when you need to manually apply a patch that hasn't made it in to the Linux source code. In many of these situations there are faster ways of getting newer versions of the kernel, like third party pre-build kernels, but occasionally it is necessary to build it yourself.

#### Getting the kernel source code

To begin we must fetch a copy of the Linux source. Luckily, the code is now mirrored on many public git repositories, so we can download an up-to-date version with the following command:
```
git clone https://github.com/torvalds/linux.git
cd linux
```

The version we have just downloaded is the current master branch, but master is not likely to be stable on all hardware, so we should check out a tagged version release. To check out version 5.9 we can run the following command:
```
git checkout v5.9
```

#### Building the kernel

Now that we have a stable version of the kernel source code checked out we need to create a kernel configuration, a file that specifies which components will be included directly in the kernel, unsupported, or added as an kernel module file. We can base a kernel configuration off of our current kernel, specifying only which of the new features added between our current kernel and the downloaded one we want, with the following command:
```
make old_config
```
You will be provided with a list of components to include, added as a module, or ignore while building. Here a 'y' specifies inclusion directly in the kernel, an 'm' specifies inclusion as a kernel module, and 'n' specifies no support. If you aren't sure whether you need a specified feature you will probably be fine with the suggested default.

#### Installing the kernel

With our configuration created we now need to build the kernel. To do this we run `make` and wait for the kernel to build. After our kernel is built we need to install it. To do that we run the following three commands:
```
sudo make install
sudo make headers_install
INSTALL_MOD_STRIP=1 sudo make modules_install
```

The first command installs the kernel itself into our boot directory. The second installs the kernel headers, so that programs we compile on this machine can reference them. The final command installs the kernel modules we built alongside our kernel and then prepares an initrd, a small disk image that is loaded as a read only filesystem early on during the computer boot process and before it has loaded filesystem drivers. We specify `INSTALL_MOD_STRIP=1` to strip metadata from the compiled modules, leaving only the necessary code. This step is optional, but in many distributions the `/boot` partition is created with a small amount of space available, and unstripped kernel modules will not fit.

#### Updating the bootloader

The final step is to update our bootloader, so that it knows about the new kernel. This step depends on the bootloader your distribution uses, but in most cases it is as simple as `sudo update-grub`. The kernel is now ready to use, so reboot and, if prompted, select it during boot. Once you have rebooted you can test that you are using the new version by running the command `uname -r`, which should echo back the kernel version you just compiled and installed.
