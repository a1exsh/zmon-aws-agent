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

#
# Uncomment this to get some detailed info about test failure:
#
#import logging
#boto3.set_stream_logger(name='botocore', level=logging.DEBUG)


@moto.mock_ec2
class TestAgent:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.region = 'eu-west-1'
        self.acc = 'aws:1234567890'

    def test_get_running_apps(self):
        apps = agent.get_running_apps(self.region)

    @moto.mock_elb
    def test_get_running_elbs(self):
        elb = boto3.client('elb', region_name=self.region)
        elb.create_load_balancer(
            LoadBalancerName='elb-1',
            Listeners=[
                {
                    'Protocol': 'HTTP',
                    'LoadBalancerPort': 80,
                    'InstancePort': 8080,
                },
            ],
        )
        # can't create ELB with tags right away with moto, workaround:
        elb.add_tags(
            LoadBalancerNames=['elb-1'],
            Tags=[
                {
                    'Key': 'StackName',
                    'Value': 'test_stack'
                },
                {
                    'Key': 'StackVersion',
                    'Value': 'v1'
                },
            ]
        )

        res = agent.get_running_elbs(self.region, self.acc)

        assert len(res) == 1
        e0 = res[0]
        assert e0['stack_name'] == 'test_stack'
        assert e0['stack_version'] == 'v1'

    @moto.mock_autoscaling
    def test_get_auto_scaling_groups(self):
        ec2 = boto3.client('ec2', region_name=self.region)

        autoscaling = boto3.client('autoscaling', region_name=self.region)
        #
        # Even though we are using boto3 here, which as opposed to
        # boto doesn't have a requirement of Launch Configuration for
        # the next step, moto does have that requirement.
        #
        autoscaling.create_launch_configuration(
            LaunchConfigurationName='launch_conf-1'
        )

        autoscaling.create_auto_scaling_group(
            AutoScalingGroupName='asg-1',
            LaunchConfigurationName='launch_conf-1',
            MinSize=1,
            MaxSize=5,
            DesiredCapacity=3,
            HealthCheckGracePeriod=300,
            Tags=[
                {
                    'Key': 'StackName',
                    'Value': 'test_stack'
                },
                {
                    'Key': 'StackVersion',
                    'Value': 'v1'
                },
            ]
        )

        groups = agent.get_auto_scaling_groups(self.region, self.acc)

        assert len(groups) == 1
        g = groups[0]
        assert len(g['instances']) == 3
        assert g['stack_name'] == 'test_stack'
        assert g['stack_version'] == 'v1'

    #@moto.mock_???
#    def test_get_elasticache_nodes(self):
#        elc = agent.get_elasticache_nodes(self.region, self.acc)

    @moto.mock_dynamodb
    def test_get_dynamodb_tables(self):
        tables = agent.get_dynamodb_tables(self.region, self.acc)

    @moto.mock_rds
    def test_get_rds_instances(self):
        rds = agent.get_rds_instances(self.region, self.acc)
