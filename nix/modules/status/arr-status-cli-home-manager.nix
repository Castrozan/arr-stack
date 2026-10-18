{ pkgs, stackRoot }:
let
  arrStatusPackageDirectory = ../../../runtime/arr_status;
in
pkgs.writeShellScriptBin "arr-status" ''
  set -Eeuo pipefail

  export ARR_STATUS_STACK_HOME="''${ARR_STATUS_STACK_HOME:-${stackRoot}}"
  export ARR_STATUS_JELLYSEERR_BASE_URL=http://127.0.0.1:5055

  exec ${pkgs.python312}/bin/python3 ${arrStatusPackageDirectory}/__main__.py "$@"
''
