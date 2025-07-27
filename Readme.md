# Lecture port série UART pour récupération des données TIC

# Installation

## config Raspberry
### synchronisation de l'heure

`sudo nano -c /etc/systemd/timesyncd.conf`

Ajouter/modifer la ligne suivante :

```bash
Servers=ntp.crashdump.fr 0.pool.ntp.org 1.pool.ntp.org 2.pool.ntp.org 3.pool.ntp.org
```
Vérifier la bonne synchronisation
```
timedatectl
```
Redémarrer le service 

```
sudo service systemd-timesyncd restart
sudo service systemd-timesyncd status
```
### Installation du client MQTT

```bash
sudo apt install -y mosquitto-clients
```

Tester un envoi :
```bash
mosquitto_pub -u userxx -P xxx -t "home/power/data" -m 'test depuis rasp' -h 192.168.x.xx -p 1883 -q 1
```

### Python


#### Installation
```
sudo apt install python3-pip
```
Création du dossier avec `cd ~ && mkdir uart_to_mqtt && cd uart_to_mqtt/`

Activation de l'environnment virtuel
```bash
python3 -m venv venv
source venv/bin/activate
```

Installation de ```paho-mqtt pyserial```
```bash
pip install paho-mqtt<2 pyserial
```

Ajout du user `pi` au groupe `dialout`

```bash
sudo usermod -aG dialout pi
reboot
```

Excéution du script 
```
python3 uart_to_mqtt.py
```
### Configuration du port série
```  
sudo raspi-config
```

Interface Options → Serial Port

- Login shell ? → No

- Activer port matériel ? → Yes

Redémarrer ensuite le Pi.

Identifier le bon port :

`ls -l /dev/serial*`

Le port est généralement `/dev/serial0`

#### Installation de `minicom`
```bash
sudo apt install minicom
```

Vérifier les trames du port série (le port TIC doit être connecté au Raspberry):

```bash
minicom -b 1200 -o -D /dev/serial0 -7 -pE
```

Pour configurer le port série :

```bash
sudo minicom -s
```

- Appuyer sur A : choisir le port série (/dev/serial0 ou /dev/ttyAMA0 selon ton Pi)
- Appuyer sur E : configure les paramètres :

- Choisir : 7E1 → c’est-à-dire : 7 bits de données
- Parité paire (Even)
- 1 bit de stop

Appuyer sur F : désactiver hardware flow control

Appuyer sur G : désactiver software flow control

#### Désactivation du bluetooth

```bash 
sudo nano /boot/firmware/config.txt
```
Entrer : 
```
[all]
enable_uart=1
dtoverlay=disable-bt
```
Puis `sudo reboot`

Enfin vérifier à nouveau : `ls -l /dev/serial*`, on devrait avoir : 

```bash
/dev/serial0 -> ttyAMA0
```

### Installation d'un service
```bash
sudo nano /etc/systemd/system/uartmqtt.service
```
Créer le service (paramétré pour utiliser le venv de python)
```bash
[Unit]
Description=Script UART vers MQTT
After=network.target

[Service]
ExecStart=/home/pi/Program/uart_to_mqtt/venv/bin/python3 /home/pi/Program/uart_to_mqtt/uart_to_mqtt.py
WorkingDirectory=/home/pi/Program/uart_to_mqtt
StandardOutput=append:/var/log/uartmqtt.log
StandardError=append:/var/log/uartmqtt.err
Restart=always
User=pi
Environment="PATH=/home/pi/Program/uart_to_mqtt/venv/bin"

[Install]
WantedBy=multi-user.target
```

Puis lancer le service 
```
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable uartmqtt.service
sudo systemctl start uartmqtt.service
```
Vérifier le status du service :
```
systemctl status uartmqtt.service
```
## Mails d'alerte 

### installation 
sudo apt update
sudo apt install msmtp msmtp-mta bsd-mailx

### configuration

Editer le fichier de configuration  `nano ~/.msmtprc`

```shell
defaults
auth           on
tls            on
tls_starttls   off
tls_trust_file /etc/ssl/certs/ca-certificates.crt
logfile        ~/.msmtp.log

account        gmail
host           smtp.gmail.com
port           587
from           ton.adresse@gmail.com
user           ton.adresse@gmail.com
password       mot_de_passe_ou_mot_de_passe_application

account default : gmail
```

Sécuriser le fichier `chmod 600 ~/.msmtprc`

Tester le fonctionnement  du mail 
```
echo "Le service uartmqtt est tombé !" | mailx -s "ALERTE : Service KO" dest@example.com
```

Mettre en place un cron : `nano /home/pi/check_uart.sh` :

```bash
#!/bin/bash

if ! systemctl is-active --quiet uartmqtt.service; then
    echo "Le service uartmqtt est tombé à $(date)" | mailx -s "🛑 ALERTE - uartmqtt KO" you@example.com
fi

crontab -e

*/5 * * * * /home/pi/check_uart.sh
```