import pytest

from jellyfin import jellyfin_library_declaration
from jellyseerr import jellyseerr_account_permissions


def libraries():
    return [
        {"Name": "Movies", "ItemId": "movies"},
        {"Name": "TV", "ItemId": "tv"},
        {"Name": "Movies (Private)", "ItemId": "private"},
    ]


def test_ordinary_friend_cannot_see_private_libraries():
    assert jellyfin_library_declaration.resolve_visible_library_ids(
        libraries(), "friend"
    ) == ["movies", "tv"]


def test_missing_public_library_refuses_a_partial_visibility_write():
    with pytest.raises(ValueError, match="missing from Jellyfin: TV"):
        jellyfin_library_declaration.resolve_visible_library_ids(
            libraries()[:1], "friend"
        )


def test_friend_requests_autoapprove_without_request_visibility_permissions():
    requester = {"id": 2, "jellyfinUsername": "friend", "permissions": 0}
    assert (
        jellyseerr_account_permissions.desired_requester_permissions(requester) == 160
    )
    assert not jellyseerr_account_permissions.account_administers_jellyseerr(requester)
    assert jellyseerr_account_permissions.account_administers_jellyseerr({"id": 1})
