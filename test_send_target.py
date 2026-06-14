"""Offline tests for the chat_id | user_id recipient rule and action_button.

Run: python test_send_target.py   (or: pytest test_send_target.py)
"""
import sys
from dataclasses import asdict

sys.path.insert(0, 'src')

from kappelas import ActionButton  # noqa: E402
from kappelas.resources.messages import MessagesResource  # noqa: E402


def test_recipient_json():
    assert MessagesResource._recipient(None, 'u') == {'user_id': 'u'}
    assert MessagesResource._recipient(42, None) == {'chat_id': 42}
    try:
        MessagesResource._recipient(None, None)
        raise AssertionError('expected ValueError')
    except ValueError:
        pass


def test_media_fields():
    m = MessagesResource(None, '')  # http unused for field building
    assert m._media_fields(None, 'u', None, None, False, None) == {'user_id': 'u'}
    assert m._media_fields(42, None, None, None, False, None) == {'chat_id': '42'}
    # user_id wins when both supplied
    assert m._media_fields(42, 'u', None, None, False, None) == {'user_id': 'u'}


def test_action_button_serialises():
    ab = ActionButton(label='Copy', type='copy_text', value='123')
    assert asdict(ab) == {'label': 'Copy', 'type': 'copy_text', 'value': '123'}


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_') and callable(fn):
            fn()
            print(f'  ok {name}')
    print('All offline tests passed')
