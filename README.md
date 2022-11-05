## openplotter-i2c

OpenPlotter app to manage I2C sensors in Raspberry Pi

### Installing

Install [openplotter-settings](https://github.com/openplotter/openplotter-settings) for **production**.

#### For production

Install I2C from openplotter-settings app.

#### For development

Install openplotter-i2c dependencies:

`sudo apt install i2c-i2c-tools python3-rpi.gpio`

Clone the repository:

`git clone https://github.com/openplotter/openplotter-i2c`

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

Pull request your changes to github and we will check and add them to the next version of the [Debian package](https://cloudsmith.io/~openplotter/repos/openplotter/packages/).

### Documentation

https://openplotter.readthedocs.io

### Support

http://forum.openmarine.net/forumdisplay.php?fid=1