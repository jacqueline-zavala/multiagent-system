from mesa import Agent, Model, model
from mesa.time import RandomActivation
from mesa.space import Grid, SingleGrid
from mesa.space import MultiGrid
from collections import deque
import random

class AgentCar(Agent):
    def __init__(self, unique_id, model, origen, orientation, trafficLight,color="black"):
        super().__init__(unique_id, model)
        self.previous = "Normal"
        self.curr = "Normal"
        self.origin = origen
        self.orientation = orientation
        self.trafficLight = trafficLight
        self.destination = self.setDestination(model)
        self.color = color

    # Escoger de manera aleatoria un destino para el auto, exluyendo aquel que
    # Involucra una vuelta en U    
    def setDestination(self, model):
        exclude = {(11,0):(10,0),(21,10):(21,11),(11,21):(10,21),(0,10):(0,11)}
        d = self.random.choice(model.possibleDestinations)
        while exclude.get(self.origin) == d:
             d = self.random.choice(model.possibleDestinations)
        return d
    
    def moveCar(self, cell):
        # Aquí se mueve el auto
        self.model.grid.move_agent(self, cell)
        if self.orientation == "Arriba" or self.orientation == "Abajo":
            if self.pos[1] == self.destination[1]:
                if self.pos[0] < self.destination[0]:
                    self.orientation = "Derecha"
                elif self.pos[0] > self.destination[0]:
                    self.orientation = "Izquierda"
        elif self.orientation == "Izquierda" or self.orientation == "Derecha":
            if self.pos[0] == self.destination[0]:
                if self.pos[1] < self.destination[1]:
                    self.orientation = "Arriba"
                elif self.pos[1] > self.destination[1]:
                    self.orientation = "Abajo"
    
    
    def checkMove(self):
        # Avanza y luego checa si debe rotar
        nextPos = self.getNextPos()
        listAgents = self.model.grid.get_cell_list_contents(nextPos)
        
        for a in listAgents:
            if isinstance(a, AgentCar):
                listAgents = self.model.grid.get_cell_list_contents(self.pos)
                for a in listAgents:
                    if isinstance(a, AgentCell):
                        self.previous = self.curr
                        self.curr = a.typeCell
                return
        
        self.moveCar(nextPos)
        listAgents = self.model.grid.get_cell_list_contents(self.pos)
        for a in listAgents:
            if isinstance(a, AgentCell):
                self.previous = self.curr
                self.curr = a.typeCell
    
    def getNextPos(self):
        if(self.orientation == "Arriba"):
            position = list(self.pos)
            position[1] += 1
            return tuple(position)
        elif (self.orientation == "Abajo"):
            position = list(self.pos)
            position[1] -= 1
            return tuple(position)
        elif (self.orientation == "Izquierda"):
            position = list(self.pos)
            position[0] -= 1
            return tuple(position)
        elif (self.orientation == "Derecha"):
            position = list(self.pos)
            position[0] += 1
            return tuple(position)

    def notifyTrafficLight(self):
        # Encontrar el semáforo
        listAgents = self.model.grid.get_cell_list_contents(self.pos)

        for a in listAgents:
            if isinstance(a, AgentCell):
                a.trafficLight.carArrived()
                a.trafficLight.carCount += 1
                return

    def findTrafficLight(self):
        listAgents = self.model.grid.get_cell_list_contents(self.pos)

        for a in listAgents:
            if isinstance(a, AgentCell):
                return a.trafficLight
    
    def delete(self):
        #(10,0),(21,10),(11,21),(0,11)
        if self.pos in [(10,0),(21,10),(11,21),(0,11)]:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return True
        
            
    
    def step(self):
        if self.delete():
            return

        if(self.pos == self.destination):
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return
        
        # Evita que el auto se pueda mover dos veces en el mismo step
        if not(self.previous == "Semaforo" and self.curr == "Semaforo"):
            self.checkMove()
        
        
        # Arq 1. Si tengo coche adelante, no avanzo (implícito)
        # Arq 2. Si estoy un una celda de aviso y mi prev es una normal 
        # Comunicarme con semáforo
        if(self.previous == "Normal" and self.curr == "Aviso"):
            self.notifyTrafficLight()
            #return
            
        # Arq 3. Si estoy en una celda de semáforo y mi prev es una de aviso
        # Detenerse
        elif(self.previous == "Aviso" and self.curr == "Semaforo"):
            self.previous = self.curr
            self.curr = "Semaforo"
            #return
        
        elif(self.previous == "Aviso" and self.curr == "Aviso"):
            if(self.trafficLight.unique_id not in AgentTrafficLight.turns):
                AgentTrafficLight.turns.append(self.trafficLight.unique_id)

        # Si estoy en una celda de semáforo y mi prev es una celda de semáforo
        elif(self.previous == "Semaforo" and self.curr == "Semaforo"):
            tl = self.findTrafficLight()
            # Arq 4. Si es verde el sem, intento avanzar
            if tl.color == "Verde":
                self.checkMove()
                return
            # Arq 5. Si es rojo no me muevo
            elif tl.color == "Rojo":
                return

        # Arq 6. Si estoy en una celda de intersección y mi prev es una celda de semáforo
        # Llamar a move y res tar a cars de semáforo
        #elif(self.curr == "Interseccion" and self.previous == "Semaforo"):
            # tl = self.findTrafficLight()
            # tl.carCount -= 1
            #return
            
        # Si estoy en una celda normal y salí de la celda de intersección, le restamos al carCount
        elif(self.curr == "Normal" and self.previous == "Interseccion"):
            self.trafficLight.carCount -= 1
        # Arq 7. Si estoy en una celda de intersección y mi prev es una celda de intersección
        # moverme (implícito)

        '''
        if(self.pos == self.destination):
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return
            
        self.checkMove()
        '''     

