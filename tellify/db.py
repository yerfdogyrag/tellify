

from config import get_redis_client, default_expiration
import json


def save_config(config):
    '''
    Config must have _id and must be jsonifyable
    '''
    
    redis = get_redis_client()
    redis.set('config-'+config['_id'], json.dumps(config))

def set_event_state(config_id, event_dict):
    '''
    Used by event handlers that need to set specific states
    '''

    redis = get_redis_client()
    redis.set('config-'+config['_id'], json.dumps(config))
