import pygame,random,time,threading
from timer_py import timer

def second(x):
    return x[1]

def comb(spaces,bombs,so_far=""):
    if not spaces:
        if bombs:
            return []
        return [so_far]
    sp = comb(spaces-1,bombs,so_far+"0")
    bo = comb(spaces-1,bombs-1,so_far+"1") if bombs else []
    return sp + bo 

class cluster:
    def __init__(self,center,coords,n_bombs):
        self.center = center
        self.cluster_coords = coords
        self.num_bombs = n_bombs
        self.num_spaces = len(self.cluster_coords)
        self.combinations = comb(self.num_spaces,self.num_bombs)
        self.valid = {}
  
    def is_consistent(self,other,our_index,their_index):
        our_code,their_code = self.combinations[our_index],other.combinations[their_index]
        consistencies = []
        for (i,pos) in enumerate(self.cluster_coords):
            if pos in other.cluster_coords:
                consistencies.append((i,other.cluster_coords.index(pos)))
        return all([our_code[i]==their_code[j] for i,j in consistencies])

    def analyse(self):
        combs = [self.combinations[i] for i in self.valid.keys()]
        if not combs:
            return [],[]
        reveals,flags = [],[]
        for i in range(self.num_spaces):
            for res in ["1","0"]:
                if all([c[i]==res for c in combs]):
                    if res=="1":
                        flags.append(self.cluster_coords[i])
                    else:
                        reveals.append(self.cluster_coords[i])
        return flags,reveals

    def predict(self):
        combs = [self.combinations[i] for i in self.valid.keys()]
        return max([(self.cluster_coords[x],sum(c[x]=="0" for c in combs)/len(combs)) for x in range(self.num_spaces)],key=second)
    
            

    @staticmethod
    def make_chain(all_clusters):
        
        chains = [[i] for i in range(len(all_clusters[0].combinations))]
        for (i,cluster) in enumerate(all_clusters[1:],start=1):
            new_chains = []
            for prev_chain in chains:
                for our_index in range(len(cluster.combinations)):
                    if all([cluster.is_consistent(all_clusters[x],our_index,prev_chain[x]) for x in range(i)]):
                        new_chains.append(prev_chain +[our_index])
            chains = list(new_chains)
            
                
            
        for chain in chains:
            for i in range(len(chain)):
                all_clusters[i].valid[chain[i]] = 1
        print("clusters:{},chains:{}".format(len(all_clusters),len(chains)))
                                             
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
        self.displaying = False
        #images 
        get_image = lambda x: pygame.transform.rotozoom(pygame.image.load(x+".png"),0,scale)
        self.images = {x:get_image(["zero","one","two","three","four","five","six"][x]) for x in range(-3,7)}
        self.base_img = get_image("base")
        self.bomb_img = get_image("bomb")
        self.flag_img = get_image("flag")
        self.hidden_img = get_image("coveredMine")

         
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
        self.display_square(x,y)
        
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
        self.display_square(x,y)

    # ai functions ---------------------------------------------------------------------------
    def get_frontier(self):
        return [(x,y) for x in range(self.width) for y in range(self.height) if any([not self.is_revealed(i,j) and not self.is_flagged(i,j) for i,j in self.neighbouring_positions(x,y)]) and self.is_revealed(x,y)]
    
    def basic_flag_reveal_detect(self,frontier):
        
        flags,reveals = [],[]
        for (x,y) in frontier:
            near = self.neighbouring_positions(x,y)
            num_flagged = len(list(filter(lambda x:self.is_flagged(*x),near)))
            hidden =  list(filter(lambda x: not self.is_revealed(*x) and not self.is_flagged(*x),near))
            value = self.number_of(x,y) -num_flagged

            if value==len(hidden):
                flags+=hidden

            elif not value:
                reveals+=hidden
                
        return flags,reveals

    def making_clusters(self,frontier):
        clusters = []
        cluster_map = {}
        for (x,y) in frontier:
            near = self.neighbouring_positions(x,y)
            num_flagged = len(list(filter(lambda x:self.is_flagged(*x),near)))
            hidden =  list(filter(lambda x: not self.is_revealed(*x) and not self.is_flagged(*x),near))
            value = self.number_of(x,y) -num_flagged
            c = cluster((x,y),sorted(hidden),value)
            clusters.append(c)
            for coord in hidden:
                cluster_map[coord] = (cluster_map[coord] if coord in cluster_map else []) + [c]
            #pygame.draw.rect(self.gd, (255,255,0),(*self.pixel_position(x,y),30*self.scale,30*self.scale),2*self.scale)
        all_chained = {c.center:0 for c in clusters}
        while not all(all_chained.values()):
            
            cluster_chain = [c for c in clusters if c.center==[key for key,val in all_chained.items() if not val][0]][:1]
            
            while True:
                cands = [x for c in cluster_chain for coord in c.cluster_coords for x in cluster_map[coord]]
                added =False
                for c in cands:
                    if c not in cluster_chain:
                        added=True
                        cluster_chain.append(c)
                        
                if not added:
                    break
            
            for x,y in map(lambda x:x.center,cluster_chain):
                all_chained[(x,y)]=1
            cluster.make_chain(cluster_chain)
        flags,reveals = [],[]
        for c in clusters:
            f,r = c.analyse()
            flags,reveals = flags+f,reveals+r
        
        if not flags and not reveals:
            rev,mark = max([x.predict() for x in clusters],key=second)
            print("predicting a reveal of {} at {}%".format(rev,mark*100))
            return [],[rev]
        return flags, reveals
            
    def run_ai(self, hint,solve,complex_solve, slow=False):
        frontier = self.get_frontier()
        flags, reveals = self.basic_flag_reveal_detect(frontier)
        if complex_solve:
            f,r = self.making_clusters(frontier)
            flags,reveals = flags+f,reveals+r
            
        if hint:
            for colour,candidates in zip([red,green],[flags,reveals]):
                for x,y in candidates:
                    pygame.draw.rect(self.gd, colour,(*self.pixel_position(x,y),30*self.scale,30*self.scale),2*self.scale)
            pygame.display.update()

        if solve:
            if not slow:
                for pos in flags:
                    self.flag_square(*pos,human_click=False)
                for pos in reveals:
                    if self.reveal_square(*pos):
                        return "lost"
            else:
                if flags:self.flag_square(*flags[0],human_click=False)
                elif reveals:self.reveal_square(*reveals[0])
        return "won" if self.won_game() else "playing"

    # GUI/UI ---------------------------------------------------------------------------------
    def pixel_position(self,x,y):
        scale_up = lambda x,y: (self.scale*x, self.scale*y)
        return scale_up(32*x + 16, self.window_height -32*y -19 -32)

    def display_square(self,x,y,show_bombs=False):
        if show_bombs and self.is_bomb(x,y):
            img = self.bomb_img

        elif self.is_flagged(x,y):
            img = self.flag_img

        elif self.is_revealed(x,y):
            img = self.images[self.number_of(x,y)]

        else:
            img = self.hidden_img
        self.gd.blit(img, self.pixel_position(x,y))
        
        
    def display(self, show_bombs=False,starting=False):
        self.displaying = True
        self.gd.blit(self.base_img,(0,0))
        for x in range(self.width):
            for y in range(self.height):
                self.display_square(x,y,show_bombs)
        pygame.display.update()
        self.displaying = False

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
        if not any((l,m,r)):
            return "playing",False
        
        if not self.valid_position(x,y):
            return "playing",False

        if l:
            if self.reveal_square(x,y):
                return "lost",True
        if r:
            self.flag_square(x,y)

        if m:
            return "playing",True


        if self.won_game():
            return "won",False
            
        return "playing",any((l,m,r))

    def start(self):
        self.reset_map()
        self.display(starting=True)
        while True:
            pos,(left_click,m,r) = self.get_mouse_info()
            if left_click and self.valid_position(*pos):
                self.initialise_map(pos)
                self.reveal_square(*pos)
                break
        self.display()
        

    def run(self):
        self.start()
        state = "playing"
    
        while state=="playing":
            state,change = self.run_main_game()
            pressed = list(pygame.key.get_pressed())
            k_pressed = [pressed[keys[x]] for x in ["hint","solve","complex solve","show_frontier","display"]]

            if any(k_pressed[:-2]):
                state = self.run_ai(*k_pressed[:-2])

            if k_pressed[-2]:
                for (x,y) in self.get_frontier():
                    pygame.draw.rect(self.gd, blue,(*self.pixel_position(x,y),30*self.scale,30*self.scale),2*self.scale)

            if k_pressed[-1]:
                self.display()

            pygame.display.update()
            
            
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

red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)

keys = {"hint":11, "solve":22, "complex solve":225, "show_frontier":9,"display":7}
# Press H for a Hint, S to solve, and Hold down Shift for a complex hint/solve.

if __name__=="__main__":       
    pygame.init()
    
    game = minesweeper()
##    while True:
##        pygame.event.get()
##        res = [(i,x) for (i,x) in enumerate(list(pygame.key.get_pressed())) if x]
##        if res:
##            print(res)
##            pressed = list(pygame.key.get_pressed())
##            print([pressed[keys[x]] for x in ["hint","solve","complex solve"]])
    runner().run(game.run).forever()
