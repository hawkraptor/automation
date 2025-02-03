#!/bin/bash

cd ~/Downloads/
echo "Downloading update for Discord, please wait..."

# Download the .deb file
curl -s -L -f --no-keepalive --http1.0 --max-time 60 -o discordupdate.deb "https://discord.com/api/download/stable?platform=linux&format=deb"

echo "File has been downloaded, installing now. You may be prompted for your account or sudo password if you did not run this as root"

# Check if the script is running as root
if [ "$(id -u)" -eq 0 ]; then

    apt install ./discordupdate.deb -y
else
    
    sudo apt install ./discordupdate.deb -y
fi

echo "Upgrade complete! Deleting downloaded file."
rm -f ./discordupdate.deb
echo "Downloaded file has been removed."
