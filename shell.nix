{ pkgs ? import <nixpkgs> { }
, mkPython
}:

let
  pyEnv = mkPython {
    requirements = builtins.readFile ./requirements.txt;
  };
in

with pkgs;

mkShell {
  buildInputs = [
    git

    texlive.combined.scheme-full

    pyEnv
    tinybeachthor.netlogo
  ];
}
