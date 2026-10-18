{ config, lib, ... }:
let
  inherit (lib) mkOption types;
  settings = config.services.arrStack;
  stringOption =
    default: description:
    mkOption {
      type = types.str;
      inherit default description;
    };
in
{
  options.services.arrStack = {
    enable = lib.mkEnableOption "the opinionated Docker media stack";
    user = mkOption {
      type = types.str;
      description = "Existing user that owns media storage and command-line tools.";
    };
    group = stringOption config.users.users.${settings.user}.group "Group that owns media storage.";
    directory = stringOption "${config.users.users.${settings.user}.home}/arr-stack" "Compose project and persistent application configuration directory.";
    bindAddress = stringOption "127.0.0.1" "Host address receiving published application ports.";
    timezone = stringOption (
      if config.time.timeZone == null then "UTC" else config.time.timeZone
    ) "Application timezone.";
    userId = mkOption {
      type = types.int;
      default =
        if config.users.users.${settings.user}.uid == null then
          1000
        else
          config.users.users.${settings.user}.uid;
      description = "Numeric media owner UID.";
    };
    groupId = mkOption {
      type = types.int;
      default =
        if config.users.groups.${settings.group}.gid == null then
          1000
        else
          config.users.groups.${settings.group}.gid;
      description = "Numeric media group GID.";
    };
    loginUsername = stringOption "admin" "Owner login applied to the media applications.";
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
      description = "Existing parent cgroup for media containers.";
    };
    dataDeviceUnit = mkOption {
      type = types.nullOr types.str;
      default = null;
      description = "Device unit that gates removable media storage.";
    };
    dataMountUnit = mkOption {
      type = types.nullOr types.str;
      default = null;
      description = "Mount unit that gates removable media storage.";
    };
    keepChainAlwaysOn = mkOption {
      type = types.bool;
      default = true;
      description = "Keep the download applications resident between requests.";
    };
    publicRequesterUsername = stringOption "public-requests" "Ordinary account used by the public request CLI.";
    jellyfinPublicUrl = stringOption "http://${settings.bindAddress}:8096" "Browser-facing Jellyfin URL used in available-media emails.";
    readmeabookPublicUrl = stringOption "http://${settings.bindAddress}:3030" "Browser-facing audiobook request URL.";
    accounts = mkOption {
      type = types.attrsOf (types.listOf types.str);
      default = builtins.fromJSON (builtins.readFile ../../config/accounts.json);
      description = "Named private-library, administrator, and advanced-request allowlists.";
    };
    secrets = mkOption {
      default = { };
      description = "Runtime secret paths and optional encrypted sources used to trigger reconciliation.";
      type = types.attrsOf (
        types.submodule {
          options = {
            file = mkOption {
              type = types.str;
              description = "Runtime path to a decrypted secret.";
            };
            source = mkOption {
              type = types.nullOr types.path;
              default = null;
              description = "Encrypted source that triggers deployment when changed.";
            };
          };
        }
      );
    };
    smtp = {
      username = stringOption "" "SMTP account username.";
      sender = stringOption "" "Notification sender address.";
      recipient = stringOption "" "Disk-guard alert recipient address.";
    };
    removedExtensionPackages = mkOption {
      type = types.listOf types.str;
      default = [ ];
      description = "Miwayomi source packages that reconciliation removes.";
    };
  };
}
