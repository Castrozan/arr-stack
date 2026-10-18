{ config, lib, ... }:
let
  inherit (lib) mkOption types;
in
{
  options.arrMediaOperatorDiscordUserId = mkOption {
    type = types.nullOr types.str;
    default = null;
    description = "Verified Discord operator allowed to remove public library media.";
  };
  options.services.arrStack = {
    enable = lib.mkEnableOption "the media Compose declaration and command-line tools";
    directory = mkOption {
      type = types.str;
      default = "${config.home.homeDirectory}/arr-stack";
      description = "Compose project directory under the user home.";
    };
    bindAddress = mkOption {
      type = types.str;
      default = "127.0.0.1";
      description = "Host address receiving application web ports.";
    };
    timezone = mkOption {
      type = types.str;
      default = "UTC";
      description = "Application timezone.";
    };
    userId = mkOption {
      type = types.int;
      default = 1000;
      description = "Media UID.";
    };
    groupId = mkOption {
      type = types.int;
      default = 1000;
      description = "Media GID.";
    };
    accounts = mkOption {
      type = types.attrsOf (types.listOf types.str);
      default = builtins.fromJSON (builtins.readFile ../../../config/accounts.json);
      description = "Named media access allowlists.";
    };
    jellyfinApiKeyFile = mkOption {
      type = types.str;
      description = "Runtime Jellyfin administrative API key file.";
    };
    hardwareAcceleration = mkOption {
      type = types.enum [
        "cpu"
        "nvidia"
      ];
      default = "cpu";
      description = "Jellyfin container hardware access.";
    };
    containerCgroupParent = mkOption {
      type = types.nullOr types.str;
      default = null;
      description = "Existing media container parent cgroup.";
    };
    jellyfinPublicUrl = mkOption {
      type = types.str;
      default = "http://${config.services.arrStack.bindAddress}:8096";
      description = "Jellyfin email-link origin.";
    };
    readmeabookPublicUrl = mkOption {
      type = types.str;
      default = "http://${config.services.arrStack.bindAddress}:3030";
      description = "Audiobook request origin.";
    };
    publicRequesterUsername = mkOption {
      type = types.str;
      default = "public-requests";
      description = "Ordinary public-request CLI account.";
    };
  };
}
