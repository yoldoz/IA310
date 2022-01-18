import math
import random 
from collections import defaultdict
import matplotlib.pyplot as plt
import tornado, tornado.ioloop
import mesa
import numpy
import pandas
import uuid
from mesa import space
from mesa.batchrunner import BatchRunner, BatchRunnerMP
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from mesa.visualization.ModularVisualization import ModularServer, VisualizationElement, UserSettableParameter
from mesa.visualization.modules import ChartModule, TextElement




def Distance(l,v):
    
    d =((l.pos[0]-v.pos[0])**2+(l.pos[1]-v.pos[1])**2)**(1/2)
    
    return (d)

def number_population(model):
    #h=0
    #for i in model.schedule.agents : 
        #h+=1
    return (model.schedule.get_agent_count())
def number_lycanthropes(model):
    l=0
    for i in model.schedule.agents : 
        if (isinstance(i,Villager)) :
            if (i.lycanthrope == True) :
                l+=1
    return l
def number_humans(model):
    h=0
    for i in model.schedule.agents : 
        if (isinstance(i,Villager)) :
            if (i.lycanthrope == False) :
                
                h+=1
    return h

def number_transformed(model):
    t=0
    for i in model.schedule.agents : 
        if (isinstance(i,Villager)) :
            if (i.transformed == True) :
                
                t+=1
    return t



class Village(mesa.Model):
    def __init__(self, n_villagers,n_lycanthropes,n_clerics,n_hunters):
        mesa.Model.__init__(self)
        self.space = mesa.space.ContinuousSpace(600, 600, False)
        self.schedule = RandomActivation(self)
        self.datacollector = DataCollector(model_reporters={"Humans": number_humans,
                                            "Were-wolves": number_lycanthropes,
                                            "Population": number_population,
                                            "Transformed": number_transformed})             
        for _ in range(n_villagers):
            self.schedule.add(Villager(random.random() * 500, random.random() * 500, 10, int(uuid.uuid1()), self,False ))
        for _ in range(n_lycanthropes):
            self.schedule.add(Villager(random.random() * 500, random.random() * 500, 10, int(uuid.uuid1()), self,True))    
        for _ in range(n_clerics):
            self.schedule.add(Cleric(random.random() * 500, random.random() * 500, 10, int(uuid.uuid1()), self)) 
        for _ in range(n_hunters):
            self.schedule.add(Hunter(random.random() * 500, random.random() * 500, 10, int(uuid.uuid1()), self)) 

    def step(self):
        
        self.schedule.step()
        self.datacollector.collect(self)
        if self.schedule.steps >= 1000:
            self.running = False




class  Cleric(mesa.Agent) :
    def __init__(self, x, y, speed, unique_id: int, model: Village ):
        super().__init__(unique_id, model)
        self.pos = (x, y)
        self.speed = speed
        self.model = model
    
        

    def portrayal_method(self):
        color = "green"
        r = 3
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": color,
                     "r": r}
        return portrayal

    def step(self):     
        for j in self.model.schedule.agents : 
            if(isinstance(j,Villager)):
                d = Distance(self,j)
                if (d<= 30)and(j.transformed==False)and(j.lycanthrope==True) :
                    
                    j.lycanthrope = False
                    break
        
        self.pos = wander(self.pos[0], self.pos[1], self.speed, self.model)



class Hunter(mesa.Agent):
    def __init__(self, x, y, speed, unique_id: int, model: Village ):
        super().__init__(unique_id, model)
        self.pos = (x, y)
        self.speed = speed
        self.model = model
    
        

    def portrayal_method(self):
        color = "black"
        r = 3
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": color,
                     "r": r}
        return portrayal

    def step(self):     
        for j in self.model.schedule.agents : 
            if(isinstance(j,Villager)):
                d = Distance(self,j)
                if (d<= 40)and(j.transformed==True)and(j.lycanthrope==True) :
                    
                    self.model.schedule.remove(j)
                    
                    break
        
        self.pos = wander(self.pos[0], self.pos[1], self.speed, self.model)



