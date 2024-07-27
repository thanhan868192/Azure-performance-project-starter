from flask import Flask, request, render_template
import os
import random
import redis
import socket
import sys
import logging
from datetime import datetime

# App Insights
# TODO: Import required libraries for App Insights
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.log_exporter import AzureEventHandler
from opencensus.ext.azure import metrics_exporter
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.stats import stats as stats_module
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace import config_integration

# Logging
config_integration.trace_integrations(['logging'])
config_integration.trace_integrations(['requests'])
logger = logging.getLogger(__name__)# TODO: Setup logger

handler = AzureLogHandler(connection_string='InstrumentationKey=bd4929a1-954a-46c1-aedd-3046bb50ee1a;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=d0535ad5-7755-4112-8b2d-8b3ea1c6c748')
handler.setFormatter(logging.Formatter('%(traceId)s %(spandId)s %(message)s'))
logger.addHandler(handler)

logger.addHandler(AzureEventHandler(connection_string='InstrumentationKey=bd4929a1-954a-46c1-aedd-3046bb50ee1a;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=d0535ad5-7755-4112-8b2d-8b3ea1c6c748'))
logger.setLevel(logging.INFO)

stats = stats_module.stats
view_manager = stats.view_manager

# Metrics
exporter = metrics_exporter.new_metrics_exporter(
    enabled_standard_metrics=True,
    connection_string='InstrumentationKey=bd4929a1-954a-46c1-aedd-3046bb50ee1a;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=d0535ad5-7755-4112-8b2d-8b3ea1c6c748')# TODO: Setup exporter
view_manager.register_exporter(exporter)

# Tracing
tracer = Tracer(
    exporter=AzureExporter(connection_string='InstrumentationKey=bd4929a1-954a-46c1-aedd-3046bb50ee1a;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=d0535ad5-7755-4112-8b2d-8b3ea1c6c748'),
    sampler=ProbabilitySampler(1.0)) # TODO: Setup tracer

app = Flask(__name__)

# Requests
middleware =  FlaskMiddleware(
    app,
    exporter=AzureExporter(connection_string='InstrumentationKey=bd4929a1-954a-46c1-aedd-3046bb50ee1a;IngestionEndpoint=https://westus-0.in.applicationinsights.azure.com/;LiveEndpoint=https://westus.livediagnostics.monitor.azure.com/;ApplicationId=d0535ad5-7755-4112-8b2d-8b3ea1c6c748'),
    sampler=ProbabilitySampler(1.0)) # TODO: Setup flask middleware

# Load configurations from environment or config file
app.config.from_pyfile('config_file.cfg')

if ("VOTE1VALUE" in os.environ and os.environ['VOTE1VALUE']):
    button1 = os.environ['VOTE1VALUE']
else:
    button1 = app.config['VOTE1VALUE']

if ("VOTE2VALUE" in os.environ and os.environ['VOTE2VALUE']):
    button2 = os.environ['VOTE2VALUE']
else:
    button2 = app.config['VOTE2VALUE']

if ("TITLE" in os.environ and os.environ['TITLE']):
    title = os.environ['TITLE']
else:
    title = app.config['TITLE']

# Redis Connection
r = redis.Redis()

# Change title to host name to demo NLB
if app.config['SHOWHOST'] == "true":
    title = socket.gethostname()

# Init Redis
if not r.get(button1): r.set(button1,0)
if not r.get(button2): r.set(button2,0)

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'GET':

        # Get current values
        vote1 = r.get(button1).decode('utf-8')
        # TODO: use tracer object to trace cat vote
        tracer.span(name="Cats_vote")
        
        vote2 = r.get(button2).decode('utf-8')
        # TODO: use tracer object to trace dog vote
        tracer.span(name="Dogs_vote")

        # Return index with values
        return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

    elif request.method == 'POST':

        if request.form['vote'] == 'reset':

            # Empty table and return results
            r.set(button1,0)
            r.set(button2,0)
            vote1 = r.get(button1).decode('utf-8')
            properties = {'custom_dimensions': {'Cats Vote': vote1}}
            # TODO: use logger object to log cat vote
            logger.info('cat vote', extra=properties)

            vote2 = r.get(button2).decode('utf-8')
            properties = {'custom_dimensions': {'Dogs Vote': vote2}}
            # TODO: use logger object to log dog vote
            logger.info('dog_vote', extra=properties)

            return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

        else:

            # Insert vote result into DB
            vote = request.form['vote']
            r.incr(vote,1)

            # Get current values
            vote1 = r.get(button1).decode('utf-8')
            vote2 = r.get(button2).decode('utf-8')

            # Return results
            return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

if __name__ == "__main__":
    # TODO: Use the statement below when running locally
    # app.run() 
    # TODO: Use the statement below before deployment to VMSS
    app.run(host='0.0.0.0', threaded=True, debug=True) # remote
