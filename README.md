# DowntimeMonitoring

## Build
Run the `./setup.sh` script  
Build using docker: `docker compose build`

## Run
Run using the `./start.sh` script

## Usage
This solution has 3 main pages:
- Data capture - [http://localhost](http://localhost) on the device (i.e. Raspberry Pi) or http://\<ip\> from other devices on the local network (where \<ip\> is the devices fixed IP address) (e.g. http://192.168.0.1 for IP address 192.168.0.1)

- Admin page - [http://localhost:8001/admin](http://localhost:8001/admin) on the device or http://\<ip\>:8001/admin from other devices (username: admin, password: admin) [Please change password from default]
 
- Dashboard - [http://localhost:3000](http://localhost:3000) on the device or http://\<ip\>:3000 from other devices (username: admin, password: admin) [Please change password from default]
