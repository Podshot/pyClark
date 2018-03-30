# PyClark
Remote error reporting that helps save the day

## Important Notice
If you are using PyClark in a project, whether it be open/close/other sourced and in source code or
in a compiled distribution form, you MUST ask the user for their permission to send error reports and inform them of what data
is sent and notify them about how this relates to the data they input into your program. Failure to follow these instructions
this means that permission to use this library is NOT granted under any circumstance.

The above notice is meant to prevent misuse of this library and protect user privacy and information.

## Goals
Create an efficient error/log reporting package that reports anonymized data back to a self-hosted
web portal (will be included at a later date, working title: Kent) for better debugging. This is aimed
more for distributed applications than a website/service. 

## Requirements
- requests

## Usage
```python
import traceback
from pyClark import Clark # Will be changed to Clark if the current package name stays

Clark.suit_up('http://127.0.0.1')

try:
	raise NotImplementedError()
except Exception as e:
	report_id = Clark.report(e, locals=locals(), globals=globals()) # Reports the full stacktrace plus optional serialized local/global veriables
	traceback.print_exc()
	print "Your report ID is: ", report_id # A Unique ID is generated server-side for users to match their error reports if they self-report the error as well
```

#### TODO