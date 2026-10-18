{
  pkgs,
  lib,
  settings,
}:
let
  source = ../../..;
  yamlPython = pkgs.python3.withPackages (packages: [ packages.pyyaml ]);
  renderingSettings = pkgs.writeText "arr-compose-settings.json" (
    builtins.toJSON {
      inherit (settings) bindAddress hardwareAcceleration containerCgroupParent;
    }
  );
  compose = pkgs.runCommand "arr-stack-compose.yml" { } ''
    ${yamlPython}/bin/python3 ${./render_compose.py} ${source}/compose.yaml ${renderingSettings} > "$out"
  '';
  jellyseerrBuildContext = lib.cleanSource (source + /images/jellyseerr);
  miwayomiBuildContext = lib.cleanSource (source + /images/miwayomi);
  environment = {
    PUID = toString settings.userId;
    PGID = toString settings.groupId;
    TZ = settings.timezone;
    ARR_CONFIG_ROOT = "${settings.directory}/config";
    ARR_DATA_ROOT = "${settings.directory}/data";
    ARR_BIND_ADDR = settings.bindAddress;
    JELLYFIN_PUBLIC_URL = settings.jellyfinPublicUrl;
    READMEABOOK_PUBLIC_URL = settings.readmeabookPublicUrl;
    JELLYSEERR_EMAIL_BUILD_CONTEXT = toString jellyseerrBuildContext;
    JELLYSEERR_EMAIL_IMAGE_VERSION = builtins.hashString "sha256" (toString jellyseerrBuildContext);
    MIWAYOMI_BUILD_CONTEXT = toString miwayomiBuildContext;
    MIWAYOMI_WEB_CACHE_VERSION = builtins.hashString "sha256" (
      builtins.readFile (miwayomiBuildContext + /miwayomi-interface-artwork.patch)
      + builtins.readFile (miwayomiBuildContext + /miwayomi-subtitle-tracks.patch)
    );
    MIWAYOMI_GATEWAY_CONFIG_PATH = toString (miwayomiBuildContext + /gateway.conf);
  };
in
{
  inherit compose;
  environmentText =
    lib.concatStringsSep "\n" (lib.mapAttrsToList (name: value: "${name}=${value}") environment) + "\n";
}
