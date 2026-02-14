name: Build APK
on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          sudo apt update
          sudo apt install -y git zip unzip autoconf autotools-dev libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
          pip install --upgrade pip
          pip install buildozer
          pip install Cython==0.29.33

      - name: Build with Buildozer
        run: |
          # Δημιουργία spec αν λείπει (προσοχή: είναι καλύτερο να έχεις το δικό σου)
          buildozer android debug
        continue-on-error: false

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: SubReminder-APK
          path: bin/*.apk
