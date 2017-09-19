import pytest
import os

from mmworkbench.components.nlp import NaturalLanguageProcessor
from mmworkbench.components.dialogue import Conversation

APP_NAME = 'kwik_e_mart'
APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), APP_NAME)


@pytest.fixture
def setup_class():
    nlp = NaturalLanguageProcessor(app_path=APP_PATH)
    nlp.build()
    nlp.dump()
    nlp.load()
    return nlp, Conversation(nlp=nlp, app_path=APP_PATH)


def test_allowed_intents_is_cleared():
    """Tests that the next_turn_settings container dict is cleared about one trip from
    app to wb.
    """
    nlp, conv = setup_class()

    conv.allowed_intents = ['store_info.find_nearest_store']
    conv.say("close door")
    assert not conv.allowed_intents
