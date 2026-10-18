{ config, lib, ... }:
let
  settings = config.services.arrStack;
  configurationDirectories = [
    "qbittorrent"
    "prowlarr"
    "sonarr"
    "radarr"
    "bazarr"
    "jellyfin"
    "jellyseerr"
    "suwayomi"
    "miwayomi"
    "miwayomi-update-disabled"
    "flaresolverr"
    "audiobookshelf"
    "audiobookshelf-metadata"
    "readmeabook/config"
    "readmeabook/cache"
    "readmeabook/pgdata"
    "readmeabook/redis"
  ];
  dataDirectories = [
    "torrents"
    "torrents/audiobooks"
    "media/tv"
    "media/movies"
    "media/tv-private"
    "media/movies-private"
    "manga/mangas"
    "audiobooks"
  ];
  directories =
    map (path: "${settings.directory}/config/${path}") configurationDirectories
    ++ map (path: "${settings.directory}/data/${path}") dataDirectories;
in
{
  config = lib.mkIf settings.enable {
    assertions = [
      {
        assertion = lib.hasPrefix "${config.home.homeDirectory}/" settings.directory;
        message = "services.arrStack.directory must be inside the configured user home.";
      }
    ];
    home.activation.createArrStackPersistenceDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] (
      lib.concatMapStringsSep "\n" (
        directory: "$DRY_RUN_CMD mkdir -p $VERBOSE_ARG ${lib.escapeShellArg directory}"
      ) directories
    );
  };
}
