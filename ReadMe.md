# SSH Tunnel Proxy

A TCP proxy for yum，pip or wget on ssh tunnel portfowarding

## Features

- a simple http(s) proxy
- show request logs
- auto set yum/wget config file，

## Todo

- file transfer
- set pip config file
- backup/restore yum/wget config file

## Usage

1. Edit the server login and bastion login（if needed）

    ```python
        server = ['192.168.1.22', 22]  # server ip/port
        login = ['root', 'Passw0rd'] # login user/password
        bastion = ['1.1.1.1', 22, 'root', '1'] # bastion login
    ```

2. run main.py

> python main.py

## Requirement

1. paramiko

> pip install paramiko
