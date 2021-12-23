# -*- coding: utf-8 -*-
"""
Created on Sun Oct 10 21:49:04 2021

@author: ZhixiongLuo
"""

import app.network_equilibrium as NE
import numpy as np
# import xlrd as xd
import time
import json


'''
data =xd.open_workbook('demand_data.xlsx') #打开excel表所在路径
sheet = data.sheet_by_name('demand_data')  #读取数据，以excel表名来打开
demand_data = []
for r in range(sheet.nrows): #将表中数据按行逐步添加到列表中，最后转换为list结构
    data1 = []
    for c in range(sheet.ncols):
        data1.append(sheet.cell_value(r,c)) 
    if r>=1:
        demand_data.append(list(data1))


data =xd.open_workbook ('node_data.xlsx') #打开excel表所在路径
sheet = data.sheet_by_name('node_data')  #读取数据，以excel表名来打开
node_data = []
for r in range(sheet.nrows): #将表中数据按行逐步添加到列表中，最后转换为list结构
    data1 = []
    for c in range(sheet.ncols):
        data1.append(sheet.cell_value(r,c))
    
    if r>=1:
        node_data.append(list(data1))
 
        
 
data =xd.open_workbook('network_data.xlsx') #打开excel表所在路径
sheet = data.sheet_by_name('network_data')  #读取数据，以excel表名来打开
network_data = []
for r in range(sheet.nrows): #将表中数据按行逐步添加到列表中，最后转换为list结构
    data1 = []
    for c in range(sheet.ncols):
        data1.append(sheet.cell_value(r,c))
    
    if r>=1:
        network_data.append(list(data1))
        


# Links = np.array([[0,1,50,1000,10],[0,2,100,1000,20],[0,3,150,1000,30],[1,2,50,1000,10],[3,2,50,1000,10],[1,4,300,1000,60],[2,4,250,1000,50],[3,4,200,1000,40]])
# node_data = [[1,4],[2,4],[3,5],[5,9],[9,10]]
# network_data = [[1,2,50,1000,10],[3,9,50,1000,10],[5,9,50,1000,10],[2,3,50,1000,10]]
# MyOD = np.array([[0,4,4000.0,50,10,100],[0,2,2000,50,20,100]])
# demand_data = [[1,1,2,1000,100,20,100],[1,3,9,1000,100,20,100],[1,5,9,1000,100,20,100],[1,2,3,1000,100,20,100],[2,1,2,1000,100,20,100],[2,3,9,1000,100,20,100],[2,5,9,1000,100,20,100],[2,2,3,1000,100,20,100]]
ChargingStation = np.array([[0,0,0,0],[1,10,2,20],[2,10,0.5,200],[3,10,2,15],[0,0,0,0]])


initial_electricity_level = 40
low_level_threshold = 20
high_level_threshold = 100
station_data = 20



f = open('example_input1.json', 'r')
content = f.read()
a = json.loads(content)
experiment_id = a[0]
node_data = a[1]
network_data = a[2]
station_data = 30
demand_data = a[4]
initial_electricity_level = a[5]
low_level_threshold = a[6]
high_level_threshold = a[7]

'''


