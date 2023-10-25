import pytest

from .datasources import mock_datasource_dir_from_hf
from .responses import mock_responses_from_hf


@pytest.fixture(scope='session')
def danbooru():
    with mock_responses_from_hf('danbooru'):
        yield


@pytest.fixture(scope='session')
def safebooru():
    with mock_responses_from_hf('safebooru'):
        yield


@pytest.fixture(scope='session')
def ccip_simple():
    with mock_datasource_dir_from_hf('ccip_simple') as dir_:
        yield dir_


@pytest.fixture(scope='session')
def ccip_mudrock():
    with mock_datasource_dir_from_hf('ccip_mudrock') as dir_:
        yield dir_
