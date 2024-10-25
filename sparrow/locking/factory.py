

def LockFactory(lock_type):
    if lock_type == 'None':
        ...
        # return NoneLock()
    elif lock_type == 'File':
        ...
        # return FileLock()
    elif lock_type == 'Redis':
        ...
        # return RedisLock()
    elif lock_type == 'Etcd':
        ...
        # return EtcdLock()
    elif lock_type == 'DynamoDB':
        ...
        # return DynamoDBLock()
    elif lock_type == 'Memcached':     
        ...
        # return MemcachedLock()
    else:
        raise ValueError(f"Unknown lock type: {lock_type}")
    