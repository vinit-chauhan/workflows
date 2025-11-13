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
