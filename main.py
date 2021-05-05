import pygame
from pygame.locals import *
import ctypes, platform, os, sys
from pygame import gfxdraw

pygame.init()

if platform.system() == "Windows":
    ctypes.windll.user32.SetProcessDPIAware()

class Colors:
    LGREY = (175, 175, 175)
    DGREY = (40, 40, 40)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    BLACK = (0, 0, 0)
    BLUE = (0, 100, 150)


loaded_images = {}

assetsDir = "assets"
if hasattr(sys, "_MEIPASS"):
    assetsDir = os.path.join(sys._MEIPASS, assetsDir)
    print("AssetDIR:", assetsDir)


def loadImage(filename, hasAlpha = False):
    if filename in loaded_images:
        image = loaded_images[filename]
    else:
        image = pygame.image.load(os.path.join(assetsDir, filename))
        if hasAlpha:
            image.convert_alpha()
        loaded_images[filename] = image

    return image


class ToggleButton(pygame.sprite.Sprite):
    def __init__(self, x, y, id):
        pygame.sprite.Sprite.__init__(self)
        self.images = [loadImage("off.png"), loadImage("on.png")]
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.state = False

        self.rect.x = x
        self.rect.y = y
        self.id = id

    def update(self):
        mouseX = pygame.mouse.get_pos()[0] - self.rect.x
        mouseY = pygame.mouse.get_pos()[1] - self.rect.y

        if (mouseX in range(0, self.rect.width)) and (mouseY in range(0, self.rect.width)):
            self.state = not self.state
            activeSymmetries[self.id] = self.state

        self.image = self.images[int(self.state)]


class ImageSelector(pygame.sprite.Sprite):
    def __init__(self, image, x, y, screenXAxisInfo, screenYAxisInfo):
        pygame.sprite.Sprite.__init__(self)
        self.imagebase = image
        self.rect = self.imagebase.get_rect()
        self.image = pygame.Surface(self.rect.size)
        self.image.blit(self.imagebase, (0, 0))
        self.rect.x = x
        self.rect.y = y
        self.screenXAxis = screenXAxisInfo
        self.screenYAxis = screenYAxisInfo
        self.allowSymmetry = False

        print(f"{self.rect.left} - {self.rect.right} : {self.rect.top} - {self.rect.bottom} @ ({self.rect.x},{self.rect.y})")

    def makePreview(self, mouseX, mouseY):
        global SHOWPREVIEW, PREVIEWRECT
        SHOWPREVIEW = True
        PREVIEWRECT.topright = self.rect.topright

        clipX = mouseX - self.rect.x - 12
        clipY = mouseY - self.rect.y - 12
        clipOffsetX = 0
        clipOffsetY = 0
        clipWidth = 25
        clipHeight = 25

        if clipX < 0:
            clipOffsetX = -clipX
        elif (clipX + 25) > self.rect.width:
            clipWidth = 25 - (clipX + 25 - self.rect.width)

        if clipY < 0:
            clipOffsetY = -clipY
        elif (clipY + 25) > self.rect.height:
            clipHeight = 25 - (clipY + 25 - self.rect.height)

        clip = self.image.subsurface((clipX + clipOffsetX, clipY + clipOffsetY, clipWidth, clipHeight))
        clip = pygame.transform.scale(clip, (clipWidth * 5, clipHeight * 5))
        PREVIEWSURF.blit(clip, (clipOffsetX * 5, clipOffsetY * 5, 125, 125))
        PREVIEWSURF.blit(loaded_images["reticle.png"], (0, 0))
        pygame.draw.rect(PREVIEWSURF, Colors.RED, (2, 2, 122, 122), 5)

    def update(self):
        mouseX = pygame.mouse.get_pos()[0]
        mouseY = pygame.mouse.get_pos()[1]

        if self.rect.left <= mouseX <= self.rect.right and self.rect.top <= mouseY <= self.rect.bottom:
            self.makePreview(mouseX, mouseY)

    def setPixelPos(self):
        global pixelPositions
        mouseX = pygame.mouse.get_pos()[0]
        mouseY = pygame.mouse.get_pos()[1]

        if self.rect.left <= mouseX <= self.rect.right and self.rect.top <= mouseY <= self.rect.bottom and pygame.mouse.get_pressed(3)[0]:
            x2D = y2D = 0

            if self.screenXAxis["3dAxis"][0] == "-":
                x2D = self.rect.right - mouseX
            else:
                x2D = mouseX - self.rect.left

            if self.screenYAxis["3dAxis"][0] == "-":
                y2D = self.rect.bottom - mouseY
            else:
                y2D = mouseY - self.rect.top

            pixelPositions[0][self.screenXAxis["3dAxis"][1]] = x2D / self.rect.width
            pixelPositions[0][self.screenYAxis["3dAxis"][1]] = y2D / self.rect.height

    def drawMarker(self, pixelPos):
        if self.screenXAxis["3dAxis"][0] == "-":
            drawX = 1 - pixelPos[self.screenXAxis["3dAxis"][1]]
        else:
            drawX = pixelPos[self.screenXAxis["3dAxis"][1]]

        if self.screenYAxis["3dAxis"][0] == "-":
            drawY = 1 - pixelPos[self.screenYAxis["3dAxis"][1]]
        else:
            drawY = pixelPos[self.screenYAxis["3dAxis"][1]]

        gfxdraw.filled_circle(self.image, int(drawX * self.rect.width), int(drawY * self.rect.height), 4, Colors.RED)
        gfxdraw.circle(self.image, int(drawX * self.rect.width), int(drawY * self.rect.height), 4, (255, 255, 255))
        gfxdraw.circle(self.image, int(drawX * self.rect.width), int(drawY * self.rect.height), 5, (0, 0, 0))



    def manualUpdate(self):
        global pixelPositions

        self.image.blit(self.imagebase, (0, 0))
        for pixelPos in pixelPositions:
            self.drawMarker(pixelPos)


