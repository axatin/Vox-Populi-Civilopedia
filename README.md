# Vox Populi Civilopedia

This repository contains the files for an online version of the Civilopedia of the mod "Vox Populi" (https://forums.civfanatics.com/forums/community-patch-project.497/, https://github.com/LoneGazebo/Community-Patch-DLL) for Firaxis' Civilization V. The online Civilopedia can be accessed at axatin.github.io/Vox-Populi-Civilopedia. The folder "ExportCivilopedia" contains the scripts used to generate the html files from the game data.

## How to generate the Civilopedia files

1. Install the latest version of Vox Populi and make sure the version number in Text/en_US/UI.json matches the VP version number.
2. Copy "ExportCivilopedia" to your mods folder and start a game of Civ5 with VP and the mod "Export Civilopedia" enabled. Make sure logging is turned on.
3. After clicking on "Begin your Journey", the game data will be written to the lua log (Documents/My Games/Sid Meier's Civilization 5/Logs/Lua.log)
4. Run `python extract_from_log.py`. This script will export the data from the lua log into a file "civilopedia_export.json"
5. The icons in the Civilopedia are not updated automatically. If any of the icon atlases have changed, you need to manually copy them from "Community-Patch-DLL/(2) Vox Populi/Assets/Atlases" into the "Atlases" folder of this repo.
6. Like the regular icons, the font icons in the Civilopedia are not updated automatically. If any of the font icon atlases have changed, you need to manually copy the relevant .ggxml and .dds files into the "FontIcons" folder of this repo.
7. In ExportCivilopedia: run `pip install -r requirements.txt` and `python generate_civilopedia.py`. That script will extract all images from the atlases in "Atlases" and generate the HTML files for the online civilopedia based on the content of "civilopedia_export.json"
8. Open `generated_files/index.html` in your browser to inspect the results.