from flore1 import *
import time
import copy

fix_color()
show_logo(3)

colors_bm = []

string = ""
clen = ""
for c in range(0, 255):
    clen += "|"+str(c)+"|"

    string += "fc:15bc:"+str(c)+" "+str(c)+" cc:0"
    if len(clen) > 55:
        colors_bm.append(string)
        string = ""
        clen = ""

colors_asset = TextAsset(colors_bm)
colors_sprite = TextSprite(asset=colors_asset)

class TextAssetCreator:
    def __init__(self, w, h):

        if w < 16:
            w = 16
        if h < 16:
            h = 16

        self.w = w
        self.h = h

        resize_console(w*2+70, h+5)
        clear_screen()

        self.cursor_c = [
            "move cursor up", "move cursor down", "move cursor left", "move cursor right"
        ]
        self.color_c = [
            "previous font color", "next font color", "font color pipette", "previous background color",
            "next background color", "background color pipette", "add color"
        ]
        self.brush_c = [
            "previous brush", "next brush", "brush pipette", "add brush"
        ]
        self.frame_c = [
            "previous frame", "next frame", "add frame", "insert frame", "remove frame", "copy frame", "paste frame",
            "set speed", "play"
        ]
        self.paint_c = [
            "paint", "erase", "write"
        ]
        self.misc_c = [
            "save", "load", "command line mode", "manual"
        ]

        self.controls = {
            "move cursor up":["z","w"],
            "move cursor down":["s"],
            "move cursor left":["q","a"],
            "move cursor right":["d"],
            "previous brush":["m"],
            "next brush":["p"],
            "previous font color":["o"],
            "next font color":["l"],
            "previous background color":["i"],
            "next background color":["k"],
            "previous frame":["u"],
            "next frame":["j"],
            "background color pipette":["0","à"],
            "font color pipette":["9","ç"],
            "brush pipette":["8","_"],
            "add frame":["ctrl+n"],
            "remove frame":["ctrl+r"],
            "copy frame":["ctrl+x"],
            "paste frame":["ctrl+v"],
            "insert frame":["ctrl+i"],
            "set speed":["ctrl+p"],
            "play":["space"],
            "command line mode":["escape"],
            "write":["t"],
            "add brush":["ctrl+b"],
            "add color":["ctrl+o"],
            "paint":["enter"],
            "save":["ctrl+s"],
            "load":["ctrl+l"],
            "erase":["backspace"],
            "manual":["tab"]
        }
        repdel = {
            "move cursor up": 0.1,
            "move cursor down": 0.1,
            "move cursor left": 0.08,
            "move cursor right": 0.08,
            "paint": 0.025,
            "__default__": 0.2
        }

        self.input = InputHandler(keys = self.controls, delays = repdel)

        self.scene = Scene(coord_x=30, coord_y=1, res_x=self.w, res_y=self.h, layer_count=2, scale=False)
        self.palette_scene = Scene(coord_x=30, coord_y=1, res_x=32, res_y=32, layer_count=1, scale=False)

        self.palette_scene.put(colors_sprite, 1, 1, 0)

        draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)

        self.refresh = Refresh(fps = 60)
        self.frame = 0
        self.playing = False
        self.sprites = []
        self.sprites.append(TextSprite())
        self.sprites[self.frame].chart = {}
        self.sprites[self.frame].prtcrd = set()
        self.sprites[self.frame].act_prtcrd = set()

        self.cursor = TextSprite()
        self.cursor.chart = {}
        self.cursor.chart["0|0"] = ("\33[41m\33[37mX\33[0m", None, "\u001b[38;5;7m \b", None)
        self.cursor.prtcrd = {(0, 0)}
        self.cursor.act_prtcrd = {(1, 1)}

        self.scene.put(self.sprites[self.frame], 1, 1, 0)
        self.scene.put(self.cursor, 1, 1, 1)

        self.refresh.feed(self.run, *(), **{})

        self.bg_palette = [None,"\u001b[48;5;7m \b"]
        self.fc_palette = [None,"\u001b[38;5;7m \b"]
        self.font_color = 1
        self.bg_color = 0
        self.brush = 0
        self.brushes = [" "]
        self.last = {
            "crd": None,
            "time": time.time()
        }

        self.path = ""

        self.play_speed = 1/24

        self.actualize_toolbar()
        print_crd("           ", 31, self.h+2)
        print_crd("FRAME "+str(self.frame), 31, self.h+2)

        self.escape = False

        self.scene.show(repeat_color=True)

        while not self.escape:
            self.refresh.run()

    def run(self):
        def run_clear():
            clear_screen()
            self.actualize_toolbar()
            self.scene.show(force=True, repeat_color=True)

        if self.input.is_pressed("command line mode"):
            run_clear()
            cursor_to_crd(0, 9)
            save_cursor()
            self.command_line_mode()
        else:
            print_crd("> press TAB for manual", 1, 1)
            self.input_check()

    def show_toolbar(self):
        print_crd("> \33[32mBRUSHES:\33[0m\n", self.w*2+33, 1)

        i = 1
        for brush in self.brushes:
            i += 1
            string = ""
            string += "  |"+brush+"|"
            if self.brushes.index(brush) == self.brush:
                string += " \33[32m<SELECT \33[0m"

            print_crd(string, self.w*2+33, i)

        print_crd("> \33[32mCOLORS:\33[0m\n", self.w*2+48, 1)

        i = 1
        for color in self.bg_palette:
            i += 1
            string = ""
            if color == None:
                string += "  |No\33[0m|"
            else:
                string += "  |"+color+"  \33[0m|"

            if self.bg_palette.index(color) == self.bg_color:
                string += " \33[32m<BG \33[0m"
            if self.bg_palette.index(color) == self.font_color:
                string += " \33[32m<FONT \33[0m"

            print_crd(string, self.w*2+48, i)

    def actualize_cursor(self):
        brush = self.brushes[self.brush]
        bgcolor = self.bg_palette[self.bg_color]
        ftcolor = self.fc_palette[self.font_color]
        if brush == " " and bgcolor == None: brush = "\33[41m\33[37mX\33[0m"
        self.cursor.chart["0|0"] = (brush, bgcolor, ftcolor, None)
        self.scene.show(force=True, repeat_color=True)
        self.actualize_toolbar()

    def actualize_toolbar(self):
        draw_rectangle(" ", self.w*2+33, 1, self.w*2+66, self.h)
        self.show_toolbar()

    def show_controls(self):
        draw_rectangle("\033[48;5;232m \33[0m", 1, 1, 70+self.w*2, self.h+5)
        print_crd("|\33[47m\33[30mCONTROLS\33[0m|\nTAB to hide", 1, 1)
        y = 3
        x = 0
        basex = 2
        maxlen = 0
        for key in self.color_c + self.brush_c + self.frame_c + self.paint_c + self.misc_c:

            if key in self.cursor_c:
                if key == self.cursor_c[0]:
                    print_crd("CURSOR", basex+x, y+1)
                    y += 2
            elif key in self.color_c:
                if key == self.color_c[0]:
                    print_crd("COLOR", basex+x, y+1)
                    y += 2
            elif key in self.brush_c:
                if key == self.brush_c[0]:
                    print_crd("BRUSH", basex+x, y+1)
                    y += 2
            elif key in self.frame_c:
                if key == self.frame_c[0]:
                    print_crd("ANIMATION", basex+x, y+1)
                    y += 2
            elif key in self.paint_c:
                if key == self.paint_c[0]:
                    print_crd("DRAWING", basex+x, y+1)
                    y += 2
            elif key in self.misc_c:
                if key == self.misc_c[0]:
                    print_crd("MISC", basex+x, y+1)
                    y += 2

            print_crd("\33[33m"+key+": \33[0m", basex+x, y)
            x += len(key)+3

            for el in self.controls[key]:
                if el.startswith("ctrl+"):
                    print_crd("ctrl + "+el[5:], basex+x, y)
                    x += len(el)+2
                else:
                    print_crd(el, basex+x, y)
                    x += len(el)
                print_crd("\033[38;5;237m or \33[0m", basex+x, y)
                x += 4
            print_crd("   ", basex+x-4, y)
            if x > maxlen: maxlen = 0; maxlen += x
            x = 0
            y += 1

            if y > 17:
                y = 4; basex += maxlen+2
                maxlen = 0

        while not self.input.is_pressed("manual"):
            pass
        draw_rectangle("\033[48;5;232m \33[0m", 1, 1, 70+self.w*2, self.h+5)
        draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)
        self.actualize_cursor()


    def input_check(self):
        if self.playing == False:
            if self.input.is_pressed("paint"):
                if 0 < self.cursor.x <= self.w*2-1 and 0 < self.cursor.y <= self.h-1:
                    self.command_line_mode(typed="/paint")
            else:
                if self.input.is_pressed("move cursor up"):
                    self.command_line_mode(typed="/mvcurs up")
                if self.input.is_pressed("move cursor down"):
                    self.command_line_mode(typed="/mvcurs down")
                if self.input.is_pressed("move cursor left"):
                    self.command_line_mode(typed="/mvcurs left")
                if self.input.is_pressed("move cursor right"):
                    self.command_line_mode(typed="/mvcurs right")

            if self.input.is_pressed("add brush"):
                self.command_line_mode(typed="/addbrush")
            if self.input.is_pressed("previous brush"):
                self.command_line_mode(typed="/pvbrush")
            if self.input.is_pressed("next brush"):
                self.command_line_mode(typed="/nxbrush")

            if self.input.is_pressed("add color"):
                self.command_line_mode(typed="/addcolor")
            if self.input.is_pressed("previous font color"):
                self.command_line_mode(typed="/pvftcolor")
            if self.input.is_pressed("next font color"):
                self.command_line_mode(typed="/nxftcolor")
            if self.input.is_pressed("previous background color"):
                self.command_line_mode(typed="/pvbgcolor")
            if self.input.is_pressed("next background color"):
                self.command_line_mode(typed="/nxbgcolor")

            if self.input.is_pressed("next frame"):
                self.command_line_mode(typed="/nxframe")
            if self.input.is_pressed("previous frame"):
                self.command_line_mode(typed="/pvframe")

            if self.input.is_pressed("add frame"):
                self.command_line_mode(typed="/addframe")
            if self.input.is_pressed("remove frame"):
                self.command_line_mode(typed="/removeframe")
            if self.input.is_pressed("insert frame"):
                self.command_line_mode(typed="/insertframe")
            if self.input.is_pressed("copy frame"):
                self.command_line_mode(typed="/copyframe")
            if self.input.is_pressed("paste frame"):
                self.command_line_mode(typed="/pasteframe")

            if self.input.is_pressed("font color pipette"):
                self.command_line_mode(typed="/ftpip")
            if self.input.is_pressed("background color pipette"):
                self.command_line_mode(typed="/bgpip")
            if self.input.is_pressed("brush pipette"):
                self.command_line_mode(typed="/brushpip")

            if self.input.is_pressed("write"):
                self.command_line_mode(typed="/write")
            if self.input.is_pressed("erase"):
                self.command_line_mode(typed="/erase")

            if self.input.is_pressed("save"):
                self.command_line_mode(typed="/save")
            if self.input.is_pressed("load"):
                self.command_line_mode(typed="/load")

            if self.input.is_pressed("play"):
                self.command_line_mode(typed="/play")
            if self.input.is_pressed("set speed"):
                self.command_line_mode(typed="/setplayspeed")

            if self.input.is_pressed("manual"):
                self.show_controls()

        else:
            if self.input.is_pressed("play"):
                self.command_line_mode(typed="/stop")

