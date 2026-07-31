from shared.constants import MessageRole, RouteAction


def test_route_action_values() -> None:
    assert RouteAction.DOC_SEARCH == "doc_search"
    assert RouteAction.END == "END"


def test_message_role_values() -> None:
    assert MessageRole.USER == "user"
    assert MessageRole.MODEL == "model"
