import os
import sys

os.chdir(sys.path[0])
sys.path.insert(1, "P://Python Projects/assets/")

from GUI import *


class Animation:
	allAnimations = []

	def SetColor(surface, colors):
		# easier to crate different images with different colors instead
		for color_pairs in colors:
			colorA, colorB = color_pairs

			pixelArray = pg.PixelArray(surface)
			pixelArray.replace(colorA, colorB)

			surface = pixelArray.make_surface().convert_alpha()

		return surface

	def __init__(self, rect, filePath, numOfFrames, fps=12, loop=False, autoPlay=False, reversable=False):
		self.rect = pg.Rect(rect)

		self.filePath = filePath

		self.numOfFrames = numOfFrames
		self.LoadImg()

		self.fps = fps
		self.loop = loop
		self.autoPlay = autoPlay

		self.reversable = reversable
		self.reversed = False

		self.updateFrame = Sequence(loop=True, autoDestroy=False, duration=self.numOfFrames, timeStep=(self.numOfFrames / FPS) * self.fps)

		self.updateFrame.append(Func(self.IncrementFrame))

		self.startFunc = None
		self.stopFunc = None

		Animation.allAnimations.append(self)

		if self.autoPlay:
			self.updateFrame.Start()

	def LoadImg(self, img=None):
		if CheckFileExists(self.filePath):
			if img == None:
				self.fullImg = pg.image.load(self.filePath)
			else:
				self.fullImg = img
			img_width, img_height = self.fullImg.get_width(), self.fullImg.get_height()

			y = 0
			frameHeight = img_height // self.numOfFrames

			self.frames = [pg.transform.scale(self.fullImg.subsurface((0, y + (i * frameHeight), img_width, frameHeight)), (self.rect.w, self.rect.h)) for i in range(img_height // frameHeight)]
			self.currentFrame = 0

		else:
			self.fullImg = None
			self.frames = []
			self.currentFrame = None

	def Draw(self):
		if self.fullImg != None:
			screen.blit(self.frames[self.currentFrame], self.rect)
			self.updateFrame.timeStep = (self.updateFrame.duration / clock.get_fps()) * self.fps if clock.get_fps() != 0 else 0
			
			self.updateFrame.Update()

			if not self.loop:
				if self.updateFrame.loopCount >= self.numOfFrames:
					self.Stop()

	def IncrementFrame(self):
		if self.reversed:
			self.currentFrame -= 1
			
			if self.currentFrame < 0:
				self.reversed = False
				self.currentFrame = 0			

		else:
			self.currentFrame += 1

			if self.currentFrame >= len(self.frames):
				if self.reversable:
					self.reversed = True
					self.currentFrame = len(self.frames) - 1
				else:
					self.currentFrame = 0

	def Start(self):
		self.updateFrame.Start()
		if self.startFunc != None:
			if isinstance(self.startFunc, Sequence):
				self.startFunc.Start()
			else:
				self.startFunc()

	def Stop(self):
		self.updateFrame.Stop()
		if self.stopFunc != None:
			if isinstance(self.stopFunc, Sequence):
				self.stopFunc.Start()
			else:
				self.stopFunc()

	# expensive
	def ChangeColor(self, colors):
		self.fullImg = Animation.SetColor(self.fullImg, colors)
		self.LoadImg(self.fullImg)



class Animator:
	allAnimators = []

	def __init__(self, animations={}, active=[]):
		self.animations = {}

		for key in animations:
			self.append(key, animations[key])

		self.activeAnimations = []

		for key in active:
			if key in self.animations:
				self.activeAnimations.append(self.animations[key])

		self.previousAnimation = None

		Animator.allAnimators.append(self)

	def __str__(self):
		return f"allAnimations: {len(self.animations)}, activeAnimations: {len(self.activeAnimations)}"

	def Draw(self):
		for animation in self.activeAnimations:
			animation.Draw()

	def append(self, key, animation):
		if type(animation) == Animation:
			
			animation.stopFunc = Func(self.RemoveActive, 0, key)
			
			animation.startFunc = Func(self.AddActive, 0, key)

			self.animations[key] = animation
		else:
			raise TypeError(f"Animation is not of type {Animation}")

	def remove(self, key):
		if key in self.animations:
			self.animations.pop(key)
		else:
			raise ValueError("Key not in dict")

	def UpdatePos(self, pos):
		for key in self.animations:
			self.animations[key].rect.x = pos[0]
			self.animations[key].rect.y = pos[1]

	def UpdateSize(self, size):
		pass

	def AddActive(self, key, onStop=None):
		if key in self.animations:
			if self.animations[key] not in self.activeAnimations:
				self.activeAnimations.append(self.animations[key])
				self.animations[key].Start()

				if onStop != None:
					self.animations[key].stopFunc = Sequence(Func(self.RemoveActive, 0, key), Func(self.AddActive, 0, onStop))

	def RemoveActive(self, key):
		if key in self.animations:
			if self.animations[key] in self.activeAnimations:
				self.activeAnimations.remove(self.animations[key])
				self.animations[key].Stop()
				self.previousAnimation = key

	def RemoveAll(self):
		self.previousAnimation = None
		if len(self.activeAnimations) > 0:
			for animation in self.activeAnimations:
				animation.Stop()

			for key in self.animations:
				if self.animations[key] == animation:
					self.previousAnimation = key

		self.activeAnimations = []

	def StartActiveAnimations(self):
		for animation in self.activeAnimations:
			animation.Start()

	def StopActiveAnimations(self):
		for animation in self.activeAnimations:
			animation.Stop()



rect = (100, 100, 100, 100)
b = Animator(
	{"idle": Animation(rect, "animations/player-idle.png", 2, 2, autoPlay=True, loop=True),
	 "walk": Animation(rect, "animations/player-walk.png", 4, 10, autoPlay=False, loop=True),
	 "jump": Animation(rect, "animations/player-jump.png", 4, 10, autoPlay=False, loop=False)},
	  active=["idle"])


def DrawLoop():
	screen.fill(darkGray)

	DrawAllGUIObjects()

	for animator in Animator.allAnimators:
		animator.Draw()
		animator.UpdatePos(pg.mouse.get_pos())

	pg.display.update()


def HandleEvents(event):
	HandleGui(event)

	if event.type == pg.KEYDOWN:
		if event.key == pg.K_0:
			b.RemoveAll()
			b.AddActive("idle")

		if event.key == pg.K_1:
			b.RemoveAll()
			b.AddActive("walk")

		if event.key == pg.K_2:
			b.RemoveAll()
			b.AddActive("jump", onStop=b.previousAnimation)

		

fpsLbl = Label((width - 100, 0, 100, 50), (black, white), drawData={"drawBackground":False, "drawBorder":False}, textData={"fontSize":12, "alignText":"right-top", "fontColor":white})

while RUNNING:
	clock.tick_busy_loop(FPS)
	deltaTime = clock.get_time()
	fpsLbl.UpdateText(str(round(clock.get_fps(), 1)))
	for event in pg.event.get():
		if event.type == pg.QUIT:
			RUNNING = False
		if event.type == pg.KEYDOWN:
			if event.key == pg.K_ESCAPE:
				RUNNING = False


		HandleEvents(event)

	DrawLoop()
