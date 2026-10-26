{ pkgs }:
let
  octoberMemorySafetyFixedVersion = "1.30.6";
in
if pkgs.lib.versionAtLeast pkgs.nginxStable.version octoberMemorySafetyFixedVersion then
  pkgs.nginxStable
else
  pkgs.nginxStable.overrideAttrs {
    version = octoberMemorySafetyFixedVersion;
    src = pkgs.fetchurl {
      url = "https://nginx.org/download/nginx-${octoberMemorySafetyFixedVersion}.tar.gz";
      hash = "sha256-PPRvXtdQTUYBJYZre+qZ+zV/MdiH4uY7NVAzEOm4tsg=";
    };
  }
