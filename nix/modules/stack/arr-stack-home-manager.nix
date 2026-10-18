{
  config,
  lib,
  pkgs,
  ...
}:
let
  settings = config.services.arrStack;
  stackRoot = settings.directory;
  policyFile = pkgs.writeText "arr-account-policy.json" (builtins.toJSON settings.accounts);
  artifacts = import ./artifacts.nix { inherit pkgs lib settings; };
  projectPath = lib.removePrefix "${config.home.homeDirectory}/" stackRoot;
  arrUsersCli = import ../users/arr-users-cli-home-manager.nix {
    inherit pkgs stackRoot policyFile;
    jellyfinApiKeyFile = settings.jellyfinApiKeyFile;
  };
  arrStatusCli = import ../status/arr-status-cli-home-manager.nix { inherit pkgs stackRoot; };
  arrMediaCli = import ../status/arr-media-cli-home-manager.nix {
    inherit pkgs stackRoot;
    operatorDiscordUserId = config.arrMediaOperatorDiscordUserId;
    requesterUsername = settings.publicRequesterUsername;
  };
in
{
  imports = [
    ./options.nix
    ./persistence.nix
  ];
  config = lib.mkIf settings.enable {
    home.packages = [
      arrUsersCli
      arrStatusCli
      arrMediaCli
    ];
    home.file = {
      "${projectPath}/docker-compose.yml".source = artifacts.compose;
      "${projectPath}/.env".text = artifacts.environmentText;
      "${projectPath}/README.md".source = ../../../README.md;
    };
  };
}
