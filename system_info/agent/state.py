from typing import Annotated, TypedDict


class GenerationState(TypedDict):
    """
    State for the generation of the service info.
    """

    service_info: Annotated[str, "Content of the service info file"]
    integration_name: Annotated[str, "Name of the integration"]
    collection_via: Annotated[str, "Collection via (tcp, udp, api, logfile)"]
    setup_steps: Annotated[list[str], "Setup steps"]
    urls: Annotated[list[str], "URLs"]
    verified_urls: Annotated[list[str], "Verified URLs"]
