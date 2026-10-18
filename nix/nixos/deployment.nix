{
  config,
  lib,
  pkgs,
  ...
}:
let
  settings = config.services.arrStack;
  policyFile = pkgs.writeText "arr-account-policy.json" (builtins.toJSON settings.accounts);
  policyServices = [
    "jellyfin-library-access-provisioner"
    "jellyseerr-account-permission-provisioner"
    "jellyseerr-private-request-routing-provisioner"
  ];
  secretSources =
    names:
    lib.filter (source: source != null) (map (name: settings.secrets.${name}.source or null) names);
  disabledServices =
    lib.optional (!config.custom.jellyseerrEmailNotifications.enable) "jellyseerr-email-notifications"
    ++ lib.optional (!config.custom.audiobookProvisioner.enable) "arr-audiobook-provisioner"
    ++ lib.optional (
      (settings.secrets.extensionRepositories.file or "") == ""
    ) "miwayomi-extension-repositories";
  credentialTriggers = lib.filterAttrs (name: _: !(builtins.elem name disabledServices)) {
    jellyseerr-email-notifications = [ "smtpPassword" ];
    arr-config-provisioner = [
      "qbittorrentPassword"
      "radarrPassword"
      "sonarrPassword"
      "prowlarrPassword"
      "samaritanoApiKey"
    ];
    arr-download-cleanup = [
      "qbittorrentPassword"
      "jellyfinApiKey"
    ];
    bazarr-auth-provisioner = [ "bazarrPassword" ];
    jellyfin-library-access-provisioner = [ "jellyfinApiKey" ];
    miwayomi-extension-repositories = [ "extensionRepositories" ];
    jellyseerr-private-request-routing-provisioner = [ "jellyfinApiKey" ];
    jellyseerr-account-permission-provisioner = [ "jellyfinApiKey" ];
    arr-audiobook-provisioner = [
      "qbittorrentPassword"
      "readmeabookPassword"
      "audiobookshelfPassword"
    ];
  };
in
{
  config = lib.mkIf settings.enable {
    systemd.services = lib.mkMerge [
      (lib.genAttrs policyServices (_: {
        environment = {
          ARR_ACCOUNT_POLICY_FILE = toString policyFile;
          ARR_USERS_LIBRARY_ROOT = "/media";
        };
        restartTriggers = [ policyFile ];
      }))
      (lib.mapAttrs (_: names: { restartTriggers = secretSources names; }) credentialTriggers)
      {
        docker.unitConfig.RequiresMountsFor = [ "${settings.directory}/data" ];
        arr-stack-front-ends-compose = {
          preStart = "${pkgs.coreutils}/bin/chown -R ${toString settings.userId}:${toString settings.groupId} -- ${lib.escapeShellArg "${settings.directory}/config/jellyseerr"}";
          restartTriggers = [ ../../images/jellyseerr ];
        };
        arr-download-cleanup.bindsTo = lib.optional (settings.dataMountUnit != null) settings.dataMountUnit;
      }
    ];
  };
}