class AgentCell(Agent):
    def __init__(self, unique_id, model, typeCell,trafficLight=None):
        super().__init__(unique_id, model)
        self.typeCell = typeCell
        self.trafficLight = trafficLight
    
    def step(self):
        pass
        
class AgentObstacle(Agent):
    def __init__(self,unique_id,model):
        super().__init__(unique_id, model)
    
    def step(self):
        pass
    

class AgentTrafficLight(Agent):

    turns = deque()
    tlights = []

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        AgentTrafficLight.tlights.append(self)
        self.carCount = 0
        self.color = "Amarillo"
        self.isMyTurn = False
        self.timeGreen = 10
    

    def carArrived(self):
        if(self.carCount == 0):
            if not self.isMyTurn:
                if self.unique_id not in AgentTrafficLight.turns:
                    AgentTrafficLight.turns.append(self.unique_id)

    def stepTrafficLight(self):
        # print("Step Semaforo")
        if AgentTrafficLight.turns:
            self.isMyTurn = AgentTrafficLight.turns[0] == self.unique_id
        else:
            self.isMyTurn = False
        print(f'Semáforo {self.unique_id}: {self.color}, is my turn: {self.isMyTurn}')

        
        # Arq. 2. Si no es mi turno, llega un coche y el contador de coches < 1, pide turno
        #Implementado en método carArrived
        
        # Arq 5.Si mi tiempo de turno acaba de terminar y mi contador de coches es mayor a 0
        if self.isMyTurn and self.timeGreen == 0 and self.carCount > 0:
            self.color = "Rojo"
            AgentTrafficLight.turns.popleft()
            AgentTrafficLight.turns.append(self.unique_id)
            self.timeGreen = 10

        # Arq 6. Si mi tiempo de turno acaba de terminar y mi contador de coches igual 0
        elif self.isMyTurn and self.timeGreen == 0 and self.carCount <= 0:
            self.color = "Rojo"
            AgentTrafficLight.turns.popleft()
            self.timeGreen = 10


        # Arq 7, si es mi turno y ya no hay autos, cambiar a rojo y quitar mi turno
        elif self.isMyTurn and self.carCount == 0:
            self.color = "Rojo"
            self.timeGreen = 10
            AgentTrafficLight.turns.popleft()

        # Arq 4, si es mi turno, cambiar a verde
        elif self.isMyTurn:
            self.color = "Verde"
            self.timeGreen -= 1

        # Arq 1, si no hay autos en ningún semáforo, amarillo
        elif not AgentTrafficLight.turns:
            self.color = "Amarillo"

        # Arq. 3 Si no es mi turno y en algún otro semáforo hay autos debo permanecer en rojo
        elif not self.isMyTurn:
            self.color = "Rojo"
        
        print(AgentTrafficLight.turns)
        print(f'Car count {self.carCount}, green: {self.timeGreen}')
    
    def step(self):
        pass
        
        


