from apps.api.app.claim_mapping import (
    ClaimMapper,
    ClaimMapping,
)

def test_custom_claim_mapping():
    mapping = ClaimMapping.from_json(
        '''
        {
          "roles_claims": [
            "permissions",
            "realm_access.roles",
            "scope"
          ],
          "role_prefix": "role:",
          "subject_claim": "user.id"
        }
        '''
    )
    mapper = ClaimMapper(mapping)
    payload = {
        "user": {"id": "user-42"},
        "permissions": ["viewer", "analyst"],
        "realm_access": {
            "roles": ["ops", "viewer"]
        },
        "scope": "openid role:admin",
    }

    assert mapper.subject(payload) == "user-42"
    assert mapper.roles(payload) == (
        "viewer",
        "analyst",
        "ops",
        "admin",
    )
