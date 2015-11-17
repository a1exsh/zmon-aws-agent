import pytest
import boto3
from zmon_agent import agent


def boto3_client(service_name, region_name=None, **kwargs):

    class boto3_autoscaling(object):
        def describe_auto_scaling_groups(self):
            return { 'AutoScalingGroups': [] }

    class boto3_ec2(object):
        def describe_instances(self):
            return { 'Reservations': [] }

    class boto3_elasticache(object):
        def describe_cache_clusters(self, CacheClusterId=None, MaxRecords=None,
                                    Marker=None, ShowCacheNodeInfo=None):
            return { 'CacheClusters': [] }

    class boto3_elb(object):
        def describe_load_balancers(self):
            return { 'LoadBalancerDescriptions': [] }

        def describe_tags(self, LoadBalancerNames=None):
            return { 'TagDescriptions': [] }

    class boto3_dynamodb(object):
        def list_tables(self):
            return { 'TableNames': [] }

    class boto3_rds(object):
        def describe_db_instances(self):
            return { 'DBInstances': [] }

    services = {
        'autoscaling': boto3_autoscaling,
        'ec2': boto3_ec2,
        'elasticache': boto3_elasticache,
        'elb': boto3_elb,
        'dynamodb': boto3_dynamodb,
        'rds': boto3_rds
    }
    service = services.get(service_name, None)
    if service:
        return service()
    else:
        raise NotImplementedError(service_name)


class TestAgent:
    @pytest.fixture(autouse=True)
    def mock(self):
        boto3.client = boto3_client
        self.region = 'eu-west-1'
        self.acc = 'aws:1234567890'

    def test_get_running_apps(self):
        apps = agent.get_running_apps(self.region)

    def test_get_running_elbs(self):
        elbs = agent.get_running_elbs(self.region, self.acc)

    def test_get_auto_scaling_groups(self):
        groups = agent.get_auto_scaling_groups(self.region, self.acc)

    def test_get_elasticache_nodes(self):
        elc = agent.get_elasticache_nodes(self.region, self.acc)

    def test_get_dynamodb_tables(self):
        tables = agent.get_dynamodb_tables(self.region, self.acc)

    def test_get_rds_instances(self):
        rds = agent.get_rds_instances(self.region, self.acc)
