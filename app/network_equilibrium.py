import numpy as np
import cvxpy as cp
import gurobipy as gp
from gurobipy import GRB
import types


class NetworkEquilibrium:
    # Suppose all the input are the numpy variables
    def __init__(self, NetworkLink = None, NetworkNode = None, ChagingStation = None, myOD = None):
        self.NetworkLink = 0
        self.NetworkNode = 0
        self.OriginNode = 0
        self.ChargingStation = 0
        self.ChargingStationLocation = 0
        self.ChargingList = []
        self.ChargingSpeed = 0
        self.ChargingWaiting =0
        self.ChargingAmount = 0
        self.OD = 0
        self.ODDemand = 0
        self.ODSize = 0
        self.ODCost = 0
        self.PathFlow = 0
        self.LinkFlow = 0
        self.LinkSize = 0
        self.LinkTravelTime = 0
        self.NodeSize = 0
        self.ChargingDemand = 0
        self.PathSet = 0
        self.ChargingSet = 0
        self.ChargingCost = 0
        self.PathToOD = 0
        self.PathCost = 0
        self.NodeLinkMatrix = 0
        self.SafeSoc = 20
        self.InitialSoc = 60
        self.MaxSoc = 200
        self.LinkEleConsu = 0
        self.UEObjective = 0
        self.NetworkLoad = 0

    def ParameterUpdate(self,):
        self.LinkSize = np.size(self.NetworkLink,0)
        self.NodeSize = np.size(self.NetworkNode,0)  
        self.NodeLinkMatrix = np.zeros((self.NodeSize,self.LinkSize))
        self.LinkStartMatrix = np.zeros((self.LinkSize,self.NodeSize))
        self.LinkEndMatrix = np.zeros((self.LinkSize,self.NodeSize))
        self.LinkEleConsu = np.zeros(self.LinkSize)
        self.LinkTravelTime = np.zeros(self.LinkSize)

        for i in range(self.LinkSize):
            self.NodeLinkMatrix[int(self.NetworkLink[i,0]),i] = 1
            self.NodeLinkMatrix[int(self.NetworkLink[i,1]),i] = -1
            self.LinkStartMatrix[i,int(self.NetworkLink[i,0])] = 1
            self.LinkEndMatrix[i,int(self.NetworkLink[i,1])] = 1
            self.LinkEleConsu[i] = self.NetworkLink[i,4]
            self.LinkTravelTime[i] = self.NetworkLink[i,2]

    def SetLinks(self, Links):
        LinkSize = len(Links)
        InfoSize = len(Links[0])
        self.NetworkLink = np.zeros([2*LinkSize,InfoSize])
        Links = np.array(Links)
        self.NetworkLink[0:LinkSize,2:InfoSize] = Links[:,2:InfoSize]
        self.NetworkLink[LinkSize:2*LinkSize,2:InfoSize] = Links[:,2:InfoSize]
        for i in range(len(Links)):
            self.NetworkLink[i,0] =  self.OriginRealNodeMatching[int(Links[i,0])]
            self.NetworkLink[i,1] =  self.OriginRealNodeMatching[int(Links[i,1])]
            self.NetworkLink[i+LinkSize,0] =  self.OriginRealNodeMatching[int(Links[i,1])]
            self.NetworkLink[i+LinkSize,1] =  self.OriginRealNodeMatching[int(Links[i,0])]
            self.NetworkLink[i+LinkSize,InfoSize-1] =  self.NetworkLink[i,InfoSize-1]+LinkSize 

    def SetNodes(self,Nodes):
        self.OriginNode = Nodes
        self.OriginRealNodeMatching = np.zeros([int(max(Nodes[:,0])+1),1])
        NodeSize = len(Nodes)
        self.NodeSize = NodeSize
        self.NetworkNode = np.zeros([NodeSize,1])
        for i in range(NodeSize):
            self.OriginNode[i][0] = int(self.OriginNode[i][0])
            self.NetworkNode[i] = [i]
        
        for i in range(NodeSize):
            self.OriginRealNodeMatching[int(Nodes[i,0])] = i

    # 充电站的方案我这边自己布置


    def SetChargingStations(self,ChargingStations):
        if type(ChargingStations) == str:
            if ChargingStations == 'low':
                ChargingStations = 30.0
            elif ChargingStations == 'middle':
                ChargingStations = 60.0
            else:
                ChargingStations = 90.0
        
        if type(ChargingStations) == float or type(ChargingStations)==int:
            self.ChargingStation = np.zeros([self.NodeSize,4])
            self.ChargingSpeed = np.zeros(self.NodeSize)
            self.ChargingWaiting = np.zeros(self.NodeSize)
            self.ChargingStationLocation = np.zeros(self.NodeSize)
            for i in range(self.NodeSize):
                if np.random.rand() < ChargingStations/100:
                    self.ChargingStation[i,:] = [1,100,1,5]
                    self.ChargingStationLocation[i] = self.ChargingStation[i,0]
                    self.ChargingSpeed[i] = self.ChargingStation[i,2]
                    self.ChargingWaiting[i] = self.ChargingStation[i,3]     
                    self.ChargingList.append(i)
        else:
            self.ChargingStation = ChargingStations
            self.ChargingSpeed = np.zeros(self.NodeSize)
            self.ChargingWaiting = np.zeros(self.NodeSize)
            self.ChargingStationLocation = np.zeros(self.NodeSize)
            for i in range(self.NodeSize):
                self.ChargingStationLocation[i] = self.ChargingStation[i,0]
                self.ChargingSpeed[i] = self.ChargingStation[i,2]
                self.ChargingWaiting[i] = self.ChargingStation[i,3]
                self.ChargingList.append(i)
    
    def SetOD(self,myOD):
        self.OD = myOD
        for i in range(len(myOD)):
            self.OD[i,0] = self.OriginRealNodeMatching[int(self.OD[i,0])]
            self.OD[i,1] = self.OriginRealNodeMatching[int(self.OD[i,1])]
        self.ODDemand = myOD[:,2]
        self.ODSize = np.size(self.OD,0)
        self.ODCost = 100000000.0 * np.ones(self.ODSize)
     
        
    def FeasibilityCheck(self,):
        # Check if all the condition is feasible for solving an equilibrium condition
        # Besides, regulating the formate for computation deta
        for i in range(self.ODSize):
            od = self.OD[i]
            # print(i)
            if len(od)>=6:
                Flag, LinkChoice, ChargingStationChoice,  ChargingAmountChoice,  BatteryLevel, ChargingCost = self.EVShortestPath(od,od[3:6])
            else:
                Flag, LinkChoice, ChargingStationChoice,  ChargingAmountChoice,  BatteryLevel, ChargingCost = self.EVShortestPath(od)
            if Flag is not True:
                return False
            if i == 0:
                self.PathSet = LinkChoice
                self.PathToOD = i
                self.ChargingCost = ChargingCost
                self.ChargingSet = ChargingAmountChoice
            else:
                self.PathSet = np.row_stack([self.PathSet,LinkChoice])
                self.PathToOD = np.row_stack([self.PathToOD,i])
                self.ChargingCost = np.row_stack([self.ChargingCost,ChargingCost])
                self.ChargingSet = np.row_stack([self.ChargingSet,ChargingAmountChoice])

        return True


    def EVShortestPath(self,od,SOCInfo=None):
        if SOCInfo is not None:
            InitialSoc = SOCInfo[0]
            SafeSoc = SOCInfo[1]
            MaxSoc = SOCInfo[2]
        else:
            SafeSoc = self.SafeSoc
            InitialSoc = self.InitialSoc
            MaxSoc = self.MaxSoc

        sp = gp.Model("EVShortestPathMIP")
        sp.setParam('OutputFlag',0)
        ## Variables
        xl = sp.addMVar(shape = self.LinkSize, vtype = GRB.BINARY, name = "linkchoice" )
        xc = sp.addMVar(shape = self.NodeSize, vtype = GRB.BINARY, name = "chargingstationchoice")
        xa = sp.addMVar(shape = self.NodeSize, lb = 0, ub = MaxSoc-SafeSoc, vtype = GRB.CONTINUOUS, name = "chargingamountchoice")
        yl = sp.addMVar(shape = self.NodeSize, lb = SafeSoc,  ub = MaxSoc,  vtype = GRB.CONTINUOUS, name = "batterylevel")
        
        ## Parameters
        Ers = np.zeros(self.NodeSize)
        Ers[int(od[0])] = 1
        Ers[int(od[1])] = -1
        #print(Ers)
        

        ## Constr
        sp.addConstr(self.NodeLinkMatrix @ xl == Ers)
        sp.addConstr(self.LinkStartMatrix @ yl + self.LinkStartMatrix @ xa - self.LinkEleConsu - self.LinkEndMatrix @ yl <= MaxSoc*(1-xl)) #MaxSoc*(1-xl)
        sp.addConstr(self.LinkStartMatrix @ yl + self.LinkStartMatrix @ xa - self.LinkEleConsu - self.LinkEndMatrix @ yl >= MaxSoc*(xl-1))
        sp.addConstr(xa <= (MaxSoc-SafeSoc)*xc)
        sp.addConstr(xc <= self.ChargingStationLocation)
        sp.addConstr(yl[int(od[0])] == InitialSoc)

        ## Objective
        sp.setObjective(self.LinkTravelTime @ xl + self.ChargingWaiting @ xc + self.ChargingSpeed @ xa)
        sp.optimize()
