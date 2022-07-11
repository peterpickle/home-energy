#!/bin/bash
#install services script
#execute this script from it's own directory

function get_absolute_path {
    ABS_PATH=$(realpath -e $1)
    if [ $? -ne 0 ]; then
        echo "Could not get the absolute path for $1"
        exit
    fi
}

function set_absolute_path_in_file {
    #check if script file exists
    if [ ! -f $1 ]; then
        echo "$1 does not exists."
        exit
    fi

    #check if service file exists
    if [ ! -f $2 ]; then
        echo "$2 does not exists."
        exit
    fi

    get_absolute_path $1

    sed -i "s! .*$1! $ABS_PATH!g" $2
}

#install service p1-reader
set_absolute_path_in_file p1-reader.py p1-reader.service
sudo cp p1-reader.service /lib/systemd/system/
sudo chmod 644 /lib/systemd/system/p1-reader.service
sudo systemctl daemon-reload
sudo systemctl enable p1-reader.service
sudo systemctl start p1-reader.service

#TODO: check feature flag prodcution

#install service production-reader
set_absolute_path_in_file production-reader.py production-reader.service
sudo cp production-reader.service /lib/systemd/system/
sudo chmod 644 /lib/systemd/system/production-reader.service
sudo systemctl daemon-reload
sudo systemctl enable production-reader.service
sudo systemctl start production-reader.service

#check service
#sudo systemctl status p1-reader.service
#sudo systemctl status production-reader.service

#follow service logs
#sudo journalctl -f -u p1-reader.service
#sudo journalctl -f -u production-reader.service
