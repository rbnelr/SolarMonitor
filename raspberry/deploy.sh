#!/bin/bash

# Intially created to deploy just measure.py from my pc to my raspberry pi
# But later could act as the entire installation script

# Exit on error
set -e
set -x

echo "Installing/Updating Solarmon..."

# TODO: create databse here?

# Check if we're in the right directory
if [[ ! -f "measure.py" ]]; then
    echo "Error: measure.py not found. Please run this script from the raspberry directory."
    exit 1
fi

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    sudo apt-get install -y git
fi

# Check if python3 and pip are installed
if ! command -v python3 &> /dev/null; then
    echo "Installing python3 and pip..."
    sudo apt-get install -y python3 python3-pip
fi

# sudo apt install python3-virtualenv

echo "Pulling latest changes from git..."
git pull

cp database.template.env database.env

# Create virtual environment if it doesn't exist
if [[ ! -d "venv" ]]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install or update Python dependencies
echo "Installing/updating Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if systemd is available
echo "Setting up systemd service..."

# Modify service file to use the virtual environment python
VENV_PATH=$(pwd)/venv
sed "s|ExecStart=/usr/bin/python3|ExecStart=$VENV_PATH/bin/python|" solarmon.measure.service > solarmon.measure.service.tmp
sudo mv solarmon.measure.service.tmp /etc/systemd/system/solarmon.measure.service

# Set correct permissions
sudo chmod 644 /etc/systemd/system/solarmon.measure.service

# Reload systemd to recognize changes
sudo systemctl daemon-reload

# Enable and restart the service
echo "Enabling and starting the service..."
sudo systemctl enable solarmon.measure
sudo systemctl restart solarmon.measure

# Show status
echo "Service status:"
#sudo systemctl status solarmon.measure #uhm this locks the console into this mode

echo "done." 