"""Read-only strategy discovery; no repository, collector, scheduler or broker calls."""
from flask import Blueprint, jsonify
from domain.strategy import DEFAULT_STRATEGY_REGISTRY


def create_strategy_blueprint(registry=DEFAULT_STRATEGY_REGISTRY):
    blueprint = Blueprint("strategy_profiles", __name__)

    @blueprint.get("/api/v1/strategy-profiles")
    def listing():
        profiles = [item.to_dict() for item in registry.current_profiles()]
        return jsonify(profiles=profiles, count=len(profiles), schema_version="strategy-profile-api-v1",
                       read_only=True, live_execution=False, strategy_execution_enabled=False)

    @blueprint.get("/api/v1/strategy-profiles/<profile_id>")
    @blueprint.get("/api/v1/strategy-profiles/<profile_id>/versions/<version>")
    def detail(profile_id, version=None):
        try:
            profile = registry.resolve(profile_id, version)
            versions = [item.reference.strategy_profile_version for item in registry.versions(profile_id)]
            return jsonify(profile=profile.to_dict(), available_versions=versions, read_only=True, live_execution=False)
        except KeyError:
            return jsonify(error={"code": "STRATEGY_PROFILE_NOT_FOUND",
                                  "message": "Requested strategy profile/version does not exist"},
                           live_execution=False), 404

    return blueprint
