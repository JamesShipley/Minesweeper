import pygame,random,time
from timer_py import timer
class runner:
    def __init__(self):
        self.program = None
        self.start = None
        
    def run(self,program):
        self.program = program
        return self
    
    def for_time(self,duration):
        t = timer().start()
        while t.get_elapsed()<duration:
            self.program()
            
    def forever(self):
        while True:
            self.program()
        
class minesweeper:
    def __init__(self,scale = 1):

        #display
        self.window_width = 995
        self.window_height = 632
        self.width = 30
        self.height = 16
        self.scale = scale
        self.gd = pygame.display.set_mode((self.window_width*scale,self.window_height*scale))

        #game variables
        self.num_bombs = 99
        #self.map = [[(None,False,False) for y in range(self.height)] for x in range(self.width)]
        self.mouse = (0,0,0)
        #images 
        get_image = lambda x: pygame.transform.rotozoom(pygame.image.load(x+".png"),0,scale)
        self.images = {x:get_image(["zero","one","two","three","four","five","six"][x]) for x in range(-3,7)}
        self.base_img = get_image("base")
        self.bomb_img = get_image("bomb")
        self.flag_img = get_image("flag")

         
    #initialising functions ----------------------------------------------------------------------
    def reset_map(self):
        self.map = [[[None,False,False] for y in range(self.height)] for x in range(self.width)]
        
    def initialise_map(self,starting_click):
        # (Number,flagged,revealed) for each position
        self.place_bombs(starting_click)
        for x in range(self.width):
            for y in range(self.height):
                self.initialise_square(x,y)

    def place_bombs(self,starting_click):
        p,q = starting_click
        
        for i in range(self.num_bombs):
            while True:
                x,y = random.randint(0,self.width-1),random.randint(0,self.height-1)
                #dont use invalid positions
                if (abs(x-p)>1 or abs(y-q)>1) and self.map[x][y][0]==None:
                    self.map[x][y][0] = -1
                    break

    def initialise_square(self,x,y):
        #if there is no bomb in this position:
        if self.map[x][y][0]==None:
            self.map[x][y][0] = sum([self.map[i][j][0]==-1 for i,j in self.neighbouring_positions(x,y)])

    #game logic ------------------------------------------------------------------------------

    def reveal_square(self,x,y):
        if not self.valid_position(x,y) or self.is_flagged(x,y) or self.is_revealed(x,y):
            return False
        
        if self.is_bomb(x,y):
            return True

        
        self.map[x][y][2] = True
        if self.number_of(x,y)!=0:
            return False

        for i,j in self.neighbouring_positions(x,y):
            if not self.is_bomb(i,j):
                self.reveal_square(i,j)
                
        return False

    def flag_square(self,x,y,human_click=True):
        if not self.valid_position(x,y) or self.is_revealed(x,y):
            return

        #flip it if a human clicked on it, otherwise set to True
        self.map[x][y][1] = True if not human_click else not self.map[x][y][1]

    # ai functions ---------------------------------------------------------------------------

    # GUI/UI ---------------------------------------------------------------------------------
    def display(self, show_bombs=False):
        self.gd.blit(self.base_img,(0,0))
        scale_up = lambda x,y: (self.scale*x, self.scale*y)
        
        
        for x in range(self.width):
            for y in range(self.height):
                pixel_position = scale_up(32*x + 16, self.window_height -32*y -19 -32)
                
                if show_bombs and self.is_bomb(x,y):
                    img = self.bomb_img

                elif self.is_flagged(x,y):
                    img = self.flag_img

                elif self.is_revealed(x,y):
                    img = self.images[self.number_of(x,y)]

                else:
                    continue
                self.gd.blit(img, pixel_position)
        pygame.display.update()

    def get_mouse_info(self):
        pygame.event.get()
        #mouse clicks
        l,m,r = pygame.mouse.get_pressed()
        l_,m_,r_ = self.mouse
        self.mouse = (l,m,r)

        #mouse pos
        i,j = pygame.mouse.get_pos()
        s = self.scale
        x,y  = (i-16*s)//(32*s) , (self.window_height*s - j -19*s)//(32*s)
        return (x,y),(l and not l_,m and not m_,r and not r_)
        
    # returns "won","playing","lost"
    def run_main_game(self):
        (x,y),(l,m,r) = self.get_mouse_info()
        
        if not self.valid_position(x,y):
            return "playing"

        if l:
            print("clicked",x,y)
            if self.reveal_square(x,y):
                return "lost"
            
        if r:
            self.flag_square(x,y)

        if self.won_game():
            return "won"
            
        return "playing"

    def start(self):
        self.reset_map()
        self.display()
        while True:
            pos,(left_click,m,r) = self.get_mouse_info()
            if left_click and self.valid_position(*pos):
                self.initialise_map(pos)
                self.reveal_square(*pos)
                break
        

    def run(self):
        self.start()
        state = "playing"
        while state=="playing":
            state = self.run_main_game()
            self.display()
            
        if state=="lost":
            print("lost")
            runner().run(lambda :self.display(show_bombs=True)).for_time(3)

        elif state=="won":
            print("won!")
            

    #helper functions ----------------------------------
    def valid_position(self,x,y):
        return 0<=x<self.width and 0<=y<self.height
    
    def is_flagged(self,x,y):
        return self.map[x][y][1]
    
    def is_revealed(self,x,y):
        return self.map[x][y][2]

    def is_bomb(self,x,y):
        return self.number_of(x,y)==-1

    def number_of(self,x,y):
        return self.map[x][y][0]

    def neighbouring_positions(self,x,y):
        return [(i,j) for i in range(x-1,x+2) for j in range(y-1,y+2) if self.valid_position(i,j) and (i,j)!=(x,y)]

    def won_game(self):
        return self.width*self.height - self.num_bombs == sum([self.is_revealed(x,y) for x in range(self.width) for y in range(self.height)])
        
    # ---------------------------------------------------

if __name__=="__main__":       
    pygame.init()
    game = minesweeper()
    runner().run(game.run).forever()
