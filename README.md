# arr-stack

My opinionated media stack, extracted from Castrozan/.dotfiles and packaged with Docker Compose. Nix, systemd, Tailscale, Cloudflare, and a particular GPU are not prerequisites.

The default install runs Jellyfin for watching, Jellyseerr for requests, Sonarr and Radarr for television and films, Prowlarr for indexers, qBittorrent for downloads, and Bazarr for subtitles. A container applies the committed application settings. Another handles cleanup through authenticated lifecycle webhooks.

## Start a new server

Install Docker Engine with Compose on Linux, or Docker Desktop using Linux containers on macOS or Windows. Use Compose 2.24.4 or newer. The commands below work in a terminal or PowerShell.

```sh
git clone https://github.com/Castrozan/arr-stack.git
cd arr-stack
docker compose up -d --build --wait
docker compose run --rm manage onboard
docker compose run --rm manage credentials
```

`onboard` finishes both startup wizards, creates public and private libraries, connects Jellyseerr to the media server and download managers, and applies account permissions. It can be run again without creating duplicate users or resetting existing passwords. It expects the generated `admin` Jellyfin account; run it before completing the browser wizard yourself.

Open http://localhost:8096 to watch and http://localhost:5055 to request. Both use the Jellyfin `admin` credentials printed by the last command. The other applications have their own generated passwords. No passwords are committed or placed in Compose environment variables.

## Defaults I want to keep

- HD profiles plus PT-BR dubbed/subtitled options, original-language television, and English-caption anime preferences.
- One account per friend for watching and requesting, automatic approval, and public-library access only.
- Three simultaneous downloads, continued seeding, and authenticated cleanup after a library title is removed.
- A shared `/data` filesystem for downloads and finished media so imports can use hardlinks.
- Pinned application releases, health checks, bounded container memory, and rotating logs.

These are presets, not proof that a release contains a subtitle track. Bazarr connects to Sonarr and Radarr, applies one language profile for English and Brazilian Portuguese, and enables embedded subtitle extraction. Add external subtitle providers in Bazarr if you need subtitle downloads; additional providers are preserved. Add your own private indexers in Prowlarr. The extracted defaults contain public indexers only.

`defaults/` owns the settings reapplied by `docker compose run --rm manage configure`. Edit those files and rebuild the tools image to change persistent policy. A dashboard edit to a managed value can be overwritten by configuration. Startup also reapplies these defaults.

Create `.env` from `.env.example` if you need different ports, timezone, or container UID/GID. Defaults work without that file. Compose declares the full port mapping. To run two installations on the same Docker host, give each a different `COMPOSE_PROJECT_NAME` and host ports, including `TORRENT_PORT`.

## Friends and private libraries

```sh
docker compose run --rm manage users create friend
docker compose run --rm manage users list
docker compose run --rm manage status
```

A new friend's generated password prints once. `users --help` lists password reset, email, enable, disable, deletion, and synchronization commands. Administrator accounts cannot be deleted, disabled, or reset by the friend commands.

Edit `config/accounts.json` to name accounts allowed private libraries or advanced request options. The owner account remains Jellyseerr's administrator. Accounts outside the private-library allowlist receive only Movies and TV. Only those public libraries are synced into Jellyseerr, whose availability metadata cannot be restricted per library.

```sh
docker compose run --rm manage users sync
docker compose run --rm manage users sync-account-permissions
docker compose run --rm manage users sync-request-routing
```

The `private-requests` account routes requests to private root folders. Log in as that account to use the routing; an administrator session bypasses upstream override rules. `onboard` creates that account with a generated password; use `users reset-password private-requests` when you want to log in.

## Manga, anime, and audiobooks

Optional services use Compose profiles. You can combine profiles, or set `COMPOSE_PROFILES` in `.env` so later starts select them too.

```sh
docker compose --profile manga up -d --build --wait
docker compose --profile anime up -d --build --wait
docker compose --profile audiobooks up -d --build --wait
```

Manga uses Suwayomi; instant anime playback uses the patched Miwayomi build. Both use FlareSolverr. Configure source extension repositories and sources in those applications; those choices and source credentials are personal. The anime image builds its pinned server source on first use.

Audiobooks use ReadMeABook and Audiobookshelf. Complete their application setup and connect ReadMeABook to `qbittorrent:8080` with the generated qBittorrent credentials. Set downloads under `/data/torrents/audiobooks` and the library under `/data/audiobooks`. Their accounts are separate from Jellyfin.

## Storage, updates, and remote access

Application state, generated credentials, and media live in Docker named volumes. This keeps database permissions and hardlinks inside Docker's Linux filesystem on macOS and Windows. `docker compose down` keeps those volumes. Adding `-v` deletes them, including media and credentials.

