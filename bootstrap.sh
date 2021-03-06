# Initialize an empty digitalocean droplet

# Login and change password
ssh root@46.101.234.224

# Add a new user "max" and give him a password
adduser max
# Give "max" rights
gpasswd -a max sudo

# Change "PermitRootLogin yes" to "PermitRootLogin no"
nano /etc/ssh/sshd_config

# Restart SSH
service ssh restart

# Switch to user "max"
su max

# Configure the timezone
dpkg-reconfigure tzdata
# Configure NTP Synchronization
apt-get update
apt-get install ntp
# Create a Swap File
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
sh -c 'echo "/swapfile none swap sw 0 0" >> /etc/fstab'

# Setup Python and Apache
apt-get update
apt-get install apache2
apt-get install python3-pip python3-dev libapache2-mod-wsgi-py3

# Clone the repository containing the code
cd /var/www
apt-get install git
git clone https://github.com/OpenBikes/api.openbikes.co
chmod -R 777 api.openbikes.co/
cd api.openbikes.co

# Install the MongoDB C driver
git clone https://github.com/mongodb/mongo-c-driver.git
cd mongo-c-driver
git checkout
./autogen.sh --with-libbson=bundled
make
make install

# Install the necessary Python libraries (takes some time)
apt-get install libblas-dev liblapack-dev libatlas-base-dev gfortran
apt-get install python3-lxml
pip3 install -r requirements.txt

# Add the cities
./scripts/add-cities.sh

# Add tasks to the crontab file
cat scripts/etc/crontab >> /var/spool/cron/crontabs/max

# Configure and enable a virtual host
cp setup/scripts/etc/apache2/sites-available/OpenBikes.conf /etc/apache2/sites-available/
a2ensite OpenBikes
service apache2 reload
service apache2 restart

# Reboot the server and you should be done!
