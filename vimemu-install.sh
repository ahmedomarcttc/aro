#!/bin/bash

cd

echo "Updating and upgrading Ubuntu OS"
sudo apt-get update -y && sudo apt-get upgrade -y

echo "Installing ansible and aptitude"
sudo apt-get install -y ansible git aptitude

echo "Installing Containernet"
# cd
git clone https://github.com/ahmedomarcttc/containernet.git
# cp -r ~/projectArrow/containernet/ ~/.
cd ~/containernet/ansible
sudo ansible-playbook -i "localhost," -c local install.yml
cd
sudo cp -r /usr/local/lib/python2.7/dist-packages/backports/ssl_match_hostname/ /usr/lib/python2.7/dist-packages/backports
sudo apt-get install -y mininet

echo "Installing the emulator"
# cd
git clone https://osm.etsi.org/gerrit/osm/vim-emu.git
# cp -r ~/projectArrow/vim-emu/ ~/.
cd ~/vim-emu/ansible
sudo ansible-playbook -i "localhost," -c local install.yml
cd ..
#cd /home/$(whoami)/vim-emu
sudo python setup.py install
sudo python setup.py develop

echo "Running Emulator unit tests to validate installation"
sudo py.test -v src/emuvim/test/unittests

echo "Run demo topology"
cd
# cp ~/projectArrow/proj_setup/demo_topo.py ~/.
sudo python demo_topo.py
