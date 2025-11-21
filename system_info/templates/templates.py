# pylint: disable=C0114
# flake8: noqa: E501

from langchain_core.prompts import PromptTemplate


with open("templates/prompts/service_info_prompt.md", "r", encoding="utf-8") as f:
    _service_info_prompt_template = f.read()

with open("templates/prompts/setup_steps_prompt.md", "r", encoding="utf-8") as f:
    _setup_steps_prompt_template = f.read()


setup_steps_prompt = PromptTemplate(
    template=_setup_steps_prompt_template,
    input_variables=["integration_name", "collection_via"]
)

service_info_prompt = PromptTemplate(
    template=_service_info_prompt_template,
    input_variables=["integration_name",
                     "collection_via", "setup_steps", "manifest"],
)


link_verification_prompt = PromptTemplate(
    input_variables=["link"],
    template="""
    You are a link verifier.
    You will be given a link and you need to verify if it is a valid link and has content.
    In the content from the page is missing, consider the page as invalid.

    If it is a valid link with content, you respond with "valid".
    If it is not a valid link, you respond with "invalid".

    Only respond with "valid" or "invalid"
    If the link is invalid, provide a reason for the invalidity.
    The reason should be a short description of the issue in 10 words or less.

    Link: {link}
    Page Content: {page_content}
    Answer:
    """
)
