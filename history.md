passwd
git clone https://github.com/matteoferla/Raspberry-Pi-irrigator.git irrigator
wget https://github.com/jjhelmus/berryconda/releases/download/v2.0.0/Berryconda3-2.0.0-Linux-armv7l.sh
bash Berryconda3-2.0.0-Linux-armv7l.sh
rm Berryconda3-2.0.0-Linux-armv7l.sh
exit

conda update --all
conda install -y scipy
conda install -y opencv
sudo apt-get install libgpiod2
cd irrigator/
which pip
pip install -r requirements.txt 
sudo raspi-config

