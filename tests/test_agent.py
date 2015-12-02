import pytest
import boto3
import moto
from zmon_agent import agent


#
# The following block is required for Python2 compatibility with
# HTTPretty which is used by moto, for details see:
#
#   https://github.com/spulec/moto/issues/474
#
try:
    from botocore.vendored.requests.packages.urllib3 import connection

    def fake_ssl_wrap_socket(sock, *args, **kwargs):
      return sock
      connection.ssl_wrap_socket = fake_ssl_wrap_socket
except ImportError:
    pass


class TestAgent:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.region = 'eu-west-1'
        self.acc = 'aws:1234567890'

    @moto.mock_ec2
    def test_get_running_apps(self):
        apps = agent.get_running_apps(self.region)

    @moto.mock_elb
    def test_get_running_elbs(self):
        elbs = agent.get_running_elbs(self.region, self.acc)

    @moto.mock_autoscaling
    def test_get_auto_scaling_groups(self):
        groups = agent.get_auto_scaling_groups(self.region, self.acc)

    #@moto.mock_???
#    def test_get_elasticache_nodes(self):
#        elc = agent.get_elasticache_nodes(self.region, self.acc)

    @moto.mock_dynamodb
    def test_get_dynamodb_tables(self):
        tables = agent.get_dynamodb_tables(self.region, self.acc)

    @moto.mock_rds
    def test_get_rds_instances(self):
        rds = agent.get_rds_instances(self.region, self.acc)
