passwd
git clone https://github.com/matteoferla/Raspberry-Pi-irrigator.git irrigator
wget https://github.com/jjhelmus/berryconda/releases/download/v2.0.0/Berryconda3-2.0.0-Linux-armv7l.sh
bash Berryconda3-2.0.0-Linux-armv7l.sh
rm Berryconda3-2.0.0-Linux-armv7l.sh
exit

conda update --all
conda install -y scipy
conda install -y opencv
conda install -y jupyter
sudo apt-get install libgpiod2
cd irrigator
which pip
pip install -r requirements.txt 
sudo raspi-config # camera and spi
sudo shutdown -r now

cd irrigator
# trialling...
python app.py
# then...
nohup /home/pi/berryconda3/bin/python app.py &
# eventually...
sudo cp irrigator.service /etc/systemd/system/irrigator.service
sudo systemctl start irrigator.service
sudo systemctl enable irrigator.service

