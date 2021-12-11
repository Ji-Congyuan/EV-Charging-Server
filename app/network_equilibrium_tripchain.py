
import numpy as np
import cvxpy as cp
import gurobipy as gp
import copy
from gurobipy import GRB


class TripChainNetworkEquilibrium:
    # Suppose all the input are the numpy variables
    def __init__(self, NetworkLink = None, NetworkNode = None, ChagingStation = None, myOD = None):
        self.NetworkLink = 0
        self.NetworkNode = 0
        self.ChargingStation = 0
        self.ChargingStationLocation = 0
        self.ChargingSpeed = 0
        self.ChargingWaiting =0
        self.OD = 0
        self.ODDemand = 0
        self.ODSize = 0
        self.ODCost = 0
        self.PathFlow = 0
        self.PathSize = 0
        self.LinkFlow = 0
        self.LinkSize = 0
        self.LinkTravelTime = 0
        self.NodeSize = 0
        self.ChargingDemand = 0
        self.PathSet = 0
        self.GeneralPathSet = []
        self.GeneralChargingSet = []
        self.ChargingCost = 0
        self.PathToOD = 0
        self.PathCost = 0
        self.NodeLinkMatrix = 0
        self.SafeSoc = 50
        self.InitialSoc = 200
        self.MaxSoc = 300
        self.LinkEleConsu = 0
        self.UEObjective = 0       
        self.PathOutPut = []

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

    def SetLinks(self,Links):
        self.NetworkLink = Links

    def SetNodes(self,Nodes):
        self.NetworkNode = Nodes

    def SetChargingStations(self,ChargingStations):
        self.ChargingStation = ChargingStations
        self.ChargingSpeed = np.zeros(self.NodeSize)
        self.ChargingWaiting = np.zeros(self.NodeSize)
        self.ChargingStationLocation = np.zeros(self.NodeSize)
        for i in range(self.NodeSize):
            self.ChargingStationLocation[i] = self.ChargingStation[i,0]
            self.ChargingSpeed[i] = self.ChargingStation[i,2]
            self.ChargingWaiting[i] = self.ChargingStation[i,3]
    
    def SetOD(self,myOD):
        self.OD = myOD
        self.ODSize = len(self.OD)
        self.ODDemand = np.zeros(self.ODSize)
        for i in range(self.ODSize):
            self.ODDemand[i] = self.OD[i][0][0]
        self.ODCost = 100000000.0 * np.ones(self.ODSize)        

    def FeasibilityCheck(self,):
        # Check if all the condition is feasible for solving an equilibrium condition
        # Besides, regulating the formate for computation deta
        for i in range(self.ODSize):
            od = self.OD[i]
            Flag, AllLinkChoice, LinkChoice, ChargingStationChoice, ChargingAmountChoice, BatteryLevel,BatteryLevel2, ChargingCost,RealChargingTime = self.EVShortestPath(od)
            if Flag is not True:
                return False
            if i == 0:
                self.PathSet = AllLinkChoice
                self.GeneralPathSet = [LinkChoice]
                self.PathToOD = i
                self.ChargingCost = ChargingCost
                self.GeneralChargingSet = [[BatteryLevel,ChargingStationChoice,ChargingAmountChoice,BatteryLevel2,RealChargingTime]]
            else:
                self.PathSet = np.row_stack([self.PathSet,AllLinkChoice])
                self.GeneralPathSet.append(LinkChoice)
                self.PathToOD = np.row_stack([self.PathToOD,i])
                self.ChargingCost = np.row_stack([self.ChargingCost,ChargingCost])
                self.GeneralChargingSet.append([BatteryLevel,ChargingStationChoice,ChargingAmountChoice,BatteryLevel2,RealChargingTime])
        return True
 
    def EVShortestPath(self,od):        
        InitialSoc = od[0][1]
        SafeSoc = od[0][2]
        MaxSoc = od[0][3]
        ChainSize = len(od[1])        
        sp = gp.Model("EVShortestPathMIP")
        sp.setParam('OutputFlag', 0)
        
        ## Variables
        xl = sp.addMVar((self.LinkSize,ChainSize), vtype = GRB.BINARY, name = "linkchoice" )
        xc = sp.addMVar((self.NodeSize,ChainSize), vtype = GRB.BINARY, name = "chargingstationchoice")
        xa = sp.addMVar((self.NodeSize,ChainSize), lb = 0, ub = MaxSoc-SafeSoc, vtype = GRB.CONTINUOUS, name = "chargingamountchoice")
        yl = sp.addMVar((self.NodeSize,ChainSize), lb = SafeSoc,  ub = MaxSoc,  vtype = GRB.CONTINUOUS, name = "batterylevel")
        ft = sp.addMVar((self.NodeSize,ChainSize), lb = 0, vtype = GRB.CONTINUOUS, name = "flexible_charging_time")
        ob = sp.addMVar(ChainSize,vtype = GRB.CONTINUOUS,name = "objective")
        
        ## Parameters
        Ers = np.zeros([self.NodeSize,ChainSize])
        BufferTime = np.zeros([self.NodeSize,ChainSize])
        for i in range(ChainSize):
            Ers[od[1][i][0],i] = 1
            Ers[od[1][i][1],i] = -1
            if i >= 1:
                BufferTime[od[1][i][0],i] = od[1][i][2] - od[1][i-1][2]
        # print(BufferTime)

        ## Constr       
        for i in range(ChainSize):
            sp.addConstr(self.NodeLinkMatrix @ xl[:,i] == Ers[:,i])
            sp.addConstr(self.LinkStartMatrix @ yl[:,i] + self.LinkStartMatrix @ xa[:,i] - self.LinkEleConsu - self.LinkEndMatrix @ yl[:,i] <= MaxSoc*(1-xl[:,i]))
            sp.addConstr(self.LinkStartMatrix @ yl[:,i] + self.LinkStartMatrix @ xa[:,i] - self.LinkEleConsu - self.LinkEndMatrix @ yl[:,i] >= MaxSoc*(xl[:,i]-1))
            sp.addConstr(self.LinkStartMatrix @ yl[:,i] + self.LinkStartMatrix @ xa[:,i] <= MaxSoc)
            sp.addConstr(xa[:,i] <= (MaxSoc-SafeSoc)*xc[:,i])
            sp.addConstr(xc[:,i] <= self.ChargingStationLocation)
            for j in range(self.NodeSize):
                sp.addConstr(ft[j,i] >= self.ChargingSpeed[j] * xa[j,i] -BufferTime[j,i])
            if i == 0:
                sp.addConstr(yl[od[1][i][0],i] == InitialSoc)
            else:
                sp.addConstr(yl[od[1][i][0],i] == yl[od[1][i-1][1],i-1])
            sp.addConstr(ob[i] == self.LinkTravelTime @ xl[:,i] + self.ChargingWaiting @ xc[:,i] + ft[:,i].sum())

        ## Objective
        sp.setObjective(ob.sum())
        sp.optimize()        
        try:
            LinkChoice = xl.X
            ChargingStationChoice = xc.X
            ChargingAmountChoice = xa.X
            BatteryLevel = yl.X
            BatteryLevel2 = yl.X+xa.X
            RealChargingTime = ft.X
            ChargingCost = np.sum(self.ChargingWaiting @ ChargingStationChoice + ft.X)
            AllLinkChoice = np.zeros(self.LinkSize)
            for i in range(ChainSize):
                AllLinkChoice += LinkChoice[:,i]
            return True, AllLinkChoice, LinkChoice, ChargingStationChoice, ChargingAmountChoice, BatteryLevel,BatteryLevel2, ChargingCost,RealChargingTime
        except TypeError:
            return False, 0,0,0,0,0,0,0,0
            
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
                
                # print(Objective.value)
                # print()
                
                self.UEObjective = Objective.value
                self.LinkFlow = linkflow.value
                self.PathFlow = pathflow.value
                self.LinkTravelTime  = self.NetworkLink[:,2]* (1+0.15*(linkflow.value*linkreci)**4)
                self.PathSize = PathSize
              
                
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
                    SPFlag, AllLinkChoice, LinkChoice, ChargingStationChoice, ChargingAmountChoice, BatteryLevel,BatteryLevel2, ChargingCost,RealChargingTime = self.EVShortestPath(od)
                    if AllLinkChoice @ self.LinkTravelTime + ChargingCost < self.ODCost[i]- 0.1:
                        self.PathSet = np.row_stack([self.PathSet,AllLinkChoice])
                        self.GeneralPathSet.append(LinkChoice)
                        self.PathToOD = np.row_stack([self.PathToOD,i])
                        self.ChargingCost = np.row_stack([self.ChargingCost,ChargingCost])
                        self.GeneralChargingSet.append([BatteryLevel,ChargingStationChoice,ChargingAmountChoice,BatteryLevel2,RealChargingTime])
                        Flag = True       
            
            return True
        else:
            return False

    def GenerateResult(self,):
        self.PathOutPut = []
        for i in range(self.ODSize):
            for j in range(self.PathSize):
                if self.PathToOD[j] == i and self.PathFlow[j]*1000/self.OD[i][0][0] >= 0.05:
                    od = self.OD[i]
                    ChainSize = len(od[1])
                    temppath = []
                    for k in range(ChainSize):
                        Flag = True
                        node = od[1][k][0]
                        time = od[1][k][2]
                        if k == 0:
                            temppath.append([node,int(time),int(self.GeneralChargingSet[j][0][node][k]),int(self.GeneralChargingSet[j][2][node][k])])       # 点位、时间、电量水平，充电量
                        else:
                            rct = self.GeneralChargingSet[j][4][node][k]
                            
                            temppath.append([node,int(time+rct),int(self.GeneralChargingSet[j][3][node][k]),0])       # 点位、时间、电量水平，充电量
                            
                        while Flag:
                            for m in range(self.LinkSize):
                                if self.NetworkLink[m,0] == node and self.GeneralPathSet[j][m][k] == 1:
                                    node = int(self.NetworkLink[m,1])
                                    time = time + self.LinkTravelTime[m]
                                    break                           
                            if node == od[1][k][1] and k < ChainSize-1:                             
                                temppath.append([node,int(time),int(self.GeneralChargingSet[j][0][node][k]),int(self.GeneralChargingSet[j][2][node][k]+self.GeneralChargingSet[j][2][node][k+1])])
                            else:
                                csamount = self.GeneralChargingSet[j][2][node][k]
                                temppath.append([node,int(time),int(self.GeneralChargingSet[j][0][node][k]),int(self.GeneralChargingSet[j][2][node][k])])
                                if csamount > 0.1:
                                    rct = self.GeneralChargingSet[j][4][node][k]
                                    print([csamount,time,rct])
                                    temppath.append([node,int(time+rct),int(self.GeneralChargingSet[j][3][node][k]),0])
                            Flag = False if node == od[1][k][1] else True
                    self.PathOutPut.append([[i,int(1000*self.PathFlow[j])],copy.deepcopy(temppath)])              
      
        return True

        






