# DeimosGuider

## Requirements

* Python 3 (Ananconda is recommended)
* astropy
* Pillow (conda install pillow)

## Installation

git clone https://github.com/KeckObservatory/DeimosGuider.git

## Usage

Create a directory with your .out files from dsimulator (e.g. masks)

cd masks

python <path_to_DeimosGuider>/deimos_guider_dss.py *.out

You can open your newly created web page with:

open guider_images.html

## Note for Mac OS X Catalina users

If you get the following error:
xcrun: error: invalid active developer path (/Library/Developer/CommandLineTools), missing xcrun at: /Library/Developer/CommandLineTools/usr/bin/xcrun

parts of the Developer Tools are missing.
The problem can be fixed by executing the following command:

xcode-select --install