# ------------------------------------------------------------------------------

    def command_line_mode(self, typed=None, args=()):

        def clear_c():
            print_crd("\n\033[s", 0, 9)
            draw_rectangle(" ", 0, 10, 30+self.w*2, self.h)
            draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            self.scene.show(force=True, repeat_color=True)
        clear_c.nargs = 0

        def echo(content):
            print("\n[out] "+str(content)+"\n")
            print("\033[s")
        echo.nargs = 1

        def invalid_command():
            print("\n[out] \33[0m\33[41mERROR: Unknown Command\33[0m\n")
            print("\033[s")
        invalid_command.nargs = 0

        def add_frame():
            self.sprites.append(TextSprite())
            self.scene.erase(self.sprites[self.frame])
            self.frame = len(self.sprites)-1
            self.sprites[len(self.sprites)-1].chart = {}
            self.sprites[len(self.sprites)-1].prtcrd = set()
            self.sprites[len(self.sprites)-1].act_prtcrd = set()
            self.scene.put(self.sprites[self.frame], 1, 1, 0)
            print_crd("           ", 31, self.h+2)
            print_crd("FRAME "+str(self.frame), 31, self.h+2)
            draw_rectangle("\033[48;5;236m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            time.sleep(0.2)
            draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            self.scene.show(force=True, repeat_color=True)
        add_frame.nargs = 0

        def copy_frame():
            self.clip = {
                "chart": copy.deepcopy(self.sprites[self.frame].chart),
                "prtcrd": copy.deepcopy(self.sprites[self.frame].prtcrd),
                "act_prtcrd": copy.deepcopy(self.sprites[self.frame].act_prtcrd)
            }
            draw_rectangle("\033[48;5;236m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            time.sleep(0.2)
            draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            self.scene.show(force=True, repeat_color=True)
        copy_frame.nargs = 0

        def paste_frame():
            if not hasattr(self, "clip"): return
            self.sprites[self.frame].chart = copy.deepcopy(self.clip["chart"])
            self.sprites[self.frame].prtcrd = copy.deepcopy(self.clip["prtcrd"])
            self.sprites[self.frame].act_prtcrd = copy.deepcopy(self.clip["act_prtcrd"])
            draw_rectangle("\033[48;5;236m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            time.sleep(0.2)
            draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            self.scene.show(force=True, repeat_color=True)
        paste_frame.nargs = 0

        def insert_frame():
            if self.frame == len(self.sprites)-1: add_frame()
            self.sprites.insert(self.frame+1, TextSprite())
            self.scene.erase(self.sprites[self.frame])
            self.frame += 1
            self.sprites[self.frame].chart = {}
            self.sprites[self.frame].prtcrd = set()
            self.sprites[self.frame].act_prtcrd = set()
            self.scene.put(self.sprites[self.frame], 1, 1, 0)
            print_crd("           ", 31, self.h+2)
            print_crd("FRAME "+str(self.frame), 31, self.h+2)
            draw_rectangle("\033[48;5;236m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            time.sleep(0.2)
            draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            self.scene.show(force=True, repeat_color=True)
        insert_frame.nargs = 0

        def remove_frame():
            self.scene.erase(self.sprites[self.frame])
            del self.sprites[self.frame]
            if len(self.sprites) == 0: new_frame()
            print_crd("           ", 31, self.h+2)
            print_crd("FRAME "+str(self.frame), 31, self.h+2)
            draw_rectangle("\033[48;5;236m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            time.sleep(0.2)
            draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            self.scene.show(force=True, repeat_color=True)
        remove_frame.nargs = 0

        def next_frame():
            print_crd("           ", 31, self.h+2)
            self.scene.erase(self.sprites[self.frame])
            self.frame += 1
            self.frame %= len(self.sprites)
            print_crd("           ", 31, self.h+2)
            print_crd("FRAME "+str(self.frame), 31, self.h+2)
            self.scene.put(self.sprites[self.frame], 1, 1, 0)
            draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            self.scene.show(force=True, repeat_color=True)
        next_frame.nargs = 0

        def previous_frame():
            print_crd("           ", 31, self.h+2)
            self.scene.erase(self.sprites[self.frame])
            self.frame -= 1
            self.frame %= len(self.sprites)
            print_crd("           ", 31, self.h+2)
            print_crd("FRAME "+str(self.frame), 31, self.h+2)
            self.scene.put(self.sprites[self.frame], 1, 1, 0)
            draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            self.scene.show(force=True, repeat_color=True)
        previous_frame.nargs = 0

        def move_cursor(dir):
            backup = lambda:None
            backup.x = int(self.cursor.x)
            backup.y = int(self.cursor.y)

            if dir == "up" and self.cursor.y > 1:
                self.scene.put(self.cursor, self.cursor.x, self.cursor.y-1, self.cursor.layer)
            elif dir == "down" and self.cursor.y < self.h-1:
                self.scene.put(self.cursor, self.cursor.x, self.cursor.y+1, self.cursor.layer)
            elif dir == "left" and self.cursor.x > 1:
                self.scene.put(self.cursor, self.cursor.x-1, self.cursor.y, self.cursor.layer)
            elif dir == "right" and self.cursor.x < 2*self.w-1:
                self.scene.put(self.cursor, self.cursor.x+1, self.cursor.y, self.cursor.layer)
            else:
                return

            if (int(self.cursor.x), int(self.cursor.y)) in self.sprites[self.frame].act_prtcrd:
                draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)

            self.scene.show(force=True, repeat_color=True)

            crd = str(int(self.cursor.x-1)) + "|" + str(int(self.cursor.y-1))
            print_crd("           ", 46, self.h+2)
            print_crd("CRD "+crd, 46, self.h+2)

            if not ((backup.x, backup.y) in self.sprites[self.frame].act_prtcrd):
                if 0 < backup.x <= self.w*2-1 and 0 < backup.y <= self.h-1:
                    print_crd("\033[48;5;234m \33[0m", 30+backup.x, 1+backup.y)

        move_cursor.nargs = 1

        def save_as():
            clear_c()
            print_crd("\33[32mDirectory ?:", 0, 10)
            self.path = alt_input(0, 11, prompt="\33[32m>>> \33[47m\33[30m ", maxline=1, maxchar=self.w*2+30)
            time.sleep(0.2)
            print("\33[0m")
            clear_c()
            save()
        save_as.nargs = 0

        def load_from():
            clear_c()
            print_crd("\33[32mDirectory ?:", 0, 10)
            folder = alt_input(0, 11, prompt="\33[32m>>> \33[47m\33[30m ", maxline=1, maxchar=self.w*2+30)
            time.sleep(0.2)
            print("\33[0m")
            assets = load_assets_from(folder)
            if assets == []: return
            self.sprites = []
            i = 0
            for asset in assets:
                self.sprites.append(TextSprite())
                self.sprites[i].set_asset(asset)
                i += 1
            self.frame = 0
            print_crd("           ", 31, self.h+2)
            print_crd("FRAME "+str(self.frame), 31, self.h+2)
            self.scene.put(self.sprites[self.frame], 1, 1, 0)
            draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            clear_c()
            draw_rectangle("\033[48;5;236m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            time.sleep(0.2)
            draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            self.scene.show(force=True, repeat_color=True)
        load_from.nargs = 0

        def save():
            i = 0
            for sprite in self.sprites:
                if self.path == "":
                    save_as()
                else:
                    asset = TextAsset(); asset.chart = sprite.chart
                    asset.prtcrd = sprite.prtcrd
                    path = self.path[:len(self.path)-4]
                    frame_nb = str(i)
                    while len(frame_nb) < 5:
                        frame_nb = "0" + frame_nb
                    save_asset_as(asset, self.path, "frame"+frame_nb)
                i += 1
            draw_rectangle("\033[48;5;236m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            time.sleep(0.2)
            draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            self.scene.show(force=True, repeat_color=True)
        save.nargs = 0

        def erase():
            crd = str(int(self.cursor.x-1)) + "|" + str(int(self.cursor.y-1))
            if not (crd in self.sprites[self.frame].chart): return
            if crd == self.last["crd"] and self.last["time"] + 0.3 > time.time(): return
            del self.sprites[self.frame].chart[crd]
            self.sprites[self.frame].prtcrd.remove((int(self.cursor.x-1),int(self.cursor.y-1)))
            self.sprites[self.frame].act_prtcrd.remove((int(self.cursor.x),int(self.cursor.y)))
            self.last["crd"] = crd
            self.last["time"] = time.time()
            self.scene.show(force=True, repeat_color=True)
            return
        erase.nargs = 0

        def paint():
            crd = str(int(self.cursor.x-1)) + "|" + str(int(self.cursor.y-1))
            if crd == self.last["crd"] and self.last["time"] + 0.3 > time.time(): return
            char = ""
            brush = self.brushes[self.brush]
            bgcolor = self.bg_palette[self.bg_color]
            ftcolor = self.fc_palette[self.font_color]
            if brush == " " and bgcolor == None:
                erase()
            else:
                char = brush
            self.sprites[self.frame].chart[crd] = (char, bgcolor, ftcolor, None)
            self.sprites[self.frame].prtcrd.add((int(self.cursor.x-1),int(self.cursor.y-1)))
            self.sprites[self.frame].act_prtcrd.add((int(self.cursor.x),int(self.cursor.y)))
            self.last["crd"] = crd
            self.last["time"] = time.time()
            self.scene.show(force=True, repeat_color=True)

        paint.nargs = 0

        def add_brush():
            clear_c()
            print_crd("\33[32mType the brush's char\n in the white rectangle\n bellow, then press enter.", 0, 10)
            brush = alt_input(0, 14, prompt="\33[32m>>> \33[47m\33[30m ", maxline=1, maxchar=1)
            time.sleep(0.2)
            print("\33[0m")
            brush = brush[0]
            clear_c()
            if (str(brush) in self.brushes) == False:
                self.brushes.append(str(brush))
            self.actualize_toolbar()
        add_brush.nargs = 0

        def add_color():
            clear_c()
            self.palette_scene.show(force=True, repeat_color=True)
            print_crd("\033[u\33[32mType the color code\n between 0 and 255\n in the white rectangle\n bellow, then press enter.", 0, 10)
            color = alt_input(0, 15, prompt="\33[32m>>> \33[47m\33[30m ", maxline=1, maxchar=3, digit_only=True)
            time.sleep(0.2)
            print("\33[0m")
            color_bg = "\u001b[48;5;"+str(color)+"m"
            color_ft = "\u001b[38;5;"+str(color)+"m"

            self.palette_scene.hide()
            draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            self.scene.show(repeat_color=True)

            clear_c()
            if (color_bg in self.bg_palette) == False:
                self.bg_palette.append(color_bg)
                self.fc_palette.append(color_ft)

            self.actualize_toolbar()
        add_color.nargs = 0

        def next_bg_color():
            self.bg_color += 1
            self.bg_color %= len(self.bg_palette)
            self.actualize_cursor()
        next_bg_color.nargs = 0

        def previous_bg_color():
            self.bg_color -= 1
            self.bg_color %= len(self.bg_palette)
            self.actualize_cursor()
        previous_bg_color.nargs = 0

        def next_ft_color():
            self.font_color += 1
            self.font_color %= len(self.bg_palette)
            self.actualize_cursor()
        next_ft_color.nargs = 0

        def previous_ft_color():
            self.font_color -= 1
            self.font_color %= len(self.fc_palette)
            self.actualize_cursor()
        previous_ft_color.nargs = 0

        def next_brush():
            self.brush += 1
            self.brush %= len(self.brushes)
            self.actualize_cursor()
        next_brush.nargs = 0

        def previous_brush():
            self.brush -= 1
            self.brush %= len(self.brushes)
            self.actualize_cursor()
        previous_brush.nargs = 0

        def play():
            self.playing = True
            self.play_sprite = TextSprite()
            self.scene.erase(self.sprites[self.frame])
            self.scene.erase(self.cursor)
            self.scene.put(self.play_sprite, 1, 1, 0)
            assets = []
            for sprite in self.sprites:
                ta = TextAsset()
                ta.chart = sprite.chart
                ta.prtcrd = sprite.prtcrd
                assets.append(ta)

            self.fb = Flipbook(self.refresh, self.play_sprite, assets, fps = float(1/self.play_speed))
            self.refresh.feed(self.scene.show, *(), **{})
            draw_rectangle("\033[48;5;236m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            time.sleep(0.2)
            draw_rectangle("\033[48;5;232m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            self.scene.show(force=True, repeat_color=True)
            self.fb.start()
        play.nargs = 0

        def set_playing_speed():
            clear_c()
            print_crd("\033[u\33[32mPlaying speed ?(ms)", 0, 10)
            self.play_speed = 0.001*float(alt_input(0, 11, prompt="\33[32m>>> \33[47m\33[30m ", maxline=1, maxchar=10, digit_only=True))
            print(self.play_speed)
            time.sleep(2)
            print("\33[0m")
            clear_c()
        set_playing_speed.nargs = 0

        def stop():
            self.playing = False
            self.fb.stop()
            self.scene.erase(self.play_sprite)
            self.scene.put(self.sprites[self.frame], 1, 1, 0)
            self.scene.put(self.cursor, 1, 1, 1)
            self.refresh.terminate(self.scene.show, *(), **{})
            draw_rectangle("\033[48;5;236m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            time.sleep(0.2)
            draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            self.scene.show(force=True, repeat_color=True)
        stop.nargs = 0

        def write():
            string = alt_input(31+self.cursor.x, self.cursor.y+1, maxline=1, maxchar=(self.w*2 - self.cursor.x)-1)
            x = 1
            for i in range(0, len(string)):
                crd = str(int(self.cursor.x-1+x)) + "|" + str(int(self.cursor.y-1))
                bgcolor = self.bg_palette[self.bg_color]
                ftcolor = self.fc_palette[self.font_color]
                self.sprites[self.frame].chart[crd] = (string[i], bgcolor, ftcolor, None)
                self.sprites[self.frame].prtcrd.add((int(self.cursor.x-1+x),int(self.cursor.y-1)))
                self.sprites[self.frame].act_prtcrd.add((int(self.cursor.x+x),int(self.cursor.y)))
                x += 1
            draw_rectangle("\033[48;5;234m \33[0m", 31, 2, 30+self.w*2, self.h+1)
            self.scene.show(force=True, repeat_color=True)
            time.sleep(0.3)

        write.nargs = 0

        def bg_pip():
            crd = str(int(self.cursor.x-1)) + "|" + str(int(self.cursor.y-1))
            if not (crd in self.sprites[self.frame].chart): return
            brush, bgcolor, ftcolor, style = self.sprites[self.frame].chart[crd]
            if not (bgcolor in self.bg_palette):
                self.bg_palette.append(bgcolor)
                self.fc_palette.append(bgcolor.replace("[48;", "[38;"))
                self.bg_color = len(self.bg_palette)-1
            else:
                self.bg_color = self.bg_palette.index(bgcolor)
            self.actualize_cursor()
        bg_pip.nargs = 0

        def ft_pip():
            crd = str(int(self.cursor.x-1)) + "|" + str(int(self.cursor.y-1))
            if not (crd in self.sprites[self.frame].chart): return
            brush, bgcolor, ftcolor, style = self.sprites[self.frame].chart[crd]
            if not (ftcolor in self.fc_palette):
                self.fc_palette.append(ftcolor)
                self.bg_palette.append(ftcolor.replace("[38;", "[48;"))
                self.font_color = len(self.fc_palette)-1
            else:
                self.font_color = self.fc_palette.index(ftcolor)
            self.actualize_cursor()
        ft_pip.nargs = 0

        def brush_pip():
            crd = str(int(self.cursor.x-1)) + "|" + str(int(self.cursor.y-1))
            if not (crd in self.sprites[self.frame].chart): return
            brush, bgcolor, ftcolor, style = self.sprites[self.frame].chart[crd]
            if not (brush in self.brushes):
                self.brushes.append(brush)
                self.brush = len(self.brushes)-1
            else:
                self.brush = self.brushes.index(brush)
            self.actualize_cursor()
        brush_pip.nargs = 0

        def command_switch(command):
            switcher = {
                "/echo": echo,
                "/mvcurs": move_cursor,
                "/clr": clear_c,
                "/pvbrush": previous_brush,
                "/nxbrush": next_brush,
                "/addbrush": add_brush,
                "/addcolor": add_color,
                "/pvbgcolor": previous_bg_color,
                "/nxbgcolor": next_bg_color,
                "/pvftcolor": previous_ft_color,
                "/nxftcolor": next_ft_color,
                "/pvframe": previous_frame,
                "/nxframe": next_frame,
                "/addframe": add_frame,
                "/insertframe": insert_frame,
                "/copyframe": copy_frame,
                "/pasteframe": paste_frame,
                "/removeframe": remove_frame,
                "/setplayspeed": set_playing_speed,
                "/bgpip": bg_pip,
                "/ftpip": ft_pip,
                "/brushpip": brush_pip,
                "/play": play,
                "/stop": stop,
                "/paint": paint,
                "/load": load_from,
                "/save": save,
                "/erase": erase,
                "/write": write
            }
            return switcher.get(command, invalid_command)

        one_cmd_mode = False

        if typed == None:
            sys_print("\033[u\33[32m[in] ")
            input("")
        else: one_cmd_mode = True

        if typed == "": return

        typed_split = typed.split(" ")
        while "" in typed_split: typed_split.remove("")

        command = typed_split[0]

        func = command_switch(command)

        if len(typed_split) == func.nargs+1: args = tuple(typed_split[1:])
        elif len(typed_split) < func.nargs+1: return print("\n[out] \33[0m\33[41mERROR: Missing Arguments\33[0m\n")
        elif len(typed_split) > func.nargs+1: return print("\n[out] \33[0m\33[41mERROR: Too many Arguments\33[0m\n")

        print("\033[s")
        func(*args)


app = TextAssetCreator(32, 18)