#        print(sp.message())
#        print(sp.get(GRB_IntAttr_Status))

        
        
        try:
            # print(od)
            LinkChoice = xl.X
            ChargingStationChoice = xc.X
            ChargingAmountChoice = xa.X
            BatteryLevel = yl.X
            ChargingCost = self.ChargingWaiting @ ChargingStationChoice + self.ChargingSpeed @ ChargingAmountChoice
            # print('Travel Time is: ', self.LinkTravelTime @ LinkChoice)
            # print('Charging Time is: ', self.ChargingSpeed @ ChargingAmountChoice)
            return True, LinkChoice, ChargingStationChoice,  ChargingAmountChoice,  BatteryLevel, ChargingCost
        
        except TypeError:
            return False, 0,0,0,0
        

    
    def EquilibriumState(self,):
        if self.FeasibilityCheck():
            Flag = True
            while Flag:
                ## Parameters
                PathSize = 1 if np.size(self.PathSet.shape) == 1 else np.size(self.PathSet,0) 
                PathODMatrix = np.zeros([self.ODSize,PathSize])
                for i in range(PathSize):
                    PathODMatrix[self.PathToOD[i],i] = 1

                ## Variables and Parameters
                linkflow = cp.Variable(self.LinkSize)
                pathflow = cp.Variable(PathSize)

                linkreci = 1000/self.NetworkLink[:,3]
                # print(linkreci**4)

                ## Constr
                Constraints =  [PathODMatrix @ pathflow == self.ODDemand/1000]
                Constraints += [self.PathSet.T @ pathflow == linkflow]
                Constraints += [linkflow >= 0, pathflow >= 0]

                ## Objects
                Objective = self.NetworkLink[:,2] @ ( linkflow + 0.15/5 * cp.multiply(linkflow**5, linkreci**4)) + pathflow @ self.ChargingCost

                prob = cp.Problem(cp.Minimize(Objective),Constraints)

                result = prob.solve()


                self.UEObjective = Objective.value
                self.LinkFlow = linkflow.value
                self.PathFlow = pathflow.value
                self.LinkTravelTime  = self.NetworkLink[:,2]* (1+0.15*(linkflow.value*linkreci)**4)
                self.ChargingAmount = self.PathFlow @ self.ChargingSet
                self.NetworkLoad = np.sum(linkflow.value*linkreci)/self.LinkSize

                
                
                ## Update the minimal costs
                if PathSize == 1:
                    self.PathCost = self.LinkTravelTime @ self.PathSet + self.ChargingCost
                else:
                    self.PathCost = self.LinkTravelTime @ self.PathSet[0] + self.ChargingCost[0]
                    for i in range(1,PathSize):
                        self.PathCost = np.row_stack([self.PathCost,self.LinkTravelTime @ self.PathSet[i] + self.ChargingCost[i]])
                for i in range(PathSize):
                    self.ODCost[self.PathToOD[i]] = self.PathCost[i] if self.PathCost[i] < self.ODCost[self.PathToOD[i]] else self.ODCost[self.PathToOD[i]]
                
                
                # print(self.PathSize)

                ## NewShortestPath
                Flag = False
                for i in range(self.ODSize):
                    od = self.OD[i]
                    if len(od) >= 6:
                        SPFlag, LinkChoice, ChargingStationChoice,  ChargingAmountChoice,  BatteryLevel,ChargingCost = self.EVShortestPath(od,od[3:6])
                    else:
                        SPFlag, LinkChoice, ChargingStationChoice,  ChargingAmountChoice,  BatteryLevel,ChargingCost = self.EVShortestPath(od)
                    if LinkChoice @ self.LinkTravelTime + ChargingCost < self.ODCost[i]- 0.1:
                        self.PathSet = np.row_stack([self.PathSet,LinkChoice])
                        self.PathToOD = np.row_stack([self.PathToOD,i])
                        self.ChargingCost = np.row_stack([self.ChargingCost,ChargingCost])
                        self.ChargingSet = np.row_stack([self.ChargingSet,ChargingAmountChoice])
                        Flag = True       

        else:
            print('Not a feasible charging station setting')



        






