{
  pkgs,
  stackModule,
  nixosSystem,
}:
let
  system = nixosSystem {
    system = pkgs.stdenv.hostPlatform.system;
    modules = [
      stackModule
      {
        system.stateVersion = "25.11";
        users.users.media = {
          isNormalUser = true;
          home = "/home/media";
          group = "users";
          uid = 2000;
        };
        home-manager.useGlobalPkgs = true;
        hardware.nvidia-container-toolkit.enable = true;
        home-manager.users.media.home.stateVersion = "25.11";
        services.arrStack = {
          enable = true;
          user = "media";
          bindAddress = "192.0.2.10";
          secrets = builtins.listToAttrs (
            map
              (name: {
                inherit name;
                value.file = "/run/secrets/${name}";
              })
              [
                "jellyfinApiKey"
                "qbittorrentPassword"
                "bazarrPassword"
                "radarrPassword"
                "sonarrPassword"
                "prowlarrPassword"
              ]
          );
        };
      }
    ];
  };
  configuration = system.config;
  home = configuration.home-manager.users.media;
  compose = home.home.file."arr-stack/docker-compose.yml".source;
  environment = pkgs.writeText "arr-check.env" home.home.file."arr-stack/.env".text;
  desiredState =
    configuration.systemd.services.arr-config-provisioner.environment.ARR_PROVISIONER_DESIRED_STATE_DIR;
  services = configuration.systemd.services;
  alwaysOnApply = services.arr-stack-front-ends-compose.serviceConfig.ExecStart;
in
{
  deployment =
    assert configuration.systemd.services.arr-download-cleanup.serviceConfig.User == "media";
    assert configuration.custom.arrStackOnDemandSupervisor.keepChainAlwaysOn;
    assert configuration.hardware.nvidia-container-toolkit.enable;
    assert configuration.services.arrStack.hardwareAcceleration == "cpu";
    assert configuration.services.arrStack.userId == 2000;
    assert pkgs.lib.hasInfix "chown -R 2000:100"
      configuration.systemd.services.arr-stack-front-ends-compose.preStart;
    assert !(configuration.systemd.services ? jellyseerr-email-notifications);
    assert !(configuration.systemd.services ? miwayomi-extension-repositories);
    assert configuration.systemd.services.arr-stack-front-ends-compose.serviceConfig.ExecStart != "";
    assert !(configuration.systemd.services ? arr-stack-drive-guard);
    assert
      configuration.systemd.services.jellyfin-library-access-provisioner.environment.ARR_USERS_LIBRARY_ROOT
      == "/media";
    assert builtins.elem "arr-stack-front-ends-compose.service"
      services.jellyseerr-account-permission-provisioner.after;
    assert builtins.elem "arr-stack-front-ends-compose.service" services.arr-download-cleanup.after;
    pkgs.runCommand "arr-stack-deployment-check" { nativeBuildInputs = [ pkgs.docker-compose ]; } ''
      docker-compose --file ${compose} --env-file ${environment} config --quiet
      test -f ${desiredState}/prowlarr/indexer.json
      test -f ${desiredState}/sonarr/notification.json
      test -f ${desiredState}/radarr/notification.json
      grep -q -- "up --detach --wait --wait-timeout" ${alwaysOnApply}
      grep -q -- " qbittorrent" ${alwaysOnApply}
      cp ${compose} "$out"
    '';
}