def Equilibrium(experiment_id, node_data, network_data, station_data, demand_data, initial_electricity_level, low_level_threshold,  high_level_threshold):

    ne = NE.NetworkEquilibrium()   
    NodeData = np.zeros([len(node_data),len(node_data[0])])
    for i in range(len(node_data)):
        NodeData[i,0] = node_data[i]['trafficNode']
        NodeData[i,1] = node_data[i]['longitude']
        NodeData[i,2] = node_data[i]['latitude']    
        NodeData[i,3] = node_data[i]['linkedPowerBus']
    
    NetworkData = np.zeros([len(network_data),len(network_data[0])])
    for i in range(len(network_data)):
        NetworkData[i,0] = network_data[i]['fromNode']
        NetworkData[i,1] = network_data[i]['toNode']
        NetworkData[i,2] = 3*network_data[i]['distance']/1000/30*60
        NetworkData[i,3] = network_data[i]['capacity']
        NetworkData[i,4] = 3*network_data[i]['distance']/1000/5
        NetworkData[i,5] = network_data[i]['linkId']
    
    DemandData = [[None]*4 for _ in range(len(demand_data))]
    for i in range(len(demand_data)):
        DemandData[i][0] = demand_data[i]['timeSlot']
        DemandData[i][1] = demand_data[i]['fromNode']
        DemandData[i][2] = demand_data[i]['toNode']
        DemandData[i][3] = demand_data[i]['od']
    demand_data = DemandData

    ne.SetNodes(NodeData)
    ne.SetLinks(NetworkData)
    ne.ParameterUpdate()
    ne.SetChargingStations(station_data)
    ChargingStationNumber = len(ne.ChargingList)
    ne.SafeSoc = low_level_threshold
    ne.InitialSoc = initial_electricity_level
    ne.MaxSoc = high_level_threshold
    demand_data_h_size = len(demand_data[0])
    timeslot = 24
    ChargingAmount = [[None]*timeslot for _ in range(ChargingStationNumber)]
    LinkFlow = [[None]*timeslot for _ in range(ne.LinkSize)]
    Networkload = [None]*timeslot

    jsonlog = {"pile_demand":{},"link_flow":{},"network_load":{}}


    StartEnd = np.zeros([timeslot,2])
    StartEnd[timeslot-1,1] = len(demand_data)
    label = 0

    for i in range(len(demand_data)-1):
        if demand_data[i][0] != demand_data[i+1][0]:
            StartEnd[label][1] = i
            label = label +1
            StartEnd[label][0] = i+1
    demand_data = np.array(demand_data)

    for i in range(timeslot):
        time_start = time.time()
        od_data = demand_data[int(StartEnd[i,0]):int(StartEnd[i,1]),1:demand_data_h_size]
        ne.SetOD(od_data)
        ne.EquilibriumState()
        k = 0
        for j in ne.ChargingList:
            ChargingAmount[k][i] = 1000 * ne.ChargingAmount[int(j)]
            jsonlog['pile_demand'][str(j)] = ChargingAmount[k]
            k = k+1
        for j in range(ne.LinkSize):
            LinkFlow[j][i] = ne.LinkFlow[j] * 1000
            jsonlog['link_flow'][str(ne.NetworkLink[i,5])] = LinkFlow[j]
        Networkload[i] = ne.NetworkLoad
        jsonlog['network_load'] = Networkload
        time_end = time.time()       
        # print('timeslot: ',i,', computational time cost is: ',time_end-time_start,'s')
    
    b = json.dumps(jsonlog)
    f2 = open('./app/experiment_result/'+str(experiment_id)+'.json', 'w')
    f2.write(b)
    f2.close()


# def Equilibrium(experiment_id, node_data, network_data, station_data, demand_data, initial_electricity_level, low_level_threshold,  high_level_threshold):
#     ne = NE.NetworkEquilibrium()
#     ne.SetNodes(np.array(Nodes))
#     ne.SetLinks(np.array(Links))
#     return 0

# ne = NE.NetworkEquilibrium()
# ne.SetLinks(Links)
# ne.SetNodes(Nodes)
# ne.ParameterUpdate()
# ne.SetChargingStations(ChargingStation)
# ne.SetOD(MyOD)

# Flag, LinkChoice, ChargingStationChoice,  ChargingAmountChoice,  BatteryLevel, ChargingCost= ne.EVShortestPath(od=[0,4],SOCInfo=[70,10,100])

# ne.EquilibriumState()

# print(ne.PathCost)

# print(ne.PathFlow)
# print(ne.PathToOD)
# print(ne.LinkFlow)

# print(ne.NetworkLink[:,2] @ ( ne.LinkFlow  + 0.03*(ne.LinkFlow**5)/(ne.NetworkLink[:,3]/1000)**4) + ne.PathFlow @ ne.ChargingCost)

# l = ne.PathSet.T @  ne.PathFlow
# print(l)