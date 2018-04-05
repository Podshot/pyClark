import re

def anonymize(item):
    result = re.sub(r'([A-Z]{1}\:/[Uu]sers/)([^/]*)', '<user>', item)
    result = re.sub(r'/home/\w+/', '<user>', result)
    return result
