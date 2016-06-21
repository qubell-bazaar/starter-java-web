import os
import requests
from qubell.api.globals import DEFAULT_CREDENTIAL_SERVICE, DEFAULT_WORKFLOW_SERVICE

from qubell.api.testing import *
from qubell.api.tools import retry
from qubell.api.private.service import GCE_CLOUD_TYPE, CLOUD_ACCOUNT_TYPE
from testtools import skip

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
    "GCE_test": {
        "policies": [{
            "action": "provisionVms",
            "parameter": "hardwareId",
            "value": "g1-small"
        }, {
            "action": "provisionVms",
            "parameter": "imageId",
            "value": "ubuntu-1204-precise-v20160516"
        }, {
            "action": "provisionVms",
            "parameter": "jcloudsRegions",
            "value": "europe-west1-c"
        }, {
            "action": "provisionVms",
            "parameter": "vmIdentity",
            "value": "ubuntu"
        }]
    }

})
class PetClinicComponentTestCase(BaseComponentTestCase):
    name = "starter-java-web"
    meta = "https://raw.github.com/qubell-bazaar/starter-java-web/gce/meta.yml"
    db_name = "petclinic"
    apps = [{
        "name": name,
        "settings": {"destroyInterval": 7200000},
        "file": os.path.realpath(os.path.join(os.path.dirname(__file__), '../%s.yml' % name))
    }]

    @classmethod
    def environment(cls, organization):
        # todo: if used more move to client
        """
        This is a hack, to replace common cloud account with Amazon Account
        :param organization:
        :return: json with Amazon Account
        """
        cls.provider = os.environ.get('PROVIDER')

        infr = super(BaseComponentTestCase, cls).environment(organization)

        for env in infr["environments"]:
            env["services"] = [{"name": DEFAULT_CREDENTIAL_SERVICE()},
                               {"name": DEFAULT_WORKFLOW_SERVICE()},
                               {"name": cls.provider
                                }
                               ]

        ca = [s for s in infr["services"] if s['type'] == CLOUD_ACCOUNT_TYPE][0]

        ca["type"] = GCE_CLOUD_TYPE
        ca["name"] = cls.provider
        ca['parameters'] = {'configuration.identity': os.environ.get('GCE_PROVIDER_IDENTITY'),
                           'configuration.credential': os.environ.get('GCE_PROVIDER_CREDENTIAL')}

        return infr

    @classmethod
    def timeout(cls):
        return 120

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
        params = {'input.app-quantity': '2',
                  'input.app-branch': instance.parameters['input.app-branch']}
        instance.reconfigure(parameters=params)
        assert instance.ready(timeout=30)

        check_site(instance)
        # Check we have 2 hosts up
        @eventually(AssertionError, KeyError)
        def eventually_assert():
            assert len(instance.returnValues['endpoints.app']) == 2
        eventually_assert()

    @instance(byApplication=name)
    @values({"lb-host": "host"})
    def test_change_branch(self, instance, host):
        params = {'input.app-branch': 'red'}
        instance.reconfigure(parameters=params)
        assert instance.ready(timeout=20)

        check_site(instance)
        resp = requests.get("http://" + host, verify=False)

        assert 'Updated PetClinic :: a Spring Framework demonstration' in resp.text
