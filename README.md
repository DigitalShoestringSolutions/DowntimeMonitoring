# DowntimeMonitoring

## Install the Shoestring Assembler
In the terminal, run:
- `sudo apt install pipx -y`
- `sudo pipx run shoestring-setup`
- `sudo reboot` if prompted to restart

## Use the Shoestring Assembler to download and configure this Solution
- In the terminal run `shoestring app`, or double click the desktop icon called `Shoestring`.  
- Use the `Download` button to select the name of this solution. Select the latest release tag.  
- Follow the prompts to configure

## Build & Start
Continue accepting the prompts to build and start now

## Usage
This solution has 3 main pages, accessed via a web browser:
- Data capture - Record downtime events and set reasons for each  
  [http://localhost](http://localhost) on the device (i.e. Raspberry Pi) or http://\<ip\> from other devices on the local network (where \<ip\> is the devices fixed IP address) (e.g. http://192.168.0.1 for IP address 192.168.0.1)

- Admin page - Setup Reasons and Machines  
  [http://localhost:8001/admin](http://localhost:8001/admin) on the device or http://\<ip\>:8001/admin from other devices (username `admin`, password is set during solution setup)
 
- Dashboard - View metrics and plots  
  [http://localhost:3000](http://localhost:3000) on the device or http://\<ip\>:3000 from other devices (username: admin, password: admin) [Please change password from default]
