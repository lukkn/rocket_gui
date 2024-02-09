#!/bin/bash

#install homebrew if the user doesn't have it yet
brew -h || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

#install required dependencies for MOTESOFT
brew install pygobject3 gtk+3