# -*- coding: utf-8 -*-
"""
Created on Sun Oct 10 21:49:04 2021

@author: ZhixiongLuo
"""

import app.network_equilibrium_tripchain as NE
import numpy as np
import pandas as pd


def generateODInfo():
    ODInfo =[
        [[1000,50,10,100],[[0,44,420],[44,41,720],[41,0,1080]]],
        [[1000,50,10,100],[[15,37,420],[37,44,720],[44,15,1080]]],
        [[1000,50,10,100],[[11,0,420],[0,3,720],[3,11,1080]]]
    ]
    return ODInfo

def generateChargingStation(charging_station,NodeSize):
    if charging_station is not None:
        Files = pd.ExcelFile('XianNetwork.xlsx')
        if charging_station == 0:
            TempChargingStation = np.array(np.array(pd.read_excel(Files,'charging_station_low')))
        elif charging_station == 1:
            TempChargingStation = np.array(np.array(pd.read_excel(Files,'charging_station_middle')))
        else:
            TempChargingStation = np.array(np.array(pd.read_excel(Files,'charging_station_high')))
        ChargingStation = np.zeros([NodeSize,4])
        for tempcs in TempChargingStation:
            tempcs[0] -= 1
            cs = int(tempcs[0])
            ChargingStation[cs] = tempcs
    else:
        ChargingStation = np.array([[0,0,0,0],[1,10,2,20],[2,10,0.5,200],[3,10,2,15],[0,0,0,0]])
    return ChargingStation

def generateLinks():
    Files = pd.ExcelFile('XianNetwork.xlsx')
    links = np.array(np.array(pd.read_excel(Files,'xianLinks')))
    return links

def generateNodes():
    Files = pd.ExcelFile('XianNetwork.xlsx')
    nodes = np.array(np.array(pd.read_excel(Files,'xianNodes')))
    return nodes

def TripChainMain(demand_ratio, electricity, charging_station,Links = None, Nodes = None):
    if Links is None:
        Links = generateLinks()
    # Links = np.array([[0,1,50,1000,10],[0,2,100,1000,20],[0,3,150,1000,30],[1,2,50,1000,10],[3,2,50,1000,10],[1,4,300,1000,60],[2,4,250,1000,50],[3,4,200,1000,40],[1,0,50,1000,10],[2,0,100,1000,20],[3,0,150,1000,30],[2,1,50,1000,10],[2,3,50,1000,10],[4,1,300,1000,60],[4,2,250,1000,50],[4,3,200,1000,40]])

    if Nodes is None:
        Nodes = generateNodes()
    # Nodes = np.array([0,1,2,3,4])

    NodeSize = len(Nodes)
    ODInfo = generateODInfo()
    # ODInfo = [[[1000,50,10,100],[[0,3,420],[3,4,720],[4,0,1080]]],[[1000,50,10,100],[[0,2,7],[2,4,12],[4,0,18]]],[[1000,50,10,100],[[1,2,7],[2,4,12],[4,0,18]]]]
    for i in range(len(ODInfo)):
        ODInfo[i][0][0] = ODInfo[i][0][0]*demand_ratio
        ODInfo[i][0][1] = electricity[0]
        ODInfo[i][0][2] = electricity[1]
        ODInfo[i][0][3] = electricity[2]


    ChargingStation = generateChargingStation(charging_station,NodeSize)

    # if charging_station == 0:
    # 	ChargingStation = np.array([[0,0,0,0],[1,10,2,20],[2,10,0.5,200],[3,10,2,15],[0,0,0,0]])

    ne = NE.TripChainNetworkEquilibrium()
    ne.SetLinks(Links)
    ne.SetNodes(Nodes)
    ne.ParameterUpdate()
    ne.SetChargingStations(ChargingStation)
    ne.SetOD(ODInfo)

    if ne.EquilibriumState():
        # print(ne.LinkTravelTime)
        ne.GenerateResult()
        return True, ne.PathOutPut,ne.GeneralChargingSet,ne
    else:
        return False, None, None,ne

# Flag, AllLinkChoice, LinkChoice, ChargingStationChoice, ChargingAmountChoice, BatteryLevel,BatteryLevel2, ChargingCost,RealChargingTime = ne.EVShortestPath(MyOD[0])

# ne.EquilibriumState()

# print(ne.PathCost)

# print(ne.PathFlow)
# print(ne.PathToOD)
# print(ne.LinkFlow)

# print(ne.NetworkLink[:,2] @ ( ne.LinkFlow + 0.03*(ne.LinkFlow**5)/(ne.NetworkLink[:,3]/1000)**4) + ne.PathFlow @ ne.ChargingCost)

# l = ne.PathSet.T @  ne.PathFlow
# print(l)

# ne.GenerateResult()
# PathOut = ne.PathOutPut
# ChargingInfo = ne.GeneralChargingSet

Flag,PathOut,ChargingSet,ne = TripChainMain(1, [25,10,70], charging_station=1,Links = None, Nodes = None)