{
  pkgs,
  stackRoot,
  policyFile,
  jellyfinApiKeyFile,
}:
let
  arrUsersPackageDirectory = ../../../runtime/arr_users;
in
pkgs.writeShellScriptBin "arr-users" ''
  set -Eeuo pipefail

  export ARR_ACCOUNT_POLICY_FILE=${pkgs.lib.escapeShellArg (toString policyFile)}
  export ARR_USERS_LIBRARY_ROOT=/media
  export ARR_USERS_JELLYFIN_BASE_URL=http://127.0.0.1:8096
  export ARR_USERS_JELLYSEERR_BASE_URL=http://127.0.0.1:5055
  export ARR_USERS_JELLYFIN_API_KEY_FILE="''${ARR_USERS_JELLYFIN_API_KEY_FILE:-${jellyfinApiKeyFile}}"
  export ARR_USERS_JELLYSEERR_SETTINGS_FILE="''${ARR_USERS_JELLYSEERR_SETTINGS_FILE:-${stackRoot}/config/jellyseerr/settings.json}"

  exec ${pkgs.python312}/bin/python3 ${arrUsersPackageDirectory}/__main__.py "$@"
''