def makeSymmetries(doX = False, doZ = False):
    global pixelPositions
    configs = {
        ("x", "z"): 0.5,
        ("x", "y"): 0.251748,
        ("z", "y"): 0.251748,
        ("y", "z"): 0.5
    }

    if doX:
        temp = []
        for pos in pixelPositions:
            x, y, z = pos["x"], pos["y"], pos["z"]

            diff = configs[("x", "z")] - z
            z = configs[("x", "z")] + diff
            temp.append({"x": x, "y": y, "z": z})

        pixelPositions.extend(temp)

    if doZ:
        temp = []
        for pos in pixelPositions:
            x, y, z = pos["x"], pos["y"], pos["z"]

            diff = configs[("z", "y")] - y
            y = configs[("z", "y")] + diff
            temp.append({"x": x, "y": y, "z": z})

        pixelPositions.extend(temp)



def pixToWorld(pixPos3D):
    worldX = int(pixPos3D["x"]*400) - 81
    worldY = int(pixPos3D["y"]*120) + 99
    worldZ = int(pixPos3D["z"]*245) - 78

    worldString = f"({worldX}, {worldY}, {worldZ})"

    return worldString

def main():
    global SHOWPREVIEW, PREVIEWRECT, pixelPositions
    run = True

    loadImage("reticle.png", True)

    selectors = pygame.sprite.Group()
    selectors.add(ImageSelector(loadImage("top.png"), 4, 4, {"offset": 283, "3dAxis": "-x"}, {"3dAxis": "-z"}))
    selectors.add(ImageSelector(loadImage("side.png"), 4, 583, {"offset": 215, "3dAxis": "-x"}, {"3dAxis": "-y"}))
    selectors.add(ImageSelector(loadImage("front.png"), 1049, 4, {"offset": 231, "3dAxis": "+z"}, {"offset": 314, "3dAxis": "-y"}))
    selectors.add(ImageSelector(loadImage("back.png"), 1049, 314, {"offset": 231, "3dAxis": "-z"}, {"offset": 314, "3dAxis": "-y"}))

    buttons = pygame.sprite.Group()
    xButton = ToggleButton(1144, 741, "x")
    zButton = ToggleButton(1396, 741, "z")
    buttons.add(xButton, zButton)

    menuBG = loadImage("menu.png", True)
    menuRect = menuBG.get_rect()
    menuRect.x = 1049
    menuRect.y = 624

    clock = pygame.time.Clock()

    outputFont = pygame.font.Font(os.path.join(assetsDir, "font.ttf"), 30)
    fontRender = outputFont.render("", False, Colors.BLACK)
    fontRect = fontRender.get_rect()
    fontRect.bottomleft = (15, 930)

    while run:
        events = pygame.event.get()
        for event in events:
            if event.type == QUIT:
                run = False
            if event.type == MOUSEBUTTONDOWN:
                buttons.update()

                for sprite in selectors:
                    sprite.setPixelPos()

                pixelPositions = pixelPositions[0:1]
                makeSymmetries(xButton.state, zButton.state)

                for sprite in selectors:
                    sprite.manualUpdate()

                worldStrList = []
                for pos in pixelPositions:
                    worldStrList.append(pixToWorld(pos))

                fontRender = outputFont.render(", ".join(worldStrList), False, Colors.BLACK)
                fontRect = fontRender.get_rect()
                fontRect.bottomleft = (15, 930)

            if event.type == KEYDOWN:
                moveSpeed = 1
                if event.mod & KMOD_SHIFT:
                    moveSpeed = 5

                mX, mY = pygame.mouse.get_pos()
                if event.key in [K_LEFT, K_a]:
                    pygame.mouse.set_pos((mX - moveSpeed, mY))
                elif event.key in [K_RIGHT, K_d]:
                    pygame.mouse.set_pos((mX + moveSpeed, mY))
                elif event.key in [K_UP, K_w]:
                    pygame.mouse.set_pos((mX, mY - moveSpeed))
                elif event.key in [K_DOWN, K_s]:
                    pygame.mouse.set_pos((mX, mY + moveSpeed))


        PREVIEWSURF.fill(Colors.LGREY)
        SHOWPREVIEW = False
        selectors.update()


        DISPLAYSURF.fill(Colors.LGREY)

        pygame.draw.rect(DISPLAYSURF, Colors.DGREY, (0, 0, 1049, 873))
        pygame.draw.rect(DISPLAYSURF, Colors.DGREY, (1045, 0, 737, 624))
        selectors.draw(DISPLAYSURF)
        DISPLAYSURF.blit(menuBG, menuRect)
        buttons.draw(DISPLAYSURF)
        DISPLAYSURF.blit(fontRender, fontRect)

        if SHOWPREVIEW:
            DISPLAYSURF.blit(PREVIEWSURF, PREVIEWRECT)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    DISPLAYSURF = pygame.display.set_mode((1682, 945), DOUBLEBUF | SCALED)
    PREVIEWSURF = pygame.surface.Surface((125, 125))
    PREVIEWRECT = PREVIEWSURF.get_rect()
    SHOWPREVIEW = False

    activeSymmetries = {"x": False, "y": False, "z": False}
    pixelPositions = [{"x": 0, "y": 0, "z": 0}]
    pygame.display.set_caption("Star Destroyer Assistant")
    pygame.display.set_icon(loadImage("dorito.png", True))
    main()
