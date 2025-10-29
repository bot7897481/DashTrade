{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.setuptools
    pkgs.python311Packages.wheel

    # Add Python packages here (built directly into the environment)
    pkgs.python311Packages.streamlit
    pkgs.python311Packages.bcrypt
    pkgs.python311Packages.psycopg2
    pkgs.python311Packages.pandas
    pkgs.python311Packages.yfinance
    pkgs.python311Packages.plotly
  ];
}
