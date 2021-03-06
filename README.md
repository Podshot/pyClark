# PyClark
Remote error reporting that helps save the day

## Goals
Create an efficient error/log reporting package that reports anonymized data back to a self-hosted
web portal (will be included at a later date, working title: Kent) for better debugging. This is aimed
more for distributed applications than a website/service. 

## Requirements
- requests

## Usage
```python
import traceback
import pyClark

clark = pyClark.Clark('http://127.0.0.1')

try:
	raise NotImplementedError()
except Exception as e:
	report_id = clark.report(e, locals=locals(), globals=globals()) # Reports the full stacktrace plus optional serialized local/global variables
	traceback.print_exc()
	print "Your report ID is: ", report_id # A Unique ID is generated server-side for users to match their error reports if they self-report the error as well
```