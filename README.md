This is a script that generates a graphics pack for Cemu to enable Nintendo's debug camera in Mario Kart 8.

# Prerequisites
In order to run this script, you need the following:
1. Gambit.rpx from Splatoon (AGMX01) or Splatoon Testfire (AGGX01). These titles contain some camera code that we need to copy into Mario Kart 8.
2. Python >=3.10
3. rpl2elf (e.g. https://github.com/Relys/rpl2elf)
4. powerpc-linux-gnu-objdump (install with e.g. sudo apt install binutils-powerpc-linux-gnu). You could also modify the script to use powerpc-eabi-objdump, if you already have devKitPPC installed on your system.

The script also invokes readelf and xxd. You'll need to run it in Linux, or in a Linux environment like WSL.

# Usage
Before running the script, copy rpl2elf and Gambit.rpx to the same directory as the script. Then run it with `python script.py [rpx file]`.

Once everything finishes up, copy the Freecam folder to Cemu/graphicPacks/MarioKart8.

# Controls
The controls are: left stick button to enable/disable; R to zoom out, L to zoom in, left stick to rotate camera, right stick to control camera position.