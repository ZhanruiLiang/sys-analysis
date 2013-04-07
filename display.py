import pygame
import world
import grids
from snake import Snake
from events import EventTypes

# TODO cool down mechanism

class LayerStack:
    """
    A stack of layers, to store items with
    different depths.

    It adopts the iterator design pattern.
    """

    def __init__(self):
        self.layersSequence = []
        self.layers = {}

    def push_layer(self, layerName):
        self.layersSequence += [layerName]
        self.layers[layerName] = []

    def add_to_layer(self, layerName, item):
        self.layers[layerName].append(item)

    def size_of(self, layerName):
        return len(self.layers[layerName])

    #
    # Iterator design pattern
    def __iter__(self):
        self.itLayer = iter(self.layersSequence)
        self.itItem = None
        return self

    #
    # Iterator design pattern
    def next(self):
        if self.itItem == None:
            self.curLayer = self.itLayer.next()
            self.itItem = iter(self.layers[self.curLayer])
            self.curItem = self.itItem.next()
            return self.curItem
        try:
            self.curItem = self.itItem.next()
            return self.curItem
        except:
            try:
                self.curLayer = self.itLayer.next()
                self.itItem = iter(self.layers[self.curLayer])
                self.curItem = self.itItem.next()
                return self.curItem
            except:
                raise StopIteration

class ImageFactory:
    """
    A factory of all images/sprites.
    Notice that it should better be a singleton
    """
    
    def __init__(self):
        self.container = {}

    def register(self, appearance, fname, angle=0):
        """
        Link an apperance to an actual image.
        """
        self.container[appearance] = pygame.transform.rotate(
                pygame.image.load(fname), angle)

    def get_image(self, appearance):
        """
        Return a surface for an appearance
        """
        return self.container[appearance]

