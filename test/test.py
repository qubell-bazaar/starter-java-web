import os

import requests
from qubell.api.private.testing import environment, instance, values
from qubell.api.tools import retry
from testtools import skip



from test_runner import BaseComponentTestCase

def eventually(*exceptions):
    """
    Method decorator, that waits when something inside eventually happens
    Note: 'sum([delay*backoff**i for i in range(tries)])' ~= 580 seconds ~= 10 minutes
    :param exceptions: same as except parameter, if not specified, valid return indicated success
    :return:
    """
    return retry(tries=50, delay=0.5, backoff=1.1, retry_exception=exceptions)

def check_site(instance):
    # Check we have 2 hosts up
    @eventually(AssertionError, KeyError)
    def eventually_assert():
        assert len(instance.returnValues['endpoints.entry'])
    eventually_assert()

    # Check site still alive
    url = instance.returnValues['endpoints.entry']
    resp = requests.get(url)
    assert resp.status_code == 200
    assert 'PetClinic :: a Spring Framework demonstration' in resp.text

@environment({
    "default": {},
    "AmazonEC2_CentOS_63": {
        "policies": [{
            "action": "provisionVms",
            "parameter": "imageId",
            "value": "us-east-1/ami-eb6b0182"
        }, {
            "action": "provisionVms",
            "parameter": "vmIdentity",
            "value": "root"
        }]
    },
    "AmazonEC2_CentOS_53": {
        "policies": [{
            "action": "provisionVms",
            "parameter": "imageId",
            "value": "us-east-1/ami-beda31d7"
        }, {
            "action": "provisionVms",
            "parameter": "vmIdentity",
            "value": "root"
        }]
    },
    "AmazonEC2_Ubuntu_1204": {
        "policies": [{
            "action": "provisionVms",
            "parameter": "imageId",
            "value": "us-east-1/ami-d0f89fb9"
        }, {
            "action": "provisionVms",
            "parameter": "vmIdentity",
            "value": "ubuntu"
        }]
    },
    "AmazonEC2_Ubuntu_1004": {
        "policies": [{
            "action": "provisionVms",
            "parameter": "imageId",
            "value": "us-east-1/ami-0fac7566"
        }, {
            "action": "provisionVms",
            "parameter": "vmIdentity",
            "value": "ubuntu"
        }]
    }
})
class PetClinicComponentTestCase(BaseComponentTestCase):
    name = "starter-java-web"
    apps = [{
        "name": name,
        "settings": {"destroyInterval": 7200000},
        "file": os.path.realpath(os.path.join(os.path.dirname(__file__), '../%s.yml' % name))
    }, {
        "name": "Database",
        "url": "https://raw.github.com/qubell-bazaar/component-mysql-dev/master/component-mysql-dev.yml",
        "launch": False
    }, {
        "name": "Load Balancer",
        "url": "https://raw.github.com/qubell-bazaar/component-haproxy/master/component-haproxy.yml",
        "launch": False
    }, {
        "name": "Application Server",
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

    @instance(byApplication=name)
    def test_petclinic_up(self, instance):
        check_site(instance)

    @instance(byApplication=name)
    def test_scaling(self, instance):
        assert len(instance.returnValues['endpoints.app']) == 1
        params = {'input.app-quantity': '2'}
        instance.reconfigure(parameters=params)
        assert instance.ready(timeout=30)

        check_site(instance)
        # Check we have 2 hosts up
        @eventually(AssertionError, KeyError)
        def eventually_assert():
            assert len(instance.returnValues['endpoints.app']) == 2
        eventually_assert()

    @skip('Until https://github.com/qubell/starter-java-web/pull/7 applied')
    def test_change_branch(self, instance):
        params = {'input.app-branch': 'red'}
        instance.reconfigure(parameters=params)
        assert instance.ready(timeout=20)

        check_site()
        resp = requests.get(self.url)

        assert 'Updated PetClinic :: a Spring Framework demonstration' in resp.text
