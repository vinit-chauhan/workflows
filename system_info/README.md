# System Info Workflow

A LangGraph-based workflow for generating system documentation for third-party integrations.

## Features

- Automatically finds relevant integration packages
- Extracts setup instructions from integration documentation
- Searches for external product setup information
- Generates comprehensive system documentation
- **Context-aware URL verification** with JavaScript rendering support

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Install Playwright Browsers

After installing the Python dependencies, you need to install the Playwright browser binaries:

```bash
playwright install chromium
```

This installs the Chromium browser required for JavaScript-rendered page fetching.

### 3. Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Google Gemini API Configuration
GEMINI_API_KEY=your_api_key_here
GEMINI_PRO_MODEL=gemini-2.5-pro
GEMINI_FLASH_MODEL=gemini-2.5-flash

# Integration Root Path
INTEGRATION_ROOT_PATH=/path/to/integrations

# Debug Mode (optional)
DEBUG=false
```

## Usage

Run the workflow with an integration name:

```bash
python main.py
```

Then enter the integration name when prompted (e.g., `cisco_ise`, `checkpoint`, etc.)

## URL Verification

The workflow includes an intelligent URL verifier that:

### Key Features:
- **JavaScript Rendering**: Uses Playwright to fetch content from JavaScript-rendered pages
- **Context-Aware Validation**: Applies different validation rules based on the section where URLs appear
- **Section-Based Criteria**:
  - **Product Info Sections**: Allow general product information pages
  - **Setup Sections**: Require actual logging/syslog setup instructions
  - **Documentation Sections**: Keep relevant documentation and reference materials
  - **Troubleshooting Sections**: Keep troubleshooting and error resolution pages

### URL Validation Rules:

1. **elastic.co domains**: Always kept if status code is 200
2. **Product Info/Overview sections**: General product pages are acceptable
3. **Setup/Configuration sections**: Must contain logging setup instructions (strict validation)
4. **Documentation sections**: Must be relevant documentation or reference material
5. **Broken links**: Always removed (non-200 status codes)

### How It Works:

1. Extracts section context for each URL in the document
2. Fetches actual page content using a headless browser (handles JavaScript)
3. Applies validation rules based on section type and content
4. Removes invalid URLs while preserving document formatting

## Output

The workflow generates a markdown file in the `output/` directory with the following structure:

- Service Info (use cases, data types, compatibility, scaling)
- Set Up Instructions (vendor prerequisites, Elastic prerequisites, setup steps)
- Validation Steps
- Troubleshooting
- Documentation Sites (verified URLs only)

## Architecture

The workflow uses LangGraph with the following nodes:

1. `find_relevant_packages_node`: Matches user input to integration packages
2. `get_package_info_node`: Loads integration manifest and documentation
3. `setup_instructions_context_node`: Extracts useful context from integration docs
4. `setup_instructions_external_info_node`: Searches for external setup instructions
5. `final_result_generation_node`: Generates comprehensive documentation
6. `url_verification_node`: Verifies and validates all URLs with context awareness

## Troubleshooting

### Playwright Installation Issues

If you encounter issues with Playwright, try:

```bash
# Reinstall Playwright browsers
playwright install --force chromium

# Or install all browsers
playwright install
```

### Browser Launch Errors

If the browser fails to launch, ensure you have the necessary system dependencies:

- **macOS**: Should work out of the box
- **Linux**: May need `libgbm`, `libnss3`, `libxss1`, etc.
- **Windows**: Should work out of the box

### Timeout Issues

If pages are timing out, you can modify the timeout in `workflow/tools.py`:

```python
response = page.goto(url, timeout=30000, wait_until='networkidle')  # 30 seconds
```

## Development

To enable debug mode, set `DEBUG=true` in your `.env` file. This will show detailed logging from the LangGraph agents.