class Display:
    def __init__(self, width=600, height=600):
        """
        Initialize display.
        @width: width of the stage
        @height: height of the stage
        """
        pygame.display.init()
        pygame.font.init()
        self.window = pygame.display.set_mode((width, height))
        self.width = width
        self.height = height

        # should be a constant
        self.blkSize = 20

    def init(self, game):
        game.bind_event(EventTypes.SNAKE_BORN, self.add_snake)
        game.bind_event(EventTypes.SNAKE_DIE, self.handle_snake_die)
        # TODO: Bind handlers for gameEvents here. 
        #   Interested events: SnakeBorn, SnakeEat, SnakeDie, FoodGen, FoodDisappear

        # Initialize layer system
        self.layerStack = LayerStack()
        self.layerStack.push_layer('field')
        #self.layerStack.push_layer('items')
        self.layerStack.push_layer('snakes')
        self.layerStack.push_layer('sky')

        # rendering callbacks
        self.renderCallbacks = {}
        self.renderCallbacks['snake'] = self.render_snake
        self.renderCallbacks['field'] = self.render_field

        # All kinds of snakes
        self.snakeAppearance = [
            'snake-red',
            'snake-red',
            'snake-blue',
            'snake-green',
            ]

        # Add field
        self.add_field(game.world.field)

        # Register images for sprites
        self.imageFactory = ImageFactory()
        r = self.imageFactory.register
        r('grid-%s'%(grids.BLANK), 'img/grid-blank.png')
        r('grid-%s'%(grids.SNAKE), 'img/grid-snake.png')
        r('grid-%s'%(grids.FOOD), 'img/grid-food.png')

        # TODO: Add panel to sky

        # Initialize stage
        self.fieldX = 80
        self.fieldY = 80

    def add_snake(self, event):
        """
        A callback to the SNAKE_BORN event.
        Add the snake to the corresponding layer.
        """
        snake = event.snake
        r = self.imageFactory.register
        name = snake.name
        # image path template
        appearance = self.snakeAppearance[self.layerStack.size_of('snakes')]
        self.layerStack.add_to_layer('snakes', snake)

        # register resources
        imgT = 'img/%s%%s.png' % appearance
        imgTurn = imgT % '-turn'
        imgNormal = imgT % ''
        # Directions:
        #          0 (0, -1)
        #          ^
        #(-1,0)3 <   > 1 (1, 0)
        #          v
        #          2 (0, 1)
        D = ((0, -1), (1, 0), (0, 1), (-1, 0))
        for d1, angle in zip(D, (180, 90, 0, 270)):
            # d1 = body[1] - head
            r((name, ('head', d1)), imgT % '-head', angle)
            # d1 = tail - body[-2]
            r((name, ('tail', d1)), imgT % '-tail', angle)
        # r((name, (d1, d2)), image, angle)
        # for body[i] or a snake, (d1, d2) = (body[i-1].pos - body[i].pos, body[i+1].pos - body[i].pos)
        r((name, (D[0], D[1])), imgTurn, 0)
        r((name, (D[1], D[2])), imgTurn, -90)
        r((name, (D[2], D[3])), imgTurn, -180)
        r((name, (D[3], D[0])), imgTurn, -270)
        r((name, (D[0], D[2])), imgNormal, 0)
        r((name, (D[1], D[3])), imgNormal, 90)
        # reverse
        r((name, (D[1], D[0])), imgTurn, 0)
        r((name, (D[2], D[1])), imgTurn, -90)
        r((name, (D[3], D[2])), imgTurn, -180)
        r((name, (D[0], D[3])), imgTurn, -270)
        r((name, (D[2], D[0])), imgNormal, 0)
        r((name, (D[3], D[1])), imgNormal, 90)

    def handle_snake_die(self, event):
        snake = event.snake
        # TODO: remove snake from layerStack

    def block2screen(self, pos):
        return (self.fieldX + pos[0] * self.blkSize, 
                self.fieldY + pos[1] * self.blkSize)

    def render_snake(self, snake):
        body_len = len(snake.body)
        body = snake.body

        g = self.imageFactory.get_image
        blit = self.window.blit
        def diff(i, j):
            (xj, yj) = snake.body[j].pos
            (xi, yi) = snake.body[i].pos
            return (xi - xj, yi - yj)
        # Render head
        blit(g((snake.name, ('head', diff(1, 0)))), 
                self.block2screen(snake.head.pos))
        # Render inner body
        for i in xrange(1, len(snake.body)-1):
            blit(g((snake.name, (diff(i-1, i), diff(i+1, i)))), 
                self.block2screen(snake.body[i].pos))
        # Render tail
        blit(g((snake.name, ('tail', diff(-1, -2)))), 
            self.block2screen(snake.body[-1].pos))

    def render_field(self, objToRender):
        field = objToRender
        for y in range(0, field.height):
            for x in range(0, field.width):
                self.window.blit(
                    self.imageFactory.get_image(
                        'grid-'+str(field.get_grid_at(x, y).type)),
                    (self.fieldX+x*self.blkSize,
                        self.fieldY+y*self.blkSize))

    def add_field(self, field):
        self.layerStack.add_to_layer('field', field)
        field.name = 'field'
        field.appearance = 'field'

    def render(self, world):
        """
        Render the world. This will be called at each update in main loop.
        
        @world: world to render
        """
        #
        # reset
        self.window.fill((255, 255, 255))

        # XXX: Why renderCallbacks? Things should be rendered layer by layer.
        # for item in self.layerStack:
        #     self.renderCallbacks[item.name](item)
        for item in self.layerStack:
            if isinstance(item, Snake):
                self.render_snake(item)

        pygame.display.flip()

    def quit(self):
        pass

if __name__ == "__main__":
    """
    Unit test
    """
    ls = LayerStack()
    ls.push_layer('ground')
    ls.push_layer('sky')

    print ls.layers
    print ls.layersSequence

    ls.add_to_layer('sky', 'eagle')
    ls.add_to_layer('ground', 'cow')
    ls.add_to_layer('sky', 'bird')
    ls.add_to_layer('ground', 'monkey')
    for animal in ls:
        print animal
