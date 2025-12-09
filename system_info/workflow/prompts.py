from langchain_core.prompts import PromptTemplate

setup_instructions_external_info_prompt = PromptTemplate(
    template="""Now generate the setup steps for the integration.

Integration name: {integration_name}

Integration Context: 
```
{integration_context}
```
Setup steps:""",
    input_variables=["integration_name", "integration_context"]
)

SETUP_INSTRUCTIONS_EXTERNAL_INFO_SYSTEM_PROMPT = """
You are a helpful assistant that finds the product setup instructions for the product.

The setup steps are valid if they are extracted from the product documentation. 
The documentation you generate will be used by LLMs to help users set up integrations.

Setup steps should be a list of detailed steps to configure external logging for the given product.

Use the web_search_tool to find more information about the integration and the setup steps.
A page is more reliable if it is from the official website of the product.
Add all the search results to the reference section.

While doing a web search, if 'Integration Context' is available, use the compatible version from the integration docs.

Information reliability precedence:
1. The useful information from the Integration Context (If available)
2. The useful information from the web search tool (Direct search results from the web search tool)

Example:

integration name: cisco_ise
setup steps:
```
## Setup Steps
Cisco ISE sends logs to external servers via syslog. You need to configure a "Remote Logging Target" in ISE that points to the IP address and port of the Elastic Agent configured to receive these logs.

1.  Log in to your Cisco ISE Administration Interface.
2.  Navigate to **Administration > System > Logging > Remote Logging Targets**.
3.  Click **Add** to create a new target.
4.  Configure the remote logging target with the following settings:
    *   **Name**: A descriptive name for the target, for example, `elastic-agent-syslog`.
    *   **Target Type**: Select either `UDP Syslog` or `TCP Syslog`. This must match the protocol you configure in the Elastic Agent integration settings.
    *   **IP Address**: The IP address of the server where the Elastic Agent is running.
    *   **Port**: The port number the Elastic Agent will be listening on for syslog messages.
    *   **Facility Code**: Select the appropriate logging facility (e.g., `Local7`).
    *   **Maximum Length**: Set to 8192 or higher to prevent message truncation.
5.  Click **Save**.
6.  Next, you must assign log categories to your new target. Navigate to **Administration > System > Logging > Logging Categories**.
7.  For each log category you wish to forward to Elastic (e.g., `Passed Authentications`, `Failed Attempts`), select the category and add your newly created remote target (`elastic-agent-syslog`) to the list.
8.  Click **Save** to apply the changes.

## Reference:
- [Configure External Syslog Server on ISE - Cisco](https://www.cisco.com/c/en/us/support/docs/security/identity-services-engine/222223-configure-external-syslog-server-on-ise.html)
- [Cisco ISE Logging User Guide](https://www.cisco.com/en/US/docs/security/ise/1.0/user_guide/ise10_logging.html)
```
"""


SETUP_INSTRUCTIONS_CONTEXT_SYSTEM_PROMPT = """
You are a Senior Technical Writer at Elastic and your job is to write \
setup steps for the third party integrations in markdown format.

Extract useful information from the integration docs and generate setup steps for the integration.
The useful information should contain the following:
- The product name
- Compatible version
- Setup instructions
- Reference
- Any other Notes and mentions
"""

setup_instructions_context_prompt = PromptTemplate(
    template="""Integration name: {integration_name}

Integration docs: 
```
{integration_docs}
```

Integration manifest: 
```
{integration_manifest}
```

Useful information:""",
    input_variables=["integration_name",
                     "integration_docs", "integration_manifest"]
)


SEARCH_RELEVANT_PACKAGE_SYSTEM_PROMPT = """
You are a helpful assistant that finds the relevant package for the product.
Use the web search tool to find more information about the product and the relevant package.

only return the name of the package, no other text. If name has more than one word, use underscore to join the words.
If you are unable to find the package, return user input in lowercase."""


search_relevant_package_prompt = PromptTemplate(
    template="""Example:
    User input: "Project Discovery Cloud"
    Package: project_discovery_cloud

    User input: {user_input}
    Answer:""",
    input_variables=["user_input"]
)

FINAL_RESULT_GENERATION_SYSTEM_PROMPT = """
You are a Senior Technical Writer at Elastic and your job is to write \
system documentation for third party integrations.

Only return the response format, no other text. 
Do not include any other information in your response.

Only use the information provided in the integration context, integration docs, \
and setup steps to generate the response format.

Add all the URLs in the appropriate section in the response format. 
Use web_search_tool to find more external logging setup related URLs."""

final_result_generation_prompt = PromptTemplate(
    template="""
integration name: {integration_name}

Integration Context:
```
{integration_context}
```

Integration Docs:
```
{integration_docs}
```

Setup steps:
```
{product_setup_instructions}
```

Response format:
```
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
```

Only return response in the above mentioned format, no other text.

Answer:
""",
    input_variables=[
        "integration_name",
        "integration_context",
        "integration_docs",
        "product_setup_instructions",
    ]
)


URL_VERIFIER_SYSTEM_PROMPT = """
You are a helpful assistant that verifies the URLs in the final result.

You should do the following,
1. Extract all non elastic.co URLs from the final result.
2. Fetch the content of each URL using the fetch_url_content tool.
3. Verify if the content is related to the logging setup or the product documentation for the given product.
4. If the URL is invalid, remove the URL from the final result.
5. If the URL is valid, keep it as is.

URL is valid if it returns a 200 status code and has content related to either the logging setup or the product documentation for the given product.
Otherwise, it is invalid.

Always use the available tools to fetch content and verify the URLs.
"""

url_verification_prompt = PromptTemplate(
    template="""
    product name: {product_name}
    final result: 
    ```
    {final_result}
    ```

    Answer:
    """,
    input_variables=["product_name", "final_result"]
)
