import logging
import sys
import threading
import paramiko
from rforward import reverse_forward_tunnel
from proxy import HTTP, logger


def set_connection():
    port = 10888
    server = ['10.152.105.137', 22]
    remote = ['127.0.0.1', 8080]
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.WarningPolicy())

    print("Connecting to ssh host %s:%d ..." % (server[0], server[1]))
    try:
        client.connect(
            server[0],
            server[1],
            username='root',
            # key_filename=options.keyfile,
            # look_for_keys=options.look_for_keys,
            password='nsfocus',
        )
    except Exception as e:
        print("*** Failed to connect to %s:%d: %r" % (server[0], server[1], e))
        sys.exit(1)

    print(
        "Now forwarding remote port %d to %s:%d ..."
        % (port, remote[0], remote[1])
    )

    setup_yum_proxy(client, port)

    # try:
    #     reverse_forward_tunnel(
    #         port, remote[0], remote[1], client.get_transport()
    #     )
    # except KeyboardInterrupt:
    #     print("C-c: Port forwarding stopped.")
    #     sys.exit(0)


def setup_yum_proxy(client, port):
    stdin, stdout, stderr = client.exec_command('grep proxy= /etc/yum.conf')
    if len(stderr.readlines())> 0:
        print("ERROR execute grep ")
    else:
        result = stdout.readlines()
        if len(result) == 1 and 'proxy=' in result[0]:
            stdin, stdout, stderr = client.exec_command("sed -i 's/^proxy=.*$/proxy=http:\/\/localhost:10888\//g' /etc/yum.conf")
            print(stderr.readlines())
        else:
            stdin, stdout, stderr = client.exec_command('echo "proxy=http://localhost:10888/" >> /etc/yum.conf')
            print(stderr.readlines())


def setup_proxy():
    try:
        logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'),

        proxy = HTTP(hostname='127.0.0.1',
                     port=int(8080),
                     backlog=int(100),
                     auth_code=None,
                     server_recvbuf_size=int(8192),
                     client_recvbuf_size=int(8192),
                     pac_file='')
        proxy.run()
    except KeyboardInterrupt:
        print("KeyboardInterrupt Exit")



if __name__ == '__main__':
    # thr = threading.Thread(
    #     target=setup_proxy, args=()
    # )
    # thr.setDaemon(True)
    # thr.start()
    set_connection()