class ModelStreet(Model):
    def __init__(self,nCars, width, length): # Matriz de 22 x 22    
        # Número de Autos
        self.numCars = nCars
        self.uniqueIDs = 1
        # Número de Semáforos
        self.numTrafficLights = 4
        # Crear grid
        self.grid = MultiGrid(width,length,False)
        # Coordenadas de las entradas a la intersección
        self.possibleStartingPoints = [(11,0),(21,11),(0,10),(10,21)]
        # Coordenadas de las salidas de la intersección
        self.possibleDestinations = [(10,0),(21,10),(11,21),(0,11)]
        self.schedule = RandomActivation(self)
        self.running = True
        
        # Semáforos
        self.tl1 = None
        self.tl2 = None
        self.tl3 = None
        self.tl4 = None
        
        
        # Construir paredes
        for i in range(0,22):
            # Construir paredes verticales
            # En [9,0-9 y 12-21] y [12,0-9 y 12-21]
            if not(i > 9 and i < 12):
                a = AgentObstacle(self.uniqueIDs,self)
                self.uniqueIDs += 1
                b = AgentObstacle(self.uniqueIDs,self)
                self.uniqueIDs += 1
                self.schedule.add(a)
                self.schedule.add(b)
                self.grid.place_agent(a,(9,i))
                self.grid.place_agent(b,(12,i))
            # Construir paredes horizontales
            # En [0-8 y 13-21, 9] y [0-8 y 13-21, 12]
            if not(i > 8 and i < 13):
                a = AgentObstacle(self.uniqueIDs,self)
                self.uniqueIDs += 1
                b = AgentObstacle(self.uniqueIDs,self)
                self.uniqueIDs += 1
                self.schedule.add(a)
                self.schedule.add(b)
                self.grid.place_agent(a,(i,9))
                self.grid.place_agent(b,(i,12))
        
        
        # Coordenadas de celdas de semáforo (9,10) (10,12) (11,9) (12,11)
        # Colocar celdas de semáforo y sus respectivos semáforos
        tl1 = AgentTrafficLight(self.uniqueIDs,self)
        self.grid.place_agent(tl1, (8,8))
        self.uniqueIDs += 1
        tl2 = AgentTrafficLight(self.uniqueIDs,self)
        self.uniqueIDs += 1
        self.grid.place_agent(tl2, (8,13))
        tl3 = AgentTrafficLight(self.uniqueIDs,self)
        self.grid.place_agent(tl3, (13,8))
        self.uniqueIDs += 1
        tl4 = AgentTrafficLight(self.uniqueIDs,self)
        self.grid.place_agent(tl4, (13,13))
        self.uniqueIDs += 1
        self.tl1 = tl1
        self.tl2 = tl2
        self.tl3 = tl3
        self.tl4 = tl4
       
        cellS1 = AgentCell(self.uniqueIDs, self, "Semaforo", tl1)
        self.uniqueIDs += 1
        cellS2 = AgentCell(self.uniqueIDs, self, "Semaforo", tl2)
        self.uniqueIDs += 1
        cellS3 = AgentCell(self.uniqueIDs, self, "Semaforo", tl3)
        self.uniqueIDs += 1
        cellS4 = AgentCell(self.uniqueIDs, self, "Semaforo", tl4)
        self.uniqueIDs += 1
       

        # Agregar celdas
        self.schedule.add(cellS1)
        self.schedule.add(cellS2)
        self.schedule.add(cellS3)
        self.schedule.add(cellS4)
        # Agregar semáforos
        self.schedule.add(tl1)
        self.schedule.add(tl2)
        self.schedule.add(tl3)
        self.schedule.add(tl4)
        
        self.grid.place_agent(cellS1, (9,10))
        self.grid.place_agent(cellS2, (10,12))
        self.grid.place_agent(cellS3, (11,9))
        self.grid.place_agent(cellS4, (12,11))

                
        # Coordenadas de celdas aviso (8,10) (11,8) (13,11) (10,13)
        # Colocar celdas de aviso
        cellA1 = AgentCell(self.uniqueIDs, self, "Aviso", tl1)
        self.uniqueIDs += 1
        cellA2 = AgentCell(self.uniqueIDs, self, "Aviso", tl3)
        self.uniqueIDs += 1
        cellA3 = AgentCell(self.uniqueIDs, self, "Aviso", tl4)
        self.uniqueIDs += 1
        cellA4 = AgentCell(self.uniqueIDs, self, "Aviso", tl2)
        self.uniqueIDs += 1
        self.schedule.add(cellA1)
        self.schedule.add(cellA2)
        self.schedule.add(cellA3)
        self.schedule.add(cellA4)
        self.grid.place_agent(cellA1, (8,10))
        self.grid.place_agent(cellA2, (11,8))
        self.grid.place_agent(cellA3, (13,11))
        self.grid.place_agent(cellA4, (10,13))
        self.trafficLights = [tl1,tl2,tl3,tl4]
        
        # Coordenadas intersección (10,10) (11,10) (10,11) (11,11)
        # Colocar celdas de intersección
        cellI1 = AgentCell(self.uniqueIDs, self, "Interseccion", tl1)
        self.uniqueIDs += 1
        cellI2 = AgentCell(self.uniqueIDs, self, "Interseccion", tl3)
        self.uniqueIDs += 1
        cellI3 = AgentCell(self.uniqueIDs, self, "Interseccion", tl2)
        self.uniqueIDs += 1
        cellI4 = AgentCell(self.uniqueIDs, self, "Interseccion", tl4)
        self.uniqueIDs += 1
        self.schedule.add(cellI1)
        self.schedule.add(cellI2)
        self.schedule.add(cellI3)
        self.schedule.add(cellI4)
        self.grid.place_agent(cellI1, (10,10))
        self.grid.place_agent(cellI2, (11,10))
        self.grid.place_agent(cellI3, (10,11))
        self.grid.place_agent(cellI4, (11,11))   

        # Coordenadas celdas normales (9,11) (10,9) (12,10) (11,12)
        # Colocar celdas de intersección
        cellN1 = AgentCell(self.uniqueIDs, self, "Normal")
        self.uniqueIDs += 1
        cellN2 = AgentCell(self.uniqueIDs, self, "Normal")
        self.uniqueIDs += 1
        cellN3 = AgentCell(self.uniqueIDs, self, "Normal")
        self.uniqueIDs += 1
        cellN4 = AgentCell(self.uniqueIDs, self, "Normal")
        self.uniqueIDs += 1
        cellN5 = AgentCell(self.uniqueIDs, self, "Normal")
        self.uniqueIDs += 1
        cellN6 = AgentCell(self.uniqueIDs, self, "Normal")
        self.uniqueIDs += 1
        cellN7 = AgentCell(self.uniqueIDs, self, "Normal")
        self.uniqueIDs += 1
        cellN8 = AgentCell(self.uniqueIDs, self, "Normal")
        self.uniqueIDs += 1
        self.schedule.add(cellN1)
        self.schedule.add(cellN2)
        self.schedule.add(cellN3)
        self.schedule.add(cellN4)
        self.schedule.add(cellN5)
        self.schedule.add(cellN6)
        self.schedule.add(cellN7)
        self.schedule.add(cellN8)
        self.grid.place_agent(cellN1, (9,11))
        self.grid.place_agent(cellN2, (10,9))
        self.grid.place_agent(cellN3, (12,10))
        self.grid.place_agent(cellN4, (11,12))
        self.grid.place_agent(cellN5, (8,11))
        self.grid.place_agent(cellN6, (10,8))
        self.grid.place_agent(cellN7, (13,10))
        self.grid.place_agent(cellN8, (11,13))     


    # Si el coche parte de (0,10) -> tl1
    # Si el coche parte de (11,0) -> tl3
    # Si el coche parte de (21,11) -> tl4
    # Si el coche parte de (10,21) -> tl2  

    def addAgents(self):
        """
        Para cada entrada a la intersección,
        checar si la celda está disponible,
        elegir de manera random entre True/False
        para decidir si agregar un nuevo agente
        """
        #boolList = [self.random.choice([True, False,False,False,False]), self.random.choice([True, False,False,False,False]), self.random.choice([True, False,False,False,False]), self.random.choice([True, False,False,False,False])]
        b1,b2,b3,b4 = random.choices(population=[True,False], weights=[0.1, 0.9],k=4)
        
        if(b1):
            cell = self.grid.get_cell_list_contents((11,0))
            if(not cell):
                b = AgentCar(self.uniqueIDs, self, (11,0), "Arriba",self.tl3,"purple")
                self.uniqueIDs += 1
                self.schedule.add(b)
                self.grid.place_agent(b, (11,0))
        
        if(b2):
            cell = self.grid.get_cell_list_contents((21,11))
            if(not cell):
                b = AgentCar(self.uniqueIDs, self, (21,11), "Izquierda",self.tl4)
                self.uniqueIDs += 1
                self.schedule.add(b)
                self.grid.place_agent(b, (21,11))

        if(b3):
            cell = self.grid.get_cell_list_contents((0,10))
            if(not cell):
                b = AgentCar(self.uniqueIDs, self, (0,10), "Derecha",self.tl1,"brown")
                self.uniqueIDs += 1
                self.schedule.add(b)
                self.grid.place_agent(b, (0,10))
        
        if(b4):
            cell = self.grid.get_cell_list_contents((10,21))
            if(not cell):
                b = AgentCar(self.uniqueIDs, self, (10,21), "Abajo", self.tl2,"orange")
                self.uniqueIDs += 1
                self.schedule.add(b)
                self.grid.place_agent(b, (10,21))

    def step(self):
        self.schedule.step()
        for lights in range(len(self.trafficLights)):
            self.trafficLights[lights].stepTrafficLight()
        self.addAgents()