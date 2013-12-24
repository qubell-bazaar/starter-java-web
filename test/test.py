import os
import pymysql
import requests

from test_runner import BaseComponentTestCase
from qubell.api.private.testing import instance, workflow, values


class PetClinicComponentTestCase(BaseComponentTestCase):
    name = "component-petclinic"
    apps = [{
        "name": name,
        "file": os.path.realpath(os.path.join(os.path.dirname(__file__), '../%s.yml' % name))
    }, {
        "name": "db",
        "url": "https://raw.github.com/qubell-bazaar/component-mysql-dev/master/component-mysql-dev.yml",
        "launch": False
    }, {
        "name": "lb",
        "url": "https://raw.github.com/qubell-bazaar/component-haproxy/master/component-haproxy.yml",
        "launch": False
    }, {
        "name": "app",
        "url": "https://raw.github.com/qubell-bazaar/component-tomcat-dev/master/component-tomcat-dev.yml",
        "launch": False
    }]

    db_name = "petclinic"

    @instance(byApplication=name)
    @values({"lb-host": "host"})
    def test_host(self, instance, host):
        resp = requests.get("http://" + host, verify=False)

        assert resp.status_code == 200

    @instance(byApplication=name)
    @values({"db-port": "port", "db-host": "host"})
    def test_db_port(self, instance, host, port):
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))

        assert result == 0