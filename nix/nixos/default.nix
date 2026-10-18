{ config, lib, ... }:
let
  settings = config.services.arrStack;
in
{
  imports = [
    ./options.nix
    ./application-configuration.nix
    ./deployment.nix
    ../modules/miwayomi/miwayomi-nixos.nix
    ../modules/tailscale-funnel/arr-media-tailscale-funnel-nixos.nix
    ../modules/login-rate-limit-proxy/arr-media-login-ratelimit-proxy-nixos.nix
    ../modules/on-demand-supervisor/arr-stack-on-demand-supervisor-nixos.nix
    ../modules/jellyseerr-notifications/jellyseerr-notifications-nixos.nix
    ../modules/configuration/arr-config-provisioner-nixos.nix
    ../modules/configuration/download-cleanup/arr-download-cleanup-nixos.nix
    ../modules/configuration/audiobooks/audiobook-provisioner-nixos.nix
    ../modules/bazarr-auth/bazarr-auth-provisioner-nixos.nix
    ../modules/library-access/jellyfin/jellyfin-library-access-provisioner-nixos.nix
    ../modules/jellyfin-subtitle-extraction/jellyfin-subtitle-extraction-warmer-nixos.nix
    ../modules/jellyseerr-account-permissions/jellyseerr-account-permission-provisioner-nixos.nix
    ../modules/jellyseerr-private-request-routing/jellyseerr-private-request-routing-provisioner-nixos.nix
    ../modules/extension-repositories/suwayomi-extension-repositories-nixos.nix
  ];
  config = lib.mkIf settings.enable {
    assertions = [
      {
        assertion = (settings.dataMountUnit == null) == (settings.dataDeviceUnit == null);
        message = "services.arrStack.dataMountUnit and dataDeviceUnit must be configured together.";
      }
    ];
    virtualisation.docker.enable = true;
    users.users.${settings.user}.extraGroups = [ "docker" ];
    hardware.nvidia-container-toolkit.enable = settings.hardwareAcceleration == "nvidia";
    home-manager.users.${settings.user} = {
      imports = [ ../modules/stack/arr-stack-home-manager.nix ];
      services.arrStack = {
        enable = true;
        inherit (settings)
          directory
          bindAddress
          timezone
          userId
          groupId
          accounts
          hardwareAcceleration
          containerCgroupParent
          jellyfinPublicUrl
          readmeabookPublicUrl
          publicRequesterUsername
          ;
        jellyfinApiKeyFile = settings.secrets.jellyfinApiKey.file;
      };
    };
  };
}
