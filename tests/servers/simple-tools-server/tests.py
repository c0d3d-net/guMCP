import pytest
from tests.utils.test_tools import get_test_id, run_tool_test


# Shared context dictionary at module level
SHARED_CONTEXT = {}

TOOL_TESTS = [
    {
        "name": "store_data",
        "args_template": 'with key="test_key" value="test_value"',
        "expected_keywords": ["id"],
        "regex_extractors": {"id": r"id:\s*([A-Za-z0-9_]+)"},
        "description": "store a key-value pair and return confirmation",
    },
    {
        "name": "retrieve_data",
        "args_template": 'with key="{id}"',
        "expected_keywords": ["id"],
        "regex_extractors": {"id": r"id:\s*([A-Za-z0-9_]+)"},
        "description": "retrieve a value by its key",
        "depends_on": ["id"],
    },
    {
        "name": "list_data",
        "args_template": "with",
        "expected_keywords": ["id"],
        "regex_extractors": {"id": r"id:\s*([A-Za-z0-9_]+)"},
        "description": "list all stored key-value pairs",
    },
    {
        "name": "store_data",
        "args_template": 'with key="another_key" value="another_value"',
        "expected_keywords": ["id"],
        "regex_extractors": {"id": r"id:\s*([A-Za-z0-9_]+)"},
        "description": "store additional data",
    },
    {
        "name": "retrieve_data",
        "args_template": 'with key="nonexistent_key"',
        "expected_keywords": ["id"],
        "regex_extractors": {"id": r"id:\s*([A-Za-z0-9_]+)"},
        "description": "handle retrieval of non-existent key",
    },
    {
        "name": "list_data",
        "args_template": "with",
        "expected_keywords": ["id"],
        "regex_extractors": {"id": r"id:\s*([A-Za-z0-9_]+)"},
        "description": "list all data after adding multiple entries",
    },
]


@pytest.fixture(scope="module")
def context():
    return SHARED_CONTEXT


@pytest.mark.parametrize("test_config", TOOL_TESTS, ids=get_test_id)
@pytest.mark.asyncio
async def test_simple_tools_tool(client, context, test_config):
    return await run_tool_test(client, context, test_config)
