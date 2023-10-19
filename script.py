import subprocess
import os
import sys
import re

def print_line(opcode, operands):
    return opcode + " "*(11-len(opcode)) + operands

def main():
    file = sys.argv[1]
    version = -1
    while (version not in {0,1,2}):
        version = int(input("Which title is " + file + "?:\n[0] Splatoon (AGMX01) (v288, latest patch) \n[1] Splatoon (AGMX01) (v272) \n[2] Splatoon Testfire (AGGX01)\n"))
        if (version not in {0,1,2}):
            print("Invalid selection. Try again.\n")
    print("Converting rpx to elf...")
    comm = subprocess.run(["./rpl2elf", file, "Gambit"])
    if (comm.returncode != 0):
        print("rpl2elf not found.")
        return

    print("Dumping .text section...")
    with open("dump", "w+") as outfile:
        comm = subprocess.run(["readelf", "-x", "2", "Gambit"], stdout=outfile)
    os.remove("Gambit")
    if (comm.returncode != 0):
        print("An error occurred.")
        return

    with open("dump", "r") as infile:
        file = infile.readlines()
    os.remove("dump")

    newfile = ""
    for line in file:
        match = False
        if (line.isspace()):
            continue
        columns = line.split()
        if (columns[0][0] != '0'):
            continue
        start_address = int(columns[0], 16)
        for i in range(0,4):
            address = start_address + 0x4*i
            if (version == 0):
                start = 0x029f6c10
            if (version == 1):
                start = 0x029f6bd0
            if (version == 2):
                start = 0x02946360
            end = start + 0x8f0
            if ((address >= start) and (address <= end)):
                match = True
                newfile += columns[i+1]
        if (match == True):
            newfile += "\n"

    with open("bytecode", "w") as outfile:
        comm = subprocess.run(["xxd", "-r", "-p"], input=newfile, stdout=outfile, text=True)
    if (comm.returncode != 0):
        print("An error occurred.")
        os.remove("bytecode")
        return

    print("Disassembling camera functions...")

    with open("camera_functions", "w") as outfile:
        comm = subprocess.run(["powerpc-linux-gnu-objdump", "-b", "binary", "-m", "powerpc:750", "bytecode", "-D", "-EB"], stdout=outfile)
    os.remove("bytecode")
    if (comm.returncode != 0):
        print("An error occurred.")
        return

    file = open("camera_functions", "r").readlines()
    os.remove("camera_functions")

    scratch = """[MK8Freecam]
moduleMatches = 0x9f0a90b7

; enables Nintendo's freecam in Mario Kart 8
; Controls: left stick button to enable/disable; R to zoom out, L to zoom in, left stick to rotate camera, right stick to control camera position

; hooks
0x027b9f54 = ba agl_lyr_Layer_initialize_
0x027b7e2c = bla set_freecam_params
0x027ba0f4 = bla set_flags

; writes
0x0279dfc4 = rlwinm. r10,r0,0,26,26         ; zoom in with L button rather than (+)

; common functions
0x02721904 = malloc:
0x027b94b4 = agl_lyr_Layer_updateDebugInfo_:
0x027d26b0 = agl_lyr_RenderStep_RenderStep:
0x0273d360 = sead_HeapMgr_getCurrentHeap:
0x02736de0 = sead_PerspectiveProjection_PerspectiveProjection:
0x027377e8 = sead_DirectProjection_DirectProjection:
0x02737100 = sead_OrthoProjection_OrthoProjection:
0x0274c304 = sead_CriticalSection_CriticalSection:
0x02677cfc = ASM_MTXCopy:

; constants                                 ; may need to edit this depending on your setup
controllerPtr = 0x1E572D94                  ; do a memory search to find the address for the last (or current) button held, then subtract 0x10c
                                            ; button values: https://wut.devkitpro.org/group__vpad__input.html
; rodata/data accesses
ADDR_10100e18 = 0x10100e18
ADDR_10100e40 = 0x10100e40
ADDR_10127ab0 = 0x10127ab0
ADDR_10127ab8 = 0x10127ab8
ADDR_10127ad0 = 0x10127ad0
ADDR_10127b38 = 0x10127b38
ADDR_10127b98 = 0x10127b98
ADDR_1018c7ec = 0x1018c7ec
ADDR_10205a70 = 0x10205a70
ADDR_10205f78 = 0x10205f78
ADDR_10205f9c = 0x10205f9c

.origin = codecave
freecamEnabled:
.int 0

; initialize nullptr
nullpointer:
.int 0
ADDR_10206238:
.long nullpointer

; float initialization variables
DAT_10147528:
.float 1
DAT_1014752c:
.float 10
DAT_10147530:
.float 0.01
DAT_10147534:
.float 1000
DAT_10147538:
.float 45
DAT_1014753c:
.float 1.77777778
DAT_10147540:
.float 0.1

set_freecam_params:
lis        r7,controllerPtr@h
ori        r7,r7,controllerPtr@l
lis        r5,freecamEnabled@ha
lwz        r6,freecamEnabled@l(r5)
lwz        r10,0x110(r7)
rlwinm.    r10,r10,0,13,13
beq        setEnabledStatus
xori       r6,r6,1
setEnabledStatus:
stw        r6,freecamEnabled@l(r5)
stw        r7,0x1198(r28)
li         r7,0x1
stw        r7,0x1194(r28)
blr

set_flags:
lwz        r12,0x80(r29)
lis        r9,freecamEnabled@ha
lwz        r9,freecamEnabled@l(r9)
cmpwi      r9,0x1
lwz        r9,0x50(r29)
bne        disableFreecam
ori        r9,r9,0xc8
b          storeBits
disableFreecam:
rlwinm     r9,r9,0,29,27
rlwinm     r9,r9,0,26,23
storeBits:
stw        r9,0x50(r29)
blr

agl_lyr_Layer_DebugInfo_DebugInfo:
"""

    codelines = []
    label_list = []

    for num, line in enumerate(file):
        if (num <= 6):
            continue
        num -= 7
        instruction = re.search(r':\s\S\S\s\S\S\s\S\S\s\S\S\s*(\S*)\s*(.*)',line)
        opcode = instruction.group(1)
        operands = instruction.group(2)

        # labels
        if (opcode in ['b','bne-','bne+','beq','beq-','blt','blt-','bgt','bgt-','ble','ble-','bge','bge-','bdnz+']):
            branch_loc = int(operands, 16)//4
            operands = "line_" + str(branch_loc)
            label_list.append(branch_loc)

        if (opcode == 'bl' and version == 0):
            match operands:
                case '0xffed6de0':
                    operands = "malloc"
                case '0xfffff554':
                    operands = "agl_lyr_Layer_updateDebugInfo_"
                case '0x2018':
                    operands = "agl_lyr_RenderStep_RenderStep"
                case '0xffefc288':
                    operands = "sead_HeapMgr_getCurrentHeap"
                case '0xffef16a8':
                    operands = "sead_PerspectiveProjection_PerspectiveProjection"
                case '0xffef23a0':
                    operands = "sead_DirectProjection_DirectProjection"
                case '0xffef1b7c':
                    operands = "sead_OrthoProjection_OrthoProjection"
                case '0xfff0c24c':
                    operands = "sead_CriticalSection_CriticalSection"
                case '0x33deb0':
                    operands = "ASM_MTXCopy"
                case '0x3df060':
                    operands = "import.coreinit.OSBlockSet"
                case '0x3df058':
                    operands = "import.coreinit.OSBlockMove"

        if (opcode == 'bl' and version == 1):
            match operands:
                case '0xffed6df0':
                    operands = "malloc"
                case '0xfffff554':
                    operands = "agl_lyr_Layer_updateDebugInfo_"
                case '0x2018':
                    operands = "agl_lyr_RenderStep_RenderStep"
                case '0xffefc298':
                    operands = "sead_HeapMgr_getCurrentHeap"
                case '0xffef16b8':
                    operands = "sead_PerspectiveProjection_PerspectiveProjection"
                case '0xffef23b0':
                    operands = "sead_DirectProjection_DirectProjection"
                case '0xffef1b8c':
                    operands = "sead_OrthoProjection_OrthoProjection"
                case '0xfff0c24c':
                    operands = "sead_CriticalSection_CriticalSection"
                case '0x33dde8':
                    operands = "ASM_MTXCopy"
                case '0x3defa0':
                    operands = "import.coreinit.OSBlockSet"
                case '0x3def98':
                    operands = "import.coreinit.OSBlockMove"

        if (opcode == 'bl' and version == 2):
            match operands:
                case '0xffed7c90':
                    operands = "malloc"
                case '0xfffff554':
                    operands = "agl_lyr_Layer_updateDebugInfo_"
                case '0x2018':
                    operands = "agl_lyr_RenderStep_RenderStep"
                case '0xffefd138':
                    operands = "sead_HeapMgr_getCurrentHeap"
                case '0xffef2558':
                    operands = "sead_PerspectiveProjection_PerspectiveProjection"
                case '0xffef3250':
                    operands = "sead_DirectProjection_DirectProjection"
                case '0xffef2a2c':
                    operands = "sead_OrthoProjection_OrthoProjection"
                case '0xfff0d0bc':
                    operands = "sead_CriticalSection_CriticalSection"
                case '0x351a6c':
                    operands = "ASM_MTXCopy"
                case '0x3f2c50':
                    operands = "import.coreinit.OSBlockSet"
                case '0x3f2c48':
                    operands = "import.coreinit.OSBlockMove"

        # code fixes
        match num:
            case 20:
                operands = "r12,ADDR_10127ab0@ha"
            case 22:
                operands = "r9,DAT_1014752c@ha"
            case 23:
                operands = "f29,ADDR_10127ab0@l(r12)"
            case 24:
                operands = "r29,ADDR_10100e40@ha"
            case 25:
                operands = "r28,ADDR_10100e18@ha"
            case 27:
                operands = "r29,r29,ADDR_10100e40@l"
            case 28:
                operands = "r11,DAT_10147528@ha"
            case 29:
                operands = "r27,ADDR_10205a70@ha"
            case 30:
                operands = "f31,DAT_1014752c@l(r9)"
            case 31:
                operands = "r28,r28,ADDR_10100e18@l"
            case 32:
                operands = "r27,r27,ADDR_10205a70@l"
            case 33:
                operands = "f30,DAT_10147528@l(r11)"
            case 187:
                operands = "r12,DAT_10147530@ha"
            case 188:
                operands = "f1,DAT_10147530@l(r12)"
            case 190:
                operands = "r8,DAT_10147534@ha"
            case 192:
                operands = "f1,DAT_10147534@l(r8)"
            case 194:
                operands = "r12,DAT_10147538@ha"
            case 196:
                operands = "f0,DAT_10147538@l(r12)"
            case 206:
                operands = "r10,DAT_1014753c@ha"
            case 208:
                operands = "f13,DAT_1014753c@l(r10)"
            case 232:
                operands = "r6,DAT_10147540@ha"
            case 233:
                operands = "f1,DAT_10147540@l(r6)"
            case 237:
                operands = "line_262"
            case 238:
                operands = "r3,8"
            case 241:
                operands = "line_264"
            case 289:
                operands = "r6,ADDR_10127b98@ha"
            case 290:
                opcode = "li"
                operands = "r0,0"
            case 291:
                operands = "r6,r6,ADDR_10127b98@l"
            case 296:
                operands = "r12,ADDR_10127ad0@ha"
            case 298:
                operands = "r12,r12,ADDR_10127ad0@l"
            case 303:
                opcode = "li"
                operands = "r0,0"
            case 304:
                operands = "r6,ADDR_10127b98@ha"
            case 306:
                operands = "r6,r6,ADDR_10127b98@l"
            case 310:
                operands = "r0,ADDR_10127b98@ha"
            case 311:
                operands = "r0,r0,ADDR_10127b98@l"
            case 317:
                operands = "r8,ADDR_10205f78@ha"
            case 318:
                operands = "f0,ADDR_10205f78@l(r8)"
            case 321:
                operands = "r6,ADDR_10205f9c@ha"
            case 324:
                operands = "r6,r6,ADDR_10205f9c@l"
            case 402:
                operands = "r3,ADDR_1018c7ec@ha"
            case 403:
                operands = "r3,ADDR_1018c7ec@l(r3)"
            case 486:
                operands = "r26,r26,ADDR_10127ab8@l"
            case 503:
                operands = "r12,ADDR_10127ad0@ha"
            case 506:
                operands = "r12,r12,ADDR_10127ad0@l"
            case 510:
                operands = "r0,ADDR_10127b38@ha"
            case 512:
                operands = "r0,r0,ADDR_10127b38@l"
            case 515:
                operands = "r7,ADDR_10127b98@ha"
            case 516:
                operands = "r7,r7,ADDR_10127b98@l"
            case 529:
                operands = "r12,ADDR_10206238@ha"
            case 531:
                operands = "r12,ADDR_10206238@l(r12)"

        # fix offsets greater than 0x338
        if (num >= 264):
            match = re.search(r'[\,\(](8[56789]\d|9\d\d)', operands)
            if (not(match is None)):
                operands = re.sub(match.group(1), str(int(match.group(1)) - 24), operands)

        codelines.append([opcode, operands])

    # print everything
    for num, line in enumerate(codelines):
        opcode = line[0]
        operands = line[1]
        # don't display these lines
        if (num == 234 or (num >= 242 and num < 262) or num == 283 or (num >= 461 and num < 485)):
            continue
        # skip these calls
        if (num == 166 or num == 189 or num == 193 or num == 266 or num == 537 or num == 561):
            continue
        if (num in label_list):
            scratch += "\nline_" + str(num) + ":\n"
        if (num == 387):
            scratch += "\nagl_lyr_Layer_initialize_:\n"
        if (num == 485):
            scratch += """li         r3,0x49c
bl         malloc
cmpwi      r3,0x0
bl         agl_lyr_Layer_DebugInfo_DebugInfo
stw        r3,0x80(r28)
addi       r25,r3,0x338
li         r3,0x418
bl         malloc
or         r27,r3,r3
lis        r26,ADDR_10127ab8@ha
li         r31,0x0
"""
        scratch += print_line(opcode, operands) + "\n"

    with open("Freecam/patch_freecam.asm", "w") as outfile:
        outfile.write(scratch)

    print('Wrote patch to file!')

main()