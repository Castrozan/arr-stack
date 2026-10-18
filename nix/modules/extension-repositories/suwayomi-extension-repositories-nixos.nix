{
  config,
  lib,
  pkgs,
  ...
}:
let
  settings = config.services.arrStack;
  secret =
    settings.secrets.extensionRepositories or {
      file = "";
      source = null;
    };
  declarationDigest = if secret.source == null then "" else builtins.hashFile "sha256" secret.source;
in
{
  config = lib.mkIf (settings.enable && secret.file != "") {
    systemd.services.suwayomi-extension-repositories = {
      description = "Point Suwayomi at the declared extension repositories";
      after = [ "arr-stack-front-ends-compose.service" ];
      requires = [ "arr-stack-front-ends-compose.service" ];
      wantedBy = [ "multi-user.target" ];
      restartTriggers = lib.optional (secret.source != null) secret.source;
      environment = {
        SUWAYOMI_GRAPHQL_URL = "http://${settings.bindAddress}:4567/api/graphql";
        SUWAYOMI_EXTENSION_REPOSITORIES_FILE = secret.file;
        SUWAYOMI_EXTENSION_REPOSITORIES_DECLARATION_DIGEST = declarationDigest;
      };
      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
        User = settings.user;
        Group = settings.group;
        ExecStart = "${pkgs.python3}/bin/python3 ${./scripts/suwayomi_extension_repositories}";
        TimeoutStartSec = "5min";
      };
    };
  };
}