class ContinuousCanvas(VisualizationElement):
    local_includes = [
        "./js/simple_continuous_canvas.js",
    ]

    def __init__(self, canvas_height=500,
                 canvas_width=500, instantiate=True):
        VisualizationElement.__init__(self)
        self.canvas_height = canvas_height
        self.canvas_width = canvas_width
        self.identifier = "space-canvas"
        if (instantiate):
            new_element = ("new Simple_Continuous_Module({}, {},'{}')".
                           format(self.canvas_width, self.canvas_height, self.identifier))
            self.js_code = "elements.push(" + new_element + ");"

    def portrayal_method(self, obj):
        return obj.portrayal_method()

    def render(self, model):
        representation = defaultdict(list)
        for obj in model.schedule.agents:
            portrayal = self.portrayal_method(obj)
            if portrayal:
                portrayal["x"] = ((obj.pos[0] - model.space.x_min) /
                                  (model.space.x_max - model.space.x_min))
                portrayal["y"] = ((obj.pos[1] - model.space.y_min) /
                                  (model.space.y_max - model.space.y_min))
            representation[portrayal["Layer"]].append(portrayal)
        return representation


def wander(x, y, speed, model):
    r = random.random() * math.pi * 2
    new_x = max(min(x + math.cos(r) * speed, model.space.x_max), model.space.x_min)
    new_y = max(min(y + math.sin(r) * speed, model.space.y_max), model.space.y_min)

    return new_x, new_y



class Villager(mesa.Agent):
    def __init__(self, x, y, speed, unique_id: int, model: Village, lycanthrope : bool ):
        super().__init__(unique_id, model)
        self.pos = (x, y)
        self.speed = speed
        self.model = model
        self.lycanthrope = lycanthrope
        self.transformed = False

    def portrayal_method(self):
        if self.lycanthrope == False : 
            color = "blue"
        elif self.lycanthrope == True :
            color = "red"
            
        if self.transformed == False :
            r = 3
        else :
            r = 6
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": color,
                     "r": r}
        return portrayal

    def step(self):
        
        if (self.transformed ==True):
            for j in self.model.schedule.agents : 
                if(isinstance(j,Villager)):
                    d = Distance(self,j)
                    if (d<= 40)and(j.lycanthrope==False) :
                        j.lycanthrope = True
                        break
            
        if (self.lycanthrope==True)  :
            
            rand = random.randint(0,10)
            if (rand == 1) :
                self.transformed = not(self.transformed)
                
        self.pos = wander(self.pos[0], self.pos[1], self.speed, self.model)
        
            

def run_single_server():
    chart = ChartModule([{'Label': 'Humans', 'Color': 'blue'},
                     {'Label': 'Were-wolves', 'Color': 'red'},
                     {'Label': 'Population', 'Color': 'orange'},
                    {'Label': 'Transformed', 'Color': 'black'}
                     ],data_collector_name='datacollector')

    
    model_params = {
    "n_villagers": UserSettableParameter("slider", "Number of villagers", 30, 25, 40, 1),
    "n_lycanthropes": UserSettableParameter("slider", "Number of lycanthropes", 5, 4, 9, 2),
    "n_clerics": UserSettableParameter("slider", "Number of clerics", 3, 1, 5, 0),
    "n_hunters": UserSettableParameter("slider", "Number of hunters", 2, 1, 5, 0),}
    server = ModularServer(Village,
                           [ContinuousCanvas(),chart],
                           "Village",
                          model_params)
    
    server.port = 8521
    server.launch()
    

def run_batch():
    d = {"n_villagers": [50],"n_lycanthropes": [5],"n_clerics": range(0, 6, 1),"n_hunters":[1]}
    fixed_params = dict(n_villagers=30, n_lycanthropes =4, n_hunters = 2)
    variable_params = dict(n_clerics=range(0, 6, 1))
    batch=BatchRunner(Village,  variable_parameters=variable_params, 
                        fixed_parameters=fixed_params,model_reporters={"Humans": number_humans,
                                            "Were-wolves": number_lycanthropes,
                                            "Population": number_population,
                                            "Transformed": number_transformed})
    batch.run_all()
    res =batch.get_model_vars_dataframe()
    
    print(res)
    plt.scatter(res['n_clerics'], res['Humans'],color='blue',label='humans')
    plt.xlim(0,5)
    plt.scatter(res['n_clerics'], res['Were-wolves'],color='red', label='lycanthropes')
    plt.xlim(0,5)
    plt.xlabel('nombre de clerics')
    plt.legend()
    
    

    
if __name__ == "__main__":
    run_single_server()
    #run_batch()
    

