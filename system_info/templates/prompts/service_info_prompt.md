You are a Senior Technical Writer and you are tasked with writing \
on-boarding document for third party integrations. Especially the \
product setup for on-boarding.

for the following product: {integration_name}
collection via: {collection_via}
setup steps doc template:

# Service Info

## Common use cases

/_ Common use cases that this will facilitate _/

## Data types collected

/_ What types of data this integration can collect _/

## Compatibility

/_ Information on the vendor versions this integration is compatible with or has been tested against _/

## Scaling and Performance

/_ Vendor-specific information on what performance can be expected, how to set up scaling, etc. _/

# Set Up Instructions

## Vendor prerequisites

/_ Add any vendor specific prerequisites, e.g. "an API key with permission to access <X, Y, Z> is required" _/

## Elastic prerequisites

/_ If there are any Elastic specific prerequisites, add them here
The stack version and agentless support is not needed, as this can be taken from the manifest _/

## Vendor set up steps

/_ List the specific steps that are needed in the vendor system to send data to Elastic.
If multiple input types are supported, add instructions for each in a subsection _/

## Kibana set up steps

/_ List the specific steps that are needed in Kibana to add and configure the integration to begin ingesting data _/

# Validation Steps

/_ List the steps that are needed to validate the integration is working, after ingestion has started.
This may include steps on the vendor system to trigger data flow, and steps on how to check the data is correct in Kibana dashboards or alerts. _/

# Troubleshooting

/* Add lists of "*Issue* / *Solutions*" for troubleshooting knowledge base into the most appropriate section below */

## Common Configuration Issues

/_ For generic problems such as "service failed to start" or "no data collected" _/

## Ingestion Errors

/_ For problems that involve "error.message" being set on ingested data _/

## API Authentication Errors

/_ For API authentication failures, credential errors, and similar _/

## Vendor Resources

/_ If the vendor has a troubleshooting specific help page, add it here _/

# Documentation sites

/_ List of URLs that contain info on the service (reference pages, set up help, API docs, etc. _/

update the setup steps document template with the following information \
and return only the updated template without any other text:

```
{setup_steps}
```

```json
{manifest}
```

Updated Template:
