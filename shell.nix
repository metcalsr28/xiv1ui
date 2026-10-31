# Tooling for generating xiv1ui textures (nix-shell --run 'python3 tools/...').
{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = [ pkgs.luajit (pkgs.python3.withPackages (p: [ p.pillow p.numpy p.fonttools ])) ];
}