For a Linux host using an existing data disk, choose it before the first start: set `ARR_DATA_DIRECTORY` to an existing absolute directory and use `docker compose -f compose.yaml -f compose.storage.yaml` for every command. Keep downloads and libraries under that one directory on a filesystem that supports hardlinks. Changing the storage driver after installation requires a backup and explicit data migration; the override does not move existing media.

Back up every project volume with writers stopped, including `state` and `cleanup-state`. The initializer refuses to generate replacement credentials when application configuration exists but the credential volume is missing. This repository does not import an existing Nix installation automatically.

```sh
git pull --ff-only
docker compose pull --ignore-buildable
docker compose up -d --build --wait
docker compose run --rm manage onboard
```

Web ports bind to loopback by default. To serve friends on another device, set `ARR_BIND_ADDR` to an appropriate host interface and provide your own HTTPS reverse proxy or private network. Set `JELLYFIN_PUBLIC_URL` to the browser-facing Jellyfin URL for available-media email links, and configure SMTP in Jellyseerr. Suwayomi and Miwayomi have no application login; remote access to those services needs an authentication boundary.

CPU playback/transcoding is the baseline. Linux hosts with the NVIDIA Container Toolkit can add `-f compose.nvidia.yaml` after `-f compose.yaml`, then select NVIDIA NVENC in Jellyfin. Hardware passthrough on Docker Desktop is outside this preset.

Each server is independent. Shared-library replication and automatically selecting the nearest house's server require a separate design.

## NixOS integration

The flake exports `nixosModules.default` and `homeManagerModules.default`. The NixOS module wraps the same Compose services, images, and application defaults with systemd supervision, drive protection, provisioning, and host CLI tools. Docker remains the application runtime.

Add the input to your system flake and import its module:

```nix
{
  inputs.arr-stack = {
    url = "github:Castrozan/arr-stack";
    inputs.nixpkgs.follows = "nixpkgs";
    inputs.home-manager.follows = "home-manager";
  };
}
```

```nix
{ inputs, config, ... }:
{
  imports = [ inputs.arr-stack.nixosModules.default ];

  services.arrStack = {
    enable = true;
    user = "media";
    loginUsername = "admin";
    secrets = {
      jellyfinApiKey.file = config.age.secrets.jellyfin-api-key.path;
      qbittorrentPassword.file = config.age.secrets.qbittorrent-password.path;
      radarrPassword.file = config.age.secrets.radarr-password.path;
      sonarrPassword.file = config.age.secrets.sonarr-password.path;
      prowlarrPassword.file = config.age.secrets.prowlarr-password.path;
      bazarrPassword.file = config.age.secrets.bazarr-password.path;
    };
  };
}
```

Declare the existing user and its Home Manager configuration in your host flake. The module imports Home Manager's NixOS integration. Supply runtime secret paths through your secret manager; secret contents never belong in Nix expressions. An optional `source` beside each secret's `file` accepts the encrypted source so secret changes restart the matching provisioner.

The Nix deployment uses bind mounts under the user's `arr-stack/config` and `arr-stack/data` directories. It preserves the original Nix layout, including Jellyfin's `/media` mount, and does not run Docker's credential initializer or onboarding. Existing installations retain their databases, accounts, credentials, and library IDs. For a fresh Nix installation, complete Jellyfin and Jellyseerr's setup and supply the administrative API key before account reconciliation can succeed. Standalone Docker volumes require an explicit state migration before switching deployment modes.

`services.arrStack` exposes the host directory, bind address, UID/GID, account allowlists, browser URLs, optional NVIDIA access, SMTP settings, and removable-drive units. See `nix/nixos/options.nix` for the interface. HTTPS origins, tunnel routing, encrypted secrets, and host storage remain host configuration.

## Verification and provenance

```sh
docker build --target tests -t arr-stack-tests .
docker run --rm arr-stack-tests
```

CI validates the Nix deployment and its native automation, then validates Compose and runs isolated Linux smoke installations, including onboarding, a friend account, repeated configuration, hardlinks, and restart persistence. macOS and Windows use the same Linux containers; native Docker Desktop execution needs separate verification.

The extracted application settings, Python automation, Nix services, and image customizations originate in https://github.com/Castrozan/.dotfiles/tree/9f9157b56298d2c6fab36a2e0835236d3127673e/machine-configuration/media/arr-stack. Personal account allowlists, domain names, VPN configuration, and secret values stay in the consuming host configuration.

Own integration code is MIT licensed. Miwayomi patch material retains the upstream Apache-2.0 license in `images/miwayomi/LICENSE`; container applications retain their respective licenses. The local patches are carried because this preset depends on their playback, source, artwork, and progress behavior.

Docker storage reference: https://docs.docker.com/engine/storage/volumes/

Shared-filesystem reference: https://trash-guides.info/File-and-Folder-Structure/Hardlinks-and-Instant-Moves/
