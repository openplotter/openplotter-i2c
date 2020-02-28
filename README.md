## openplotter-i2c

OpenPlotter app to manage I2C sensors in Raspberry Pi

### Installing

#### For production

Install [openplotter-settings](https://github.com/openplotter/openplotter-settings) for **production** and just install this app from *OpenPlotter Apps* tab.

#### For development

Install [openplotter-settings](https://github.com/openplotter/openplotter-settings) for **development**.

Install openplotter-i2c dependencies:

`sudo apt install i2c-tools`

Make your changes and create the package:

```
cd openplotter-i2c
dpkg-buildpackage -b
```

Install the package:

```
cd ..
sudo dpkg -i openplotter-i2c_x.x.x-xxx_all.deb
```

Run post-installation script:

`sudo i2cPostInstall`

Run:

`openplotter-i2c`

Make your changes and repeat package, installation and post-installation steps to test. Pull request your changes to github and we will check and add them to the next version of the [Debian package](https://launchpad.net/~openplotter/+archive/ubuntu/openplotter).

### Documentation

https://openplotter.readthedocs.io

### Support

http://forum.openmarine.net/forumdisplay.php?fid=1
