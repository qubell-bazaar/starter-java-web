import os
import requests

from qubell.api.testing import *
from qubell.api.tools import retry
from testtools import skip

def eventually(exceptions=(AssertionError, KeyError), tries=50 ):
    """
    Method decorator, that waits when something inside eventually happens
    Note: 'sum([delay*backoff**i for i in range(tries)])' ~= 580 seconds ~= 10 minutes
    :param exceptions: same as except parameter, if not specified, valid return indicated success
    :return:
    """
    return retry(tries=tries, delay=0.5, backoff=1.1, retry_exception=exceptions)

def check_site(instance):
    # Check we have 2 hosts up
    @eventually()
    def eventually_assert():
        assert len(instance.returnValues['petclinic.entry-url'])
    eventually_assert()

    # Check site still alive
   
    url = instance.returnValues['petclinic.entry-url'][0]
    resp = requests.get(url)
    assert resp.status_code == 200
    assert 'PetClinic :: a Spring Framework demonstration' in resp.text

@environment({
    "default": {}
})
class PetClinicComponentTestCase(BaseComponentTestCase):
    name = "starter-java-web"
    meta = os.path.realpath(os.path.join(os.path.dirname(__file__), '../meta.yml'))  
    destroy_interval = int(os.environ.get('DESTROY_INTERVAL', 1000*60*60*2))
    db_name = "petclinic"
    apps = [{
        "name": name,
        "settings": {"destroyInterval": destroy_interval},
        "file": os.path.realpath(os.path.join(os.path.dirname(__file__), '../%s.yml' % name))
   }]
    @classmethod
    def timeout(cls):
        return 120
 
    @instance(byApplication=name)
    def test_host(self, instance):
        host = instance.returnValues['petclinic.entry-url'][0]
        resp = requests.get(host, verify=False)

        assert resp.status_code == 200

    @instance(byApplication=name)
    def test_db_port(self, instance):
        import socket
        host = instance.returnValues['petclinic.dbms']['db-host']
        port = instance.returnValues['petclinic.dbms']['db-port']
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))

        assert result == 0

    @instance(byApplication=name)
    def test_petclinic_up(self, instance):
        check_site(instance)

    @instance(byApplication=name)
    def test_scaling(self, instance):
        assert len(instance.returnValues['petclinic.app-hosts']) == 1
        params = {'configuration.clusterSize': '2',
                 'configuration.scm-branch': instance.parameters['configuration.scm-branch']}
        instance.reconfigure(parameters=params)
        assert instance.ready(timeout=30)

        check_site(instance)
        # Check we have 2 hosts up
        @eventually()
        def eventually_assert():
            assert len(instance.returnValues['petclinic.app-hosts']) == 2
        eventually_assert()

    @instance(byApplication=name)
    def test_change_branch(self, instance):
        params = {'configuration.scm-branch': 'red'}
        sub = instance.submodules['BuildServer']
        oldvalue = sub.returnValues['build-result.war_urls']
        print "Old value %s" % oldvalue[0]
        instance.reconfigure(parameters=params)
        @eventually(tries=3000)
        def eventually_assert():
            print "New value %s" % sub.returnValues['build-result.war_urls'][0]
            assert sub.returnValues['build-result.war_urls'][0] != oldvalue[0]
        eventually_assert()
        assert instance.ready(timeout=30)
        host = instance.returnValues['petclinic.entry-url'][0]
        check_site(instance)
        @eventually(AssertionError, KeyError)
        def eventually_assert():
            resp = requests.get(host, verify=False)
            assert 'Updated PetClinic :: a Spring Framework demonstration' in resp.text
        eventually_assert()
