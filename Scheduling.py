import random
import matplotlib.pyplot as plt
from Instance import Job,State,Machine,PT,agv_num
import numpy as np



class AGV:
    def __init__(self,idx,L_U):
        self.idx=idx
        self.cur_site=L_U
        self.using_time=[]
        self._on=[]
        self._to=[]
        self.end=0

    def ST(self,s,t1,t2):
        start=max(s,self.end+t1)
        return start-t1,start+t2

    def update(self,s,trans1,trans2,J_site,J_m,_on=None):
        self.using_time.append([s,s+trans1])
        self.using_time.append([s + trans1, s+trans1 + trans2])
        self._on.append(None)
        self._on.append(_on)
        self._to.extend([J_site,J_m])
        self.end=s+trans1+trans2
        self.cur_site=J_m

class Item:
    def __init__(self,idx):
        self.idx=idx
        self.start=[]
        self.end=[]
        self._on=[]
        self.T=[]
        self.last_ot=0
        self.L=0
        self.laston=None

    def update(self,s,e,on,t):
        self.start.append(s)
        self.end.append(e)
        self._on.append(on)
        self.laston=on
        self.T.append(t)
        self.last_ot=e
        self.L+=t

class Scheduling:
    def __init__(self,J_num,Machine,State,PT,TT,agv_num):
        self.M=Machine
        self.J_num=J_num
        self.agv_num=agv_num
        self.TT=TT
        self.State=State
        self.PT=PT
        self.Create_Job()
        self.Create_Machine()
        self.Create_Agv()
        self.fitness=0

    def Create_Job(self):
        self.Jobs=[]
       # M=Item(0)
        for i in range(self.J_num):
            J=Item(i+1)
            J.laston=0
            self.Jobs.append(J)

    def Create_Machine(self):
        self.Machines=[]
        idx=1
        for i in range(len(self.M)):    #突出机器的阶段性，即各阶段有哪些机器
            State_i=[]
            for j in range(self.M[i]):
                M=Item(idx)
                State_i.append(M)
                idx+=1
            self.Machines.append(State_i)
    def Create_Agv(self):
        self.Agvs=[]
        for i in range(self.agv_num):
            A=AGV(i,0)
            self.Agvs.append(A)
    #每个阶段的解码
    def Stage_Decode(self,CHS,Stage):

        for i in CHS:
            last_od=self.Jobs[i].last_ot
            last_Md=[self.Machines[Stage][M_i].last_ot for M_i in range(self.M[Stage])] #机器的完成时间
            last_ML = [self.Machines[Stage][M_i].L for M_i in range(self.M[Stage])]     #机器的负载
            M_time=[self.PT[Stage][M_i][i] for M_i in range(self.M[Stage])]             #机器对当前工序的加工时间
            O_et=[last_Md[_]+M_time[_] for _ in range(self.M[Stage])]
            if O_et.count(min(O_et))>1 and last_ML.count(last_ML)>1:
                Machine=random.randint(0,self.M[Stage])
            elif O_et.count(min(O_et))>1 and last_ML.count(last_ML)<1:
                Machine=last_ML.index(min(last_ML))
            else:
                Machine=O_et.index(min(O_et))
            best_s,best_e,t1,t2=None,None,None,None
            min_tf=99999
            best_agv=None
            Machineidx=sum(self.M[0:Stage])+Machine+1
            # print(Machineidx)
            # print("***********")
            # print(Stage)
            for agv in self.Agvs:
                trans1=self.TT[agv.cur_site][self.Jobs[i].laston]
                trans2=self.TT[self.Jobs[i].laston][Machineidx]
                start,end=agv.ST(self.Jobs[i].last_ot,trans1,trans2)
                if end<min_tf:
                    best_s,best_e,t1,t2 = start,end,trans1,trans2
                    best_agv=agv
                    min_tf=best_e
            best_agv.update(best_s,t1,t2,self.Jobs[i].laston,Machineidx,self.Jobs[i].idx)
            # 无AGV
            s, e, t=max(last_od,last_Md[Machine],),max(last_od,last_Md[Machine])+M_time[Machine],M_time[Machine]

            # 有AGV
            #s, e, t=max(last_Md[Machine],max(last_od,best_e)),max(last_Md[Machine],max(last_od,best_e))+M_time[Machine],M_time[Machine]
            self.Jobs[i].update(s, e,Machineidx, t)
            self.Machines[Stage][Machine].update(s, e,i, t)
            if e>self.fitness:
                self.fitness=e

    #解码
    def Decode(self,CHS):
        for i in range(self.State):
            self.Stage_Decode(CHS,i)
            Job_end=[self.Jobs[i].last_ot for i in range(self.J_num)]
            CHS = sorted(range(len(Job_end)), key=lambda k: Job_end[k], reverse=False)

    #画甘特图
    def Gantt(self):
        #fig = plt.figure()
        fig=plt.figure(figsize=(24, 10))  # 设置DPI为100
        M = ['red', 'blue', 'yellow', 'orange', 'green', 'moccasin', 'purple', 'pink', 'navajowhite', 'Thistle',
             'Magenta', 'SlateBlue', 'RoyalBlue', 'Aqua', 'floralwhite', 'ghostwhite', 'goldenrod', 'mediumslateblue',
             'navajowhite','navy', 'sandybrown']
        M_num=0
        for i in range(len(self.M)):
            for j in range(self.M[i]):
                for k in range(len(self.Machines[i][j].start)):
                    Start_time=self.Machines[i][j].start[k]
                    End_time=self.Machines[i][j].end[k]
                    Job=self.Machines[i][j]._on[k]
                    plt.barh(M_num, width=End_time - Start_time, height=0.8, left=Start_time, \
                             color=M[Job%21], edgecolor='black')
                    plt.text(x=Start_time + ((End_time - Start_time) / 2 -4), y=M_num-0.08 ,
                             s=Job+1, size=15, fontproperties='Times New Roman')
                M_num += 1
        opline=[sum(Machine[0:i+1])-0.5 for i in range(len(Machine))]

        # for i in range(len(opline)):
        #     plt.hlines(opline[i],xmin=0,xmax=500, colors='black',linestyles='solid',label="OP"+str(i+1))
        plt.yticks(np.arange(M_num + 1), np.arange(1, M_num + 2), size=20, fontproperties='Times New Roman')
        plt.xticks(size=20, fontproperties='Times New Roman')
        plt.ylabel("机器", size=20, fontproperties='SimSun')
        plt.xlabel("时间", size=20, fontproperties='SimSun')
        plt.tick_params(labelsize=20)
        plt.tick_params(direction='in')
        plt.show()

    def Agv_Gantt(self):
        #fig = plt.figure()
        fig=plt.figure(figsize=(24, 10))  # 设置DPI为100
        M = ['red', 'blue', 'yellow', 'orange', 'green', 'moccasin', 'purple', 'pink', 'navajowhite', 'Thistle',
             'Magenta', 'SlateBlue', 'RoyalBlue', 'Aqua', 'floralwhite', 'ghostwhite', 'goldenrod', 'mediumslateblue',
             'navajowhite','navy', 'sandybrown']
        agv_num=0
        for agv in self.Agvs:
            to_num=0
            for use_time in agv.using_time:
                Start_time=use_time[0]
                End_time=use_time[1]
                to=agv._to[to_num]
                if (Start_time-End_time)!=0:
                    plt.barh(agv_num, width=End_time - Start_time, height=0.8, left=Start_time, \
                             color=M[to%(sum(Machine)+1)], edgecolor='black')
                    plt.text(x=Start_time + ((End_time - Start_time) / 2 -1), y=agv_num-0.08 ,
                             s=to, size=15, fontproperties='Times New Roman')
                to_num+=1
            agv_num+=1
        #opline=[sum(Machine[0:i+1])-0.5 for i in range(len(Machine))]

        # for i in range(len(opline)):
        #     plt.hlines(opline[i],xmin=0,xmax=500, colors='black',linestyles='solid',label="OP"+str(i+1))
        plt.yticks(np.arange(agv_num + 1), np.arange(1, agv_num + 2), size=20, fontproperties='Times New Roman')
        plt.xticks(size=20, fontproperties='Times New Roman')
        plt.ylabel("AGV", size=20, fontproperties='SimSun')
        plt.xlabel("Time", size=20, fontproperties='SimSun')
        plt.tick_params(labelsize=20)
        plt.tick_params(direction='in')
        plt.show()



#
