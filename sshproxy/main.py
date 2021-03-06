import logging
import sys
import threading
import paramiko
from rforward import reverse_forward_tunnel
from proxy import HTTP, logger


def set_connection(http_proxy_port):
    server = ['172.20.243.133', 22]  # server ip and port
    login = ['root', 'linux123!@#'] # login user and password
    bastion = ['172.20.243.132', 22, 'root', 'linux123!@#'] # bastion login

    bastion_channel = build_jump(bastion, server[0], server[1])

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    proxy_port = 10888
    try:
        print("Connecting to ssh host %s:%d ..." % (server[0], server[1]))
        client.connect(
            server[0],
            server[1],
            username=login[0],
            password=login[1],
            sock=bastion_channel,
        )
    except Exception as e:
        print("*** Failed to connect to %s:%d: %r" % (server[0], server[1], e))
        sys.exit(1)

    setup_yum_proxy(client, proxy_port)
    setup_wget_proxy(client, proxy_port)

    try:
        remote = ['127.0.0.1', http_proxy_port]
        print(
            "Now forwarding remote port %d to %s:%d ..." % (
                proxy_port, remote[0], remote[1])
        )
        reverse_forward_tunnel(
            proxy_port, remote[0], remote[1], client.get_transport()
        )
    except KeyboardInterrupt:
        print("C-c: Port forwarding stopped.")
        sys.exit(0)


def build_jump(bastion, des_server, des_port):
    bastion_client = paramiko.SSHClient()
    bastion_client.load_system_host_keys()
    bastion_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print("*** connecting to bastion %s:%d: %r" %
              (bastion[0], bastion[1], 1))
        bastion_client.connect(
            bastion[0],
            bastion[1],
            username=bastion[2],
            password=bastion[3],
        )
        bastion_transport = bastion_client.get_transport()
        dest_addr = (des_server, des_port)
        src_addr = ('localhost', 22)
        jumpbox_channel = bastion_transport.open_channel(
            "direct-tcpip", dest_addr, src_addr)
        return jumpbox_channel
    except Exception as e:
        print("*** Failed to connect to bastion %s:%d: %r" %
              (bastion[0], bastion[1], e))
        return None


def setup_yum_proxy(client, port):
    stdin, stdout, stderr = client.exec_command('grep proxy= /etc/yum.conf')
    if len(stderr.readlines()) > 0:
        print("ERROR execute grep ")
    else:
        result = stdout.readlines()
        if len(result) == 1 and 'proxy=' in result[0]:
            stdin, stdout, stderr = client.exec_command(
                "sed -i 's/^proxy=.*$/proxy=http:\/\/localhost:10888\//g' /etc/yum.conf")
            print(stderr.readlines())
        else:
            stdin, stdout, stderr = client.exec_command(
                'echo "proxy=http://localhost:10888/" >> /etc/yum.conf')
            print(stderr.readlines())


def setup_wget_proxy(client, port):
    stdin, stdout, stderr = client.exec_command(
        "sed -i 's/^#\?http_proxy = .*$/http_proxy = http:\/\/localhost:10888\//g' /etc/wgetrc")
    if len(stderr.readlines()) > 0:
        print("ERROR set wget proxy ")
    stdin, stdout, stderr = client.exec_command(
        "sed -i 's/^#\?https_proxy = .*$/https_proxy = http:\/\/localhost:10888\//g' /etc/wgetrc")


def setup_proxy(http_proxy_port):
    try:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'),

        proxy = HTTP(hostname='127.0.0.1',
                     port=int(http_proxy_port),
                     backlog=int(100),
                     auth_code=None,
                     server_recvbuf_size=int(8192),
                     client_recvbuf_size=int(8192),
                     pac_file='')
        proxy.run()
    except KeyboardInterrupt:
        print("KeyboardInterrupt Exit")


if __name__ == '__main__':
    local_port = 8080
    thr = threading.Thread(
        target=setup_proxy, args=([local_port])
    )
    thr.setDaemon(True)
    thr.start()
    set_connection(local_port)
