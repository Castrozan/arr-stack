{ config, lib, ... }:
let
  settings = config.services.arrStack;
  secret = name: settings.secrets.${name}.file or "";
  homeUnit = "home-manager-${settings.user}.service";
  stack = settings.directory;
  alwaysOnStackUnits = [
    "arr-stack-front-ends-compose.service"
  ]
  ++ lib.optional (
    settings.dataMountUnit != null && settings.dataDeviceUnit != null
  ) "arr-stack-drive-guard.service";
  downloadChainStackUnits = lib.optionals settings.keepChainAlwaysOn alwaysOnStackUnits;
in
{
  config = lib.mkIf settings.enable {
    custom = {
      arrMediaTailscaleFunnel = {
        enable = true;
        funnels = [ ];
      };
      arrStackOnDemandSupervisor = {
        enable = true;
        stackHomeDirectory = stack;
        inherit (settings) keepChainAlwaysOn;
        diskGuard = {
          path = "${stack}/data";
          alertSmtpUsername = settings.smtp.username;
          alertEmailSender = settings.smtp.sender;
          alertEmailRecipient = settings.smtp.recipient;
          alertAppPasswordSecretFile = secret "smtpPassword";
        };
        mountGuard = {
          enable = settings.dataMountUnit != null && settings.dataDeviceUnit != null;
          dataDeviceUnit = if settings.dataDeviceUnit == null then "" else settings.dataDeviceUnit;
          dataMountUnit = if settings.dataMountUnit == null then "" else settings.dataMountUnit;
          composeDeclarationProviderUnits = [ homeUnit ];
          composeApplicatorPredecessorUnits = [ "miwayomi-compose.service" ];
          frontEndServices = [
            "jellyfin"
            "jellyseerr"
            "suwayomi"
            "miwayomi"
            "miwayomi-gateway"
            "flaresolverr"
            "audiobookshelf"
            "readmeabook"
          ];
        };
      };
      miwayomi = {
        enable = true;
        stackHomeDirectory = stack;
        baseUrl = "http://${settings.bindAddress}:4568";
        repositoryListSecretFile = secret "extensionRepositories";
        inherit (settings) removedExtensionPackages;
        composePredecessorUnits = lib.optional (
          settings.dataMountUnit != null
        ) "arr-stack-drive-guard.service";
      };
      jellyseerrEmailNotifications = {
        enable = secret "smtpPassword" != "";
        jellyseerrSettingsFile = "${stack}/config/jellyseerr/settings.json";
        senderAddress = settings.smtp.sender;
        smtpUsername = settings.smtp.username;
        appPasswordSecretFile = secret "smtpPassword";
        notificationTypesBitmask = 142;
      };
      arrConfigProvisioner = {
        enable = true;
        stackHomeDirectory = stack;
        qbittorrentPasswordSecretFile = secret "qbittorrentPassword";
        samaritanoApiKeySecretFile = secret "samaritanoApiKey";
        inherit (settings) loginUsername;
        radarrPasswordSecretFile = secret "radarrPassword";
        sonarrPasswordSecretFile = secret "sonarrPassword";
        prowlarrPasswordSecretFile = secret "prowlarrPassword";
        downloadChainProviderUnits = downloadChainStackUnits;
      };
      arrDownloadCleanup = {
        enable = true;
        stackHomeDirectory = stack;
        qbittorrentPasswordSecretFile = secret "qbittorrentPassword";
        jellyfinApiKeySecretFile = secret "jellyfinApiKey";
        downloadChainProviderUnits = downloadChainStackUnits;
      };
      jellyfinLibraryAccessProvisioner = {
        enable = true;
        jellyfinApiKeySecretFile = secret "jellyfinApiKey";
        libraryPathProviderUnits = [ homeUnit ];
      };
      jellyfinSubtitleExtractionWarmer = {
        enable = true;
        jellyfinApiKeySecretFile = secret "jellyfinApiKey";
        jellyfinDataDirectory = "${stack}/config/jellyfin/data/data";
      };
      jellyseerrAccountPermissionProvisioner = {
        enable = true;
        jellyfinApiKeySecretFile = secret "jellyfinApiKey";
        jellyseerrSettingsFile = "${stack}/config/jellyseerr/settings.json";
        serviceProviderUnits = alwaysOnStackUnits;
        orderedBeforeUnits = [ "jellyseerr-private-request-routing-provisioner.service" ];
      };
      jellyseerrPrivateRequestRoutingProvisioner = {
        enable = true;
        jellyfinApiKeySecretFile = secret "jellyfinApiKey";
        jellyseerrSettingsFile = "${stack}/config/jellyseerr/settings.json";
        rootFolderProviderUnits = [ "arr-config-provisioner.service" ];
      };
      bazarrAuthProvisioner = {
        enable = true;
        configFile = "${stack}/config/bazarr/config/config.yaml";
        containerName = "arr-bazarr";
        inherit (settings) loginUsername;
        passwordSecretFile = secret "bazarrPassword";
      };
      audiobookProvisioner = {
        enable = secret "audiobookshelfPassword" != "" && secret "readmeabookPassword" != "";
        audiobookshelfBaseUrl = "http://${settings.bindAddress}:13378";
        readmeabookBaseUrl = "http://${settings.bindAddress}:3030";
        prowlarrBaseUrl = "http://${settings.bindAddress}:9696";
        prowlarrConfigFile = "${stack}/config/prowlarr/config.xml";
        passwordFile = secret "audiobookshelfPassword";
        downloadPasswordFile = secret "qbittorrentPassword";
        readmeabookPasswordFile = secret "readmeabookPassword";
        username = settings.loginUsername;
      };
    };
  };
}
