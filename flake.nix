{
  description = "Opinionated Docker media stack and declarative Nix deployment";
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.11";
    home-manager.url = "github:nix-community/home-manager/release-25.11";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
  };
  outputs =
    {
      self,
      nixpkgs,
      home-manager,
    }:
    {
      nixosModules.default = {
        imports = [
          home-manager.nixosModules.home-manager
          ./nix/nixos
        ];
      };
      homeManagerModules.default = ./nix/modules/stack/arr-stack-home-manager.nix;
      checks = nixpkgs.lib.genAttrs [ "x86_64-linux" "aarch64-linux" ] (
        system:
        import ./nix/checks.nix {
          pkgs = nixpkgs.legacyPackages.${system};
          inherit (nixpkgs.lib) nixosSystem;
          stackModule = self.nixosModules.default;
        }
      );
    };
}
