# To learn more about how to use Nix to configure your environment
# see: https://firebase.google.com/docs/studio/customize-workspace
{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-24.05"; # or "unstable"

  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.virtualenv
  ];

  # Sets environment variables in the workspace
  env = {};
  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      "ms-python.python"
      "ms-toolsai.jupyter"
    ];

  workspace = {
      onCreate = {
        # This script creates a virtual environment (.venv) and installs dependencies from requirements.txt
        create-venv = ''
          python -m venv --system-site-packages .venv
          source .venv/bin/activate
          pip install --no-cache-dir -r requirements.txt
        '';
      };
      onStart = {
        # 2. Create a CLEAN virtual environment (no --system-site-packages)
        # This ensures pip installs everything into a writable folder.
        setup-env = "python3 -m venv --system-site-packages .venv && source .venv/bin/activate && pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt";
      };
    };
  };
}