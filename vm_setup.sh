#!/bin/bash

cd

echo "Updating and upgrading Ubuntu OS"
sudo apt-get update -y && sudo apt-get upgrade -y

# echo "Step 2: Moving all the folder in the right places"
# cp -r ~/projectArrow/containernet/ ~/.
# cp -r ~/projectArrow/vim-emu/ ~/.
# cp ~/projectArrow/proj_setup/demo_topo.py ~/.

## Moving the folder into right directories
# mv ~/projectArrow/containernet/ ~/.
# mv ~/projectArrow/vim-emu/ ~/.
# mv ~/projectArrow/proj_setup/demo_topo.py ~/.

## Moving required folder back to project folder
# mv ~/containernet/ ~/projectArrow/.
# mv ~/vim-emu/ ~/projectArrow/.
# mv ~/demo_topo.py ~/projectArrow/proj_setup/
echo "Installing Chrome"
if [ $(dpkg-query -W -f='${Status}' google-chrome-stable 2>/dev/null | grep -c "ok installed") -eq 0 ];
then
  wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
  sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
  sudo apt-get -y update
  sudo apt-get -y install google-chrome-stable
else
  echo "Chrome Already Installed"
fi

echo "Installing atom"
if [ $(dpkg-query -W -f='${Status}' atom 2>/dev/null | grep -c "ok installed") -eq 0 ];
then
  sudo add-apt-repository ppa:webupd8team/atom
  sudo apt-get -y update
  sudo apt-get -y install atom
  sudo atom .
else
  sudo atom .
  echo "Atom Already Installed"
fi

echo "Installing Postman"
if [ -x /opt/Postman/Postman ]
then
  echo "Postman Already Installed"
else
  wget https://dl.pstmn.io/download/latest/linux64 -O postman.tar.gz
  sudo tar -xzf postman.tar.gz -C /opt
  rm postman.tar.gz
  sudo ln -s /opt/Postman/Postman /usr/bin/postman
  cat > ~/.local/share/applications/postman.desktop <<EOL
[Desktop Entry]
Encoding=UTF-8
Name=Postman
Exec=postman
Icon=/opt/Postman/resources/app/assets/icon.png
Terminal=false
Type=Application
Categories=Development;
EOL
fi

cd
echo "Installing Wireshark"
if [ $(dpkg-query -W -f='${Status}' wireshark 2>/dev/null | grep -c "ok installed") -eq 0 ];
then
  sudo add-apt-repository ppa:wireshark-dev/stable
  sudo apt-get update
  sudo apt-get install wireshark
  sudo usermod -a -G wireshark $(whoami)
  # sudo wireshark &
else
  # sudo wireshark &
  echo "wireshark Already Installed"
fi

cd
#./projectArrow/proj_setup/vimemu-aro-install.sh

