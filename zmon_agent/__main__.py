from __future__ import print_function

import os
import argparse
import json
import logging
import requests
from datetime import datetime

from . import agent


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")


def main():
    argp = argparse.ArgumentParser(description='ZMon AWS Agent')
    argp.add_argument('-e', '--entity-service', dest='entityservice')
    argp.add_argument('-r', '--region', dest='region', default=None)
    argp.add_argument('-j', '--json', dest='json', action='store_true')
    args = argp.parse_args()

    logging.basicConfig(level=logging.INFO)

    if not args.region:
        logging.info("Trying to figure out region...")
        try:
            response = requests.get('http://169.254.169.254/latest/meta-data/placement/availability-zone', timeout=2)
        except:
            logging.error("Region was not specified as a parameter and can not be fetched from instance meta-data!")
            raise
        region = response.text[:-1]
    else:
        region = args.region

    logging.info("Using region: {}".format(region))

    logging.info("Entity service url: %s", args.entityservice)

    apps = agent.get_running_apps(region)
    if len(apps) > 0:
        infrastructure_account = apps[0]['infrastructure_account']
        elbs = agent.get_running_elbs(region, infrastructure_account)
        scaling_groups = agent.get_auto_scaling_groups(region, infrastructure_account)
        rds = agent.get_rds_instances(region, infrastructure_account)
        elasticaches = agent.get_elasticache_nodes(region, infrastructure_account)
        dynamodbs = agent.get_dynamodb_tables(region, infrastructure_account)
    else:
        elbs = []
        scaling_groups = []
        rds = []

    if args.json:
        d = {'apps': apps, 'elbs': elbs, 'rds': rds, 'elc': elasticaches, 'dynamodb': dynamodbs}
        print(json.dumps(d))
    else:

        if infrastructure_account is not None:
            account_alias = agent.get_account_alias(region)
            ia_entity = {"type": "local",
                         "infrastructure_account": infrastructure_account,
                         "account_alias": account_alias,
                         "region": region,
                         "id": "aws-ac[{}:{}]".format(infrastructure_account, region),
                         "created_by": "agent"}

            application_entities = agent.get_apps_from_entities(apps, infrastructure_account, region)

            current_entities = []

            for e in elbs:
                current_entities.append(e["id"])

            for e in scaling_groups:
                current_entities.append(e["id"])

            for a in apps:
                current_entities.append(a["id"])

            for a in application_entities:
                current_entities.append(a["id"])

            for a in rds:
                current_entities.append(a["id"])

            for a in elasticaches:
                current_entities.append(a["id"])

            for a in dynamodbs:
                current_entities.append(a["id"])

            current_entities.append(ia_entity["id"])

            # removing all entities
            query = {'infrastructure_account': infrastructure_account, 'region': region, 'created_by': 'agent'}
            r = requests.get(args.entityservice,
                             params={'query': json.dumps(query)})
            entities = r.json()

            existing_entities = {}

            to_remove = []
            for e in entities:
                existing_entities[e['id']] = e
                if not e["id"] in current_entities:
                    to_remove.append(e["id"])

            if os.getenv('zmon_user'):
                auth = (os.getenv('zmon_user'), os.getenv('zmon_password', ''))
            else:
                auth = None

            for e in to_remove:
                logging.info("removing instance: {}".format(e))

                r = requests.delete(args.entityservice + "{}/".format(e), auth=auth)

                logging.info("...%s", r.status_code)

            def put_entity(entity_type, entity):
                logging.info("Adding {} entity: {}".format(entity_type, entity['id']))

                r = requests.put(args.entityservice, auth=auth,
                                 data=json.dumps(entity, default=json_serial),
                                 headers={'content-type': 'application/json'})

                logging.info("...%s", r.status_code)

            put_entity('LOCAL', ia_entity)

            for instance in apps:
                put_entity('instance', instance)

            for asg in scaling_groups:
                put_entity('Auto Scaling group', asg)

            for elb in elbs:
                put_entity('elastic load balancer', elb)

            for db in rds:
                put_entity('RDS instance', db)

            # merge here or we loose it on next pull
            for app in application_entities:
                if app['id'] in existing_entities:
                    ex = existing_entities[app['id']]
                    if 'scalyr_ts_id' in ex:
                        app['scalyr_ts_id'] = ex['scalyr_ts_id']

            for app in application_entities:
                put_entity('application', app)

            for elasticache in elasticaches:
                put_entity('elasticache', elasticache)

            for dynamodb in dynamodbs:
                put_entity('dynamodb', dynamodb)

if __name__ == '__main__':
    main()
