#!/usr/bin/env bash
sudo apt-get update

sudo apt-get install -y build-essential python3.4-dev python3-pip htop curl vim git mercurial postgresql postgresql-server-dev-9.3

sudo -u postgres psql -c "CREATE ROLE eggplant PASSWORD 'eggplant123' LOGIN CREATEDB;"
sudo -u postgres createdb eggplant eggplant

sudo pip3 install virtualenv

sudo -u vagrant virtualenv -p /usr/bin/python3.4 /home/vagrant/env

# pillow requirements
sudo apt-get -y install libjpeg8 libjpeg62-dev libfreetype6 libfreetype6-dev

sudo su vagrant
source /home/vagrant/env/bin/activate

cp /home/vagrant/eggplant/settings/local.py.example \
   /home/vagrant/eggplant/settings/local.py
pip3 install -r /vagrant/requirements/development.txt

LINE="source /home/vagrant/env/bin/activate; cd /vagrant"
FILE=/home/vagrant/.bashrc
grep -q "$LINE" "$FILE" || echo "$LINE" >> "$FILE"
